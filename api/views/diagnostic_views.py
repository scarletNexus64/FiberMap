from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from ..models import MesureOTDR, Coupure, Liaison, PointDynamique
from ..serializers import (
    MesureOTDRSerializer, MesureOTDRCreateSerializer, 
    CoupureSerializer, LiaisonListSerializer
)
from ..services import CoupureService, NotificationService

class MesureOTDRViewSet(viewsets.ModelViewSet):
    """ViewSet pour les mesures OTDR"""
    queryset = MesureOTDR.objects.select_related('liaison', 'technicien', 'point_mesure')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['liaison', 'technicien', 'type_evenement', 'position_technicien', 'direction_analyse']
    ordering = ['-date_mesure']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MesureOTDRCreateSerializer
        return MesureOTDRSerializer
    
    def perform_create(self, serializer):
        serializer.save(technicien=self.request.user)
    
    @action(detail=True, methods=['post'])
    def analyser_coupure(self, request, pk=None):
        """Analyse une mesure OTDR et détecte automatiquement une coupure"""
        mesure = self.get_object()
        
        if mesure.type_evenement != 'coupure':
            return Response(
                {'error': 'Cette mesure ne correspond pas à une coupure'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si une coupure existe déjà pour cette mesure
        coupure_existante = Coupure.objects.filter(mesure_otdr=mesure).first()
        if coupure_existante:
            return Response({
                'message': 'Coupure déjà analysée',
                'coupure': CoupureSerializer(coupure_existante).data
            })
        
        # Créer la coupure
        coupure = CoupureService.creer_coupure(mesure)
        
        # Notifier les superviseurs
        NotificationService.notifier_coupure_detectee(coupure)
        
        return Response({
            'message': 'Coupure analysée et créée',
            'coupure': CoupureSerializer(coupure).data,
            'analyse': CoupureService.analyser_coupure(mesure)
        }, status=status.HTTP_201_CREATED)

class CoupureViewSet(viewsets.ModelViewSet):
    """ViewSet pour les coupures"""
    queryset = Coupure.objects.select_related('liaison', 'mesure_otdr', 'point_dynamique_proche', 'segment_touche')
    serializer_class = CoupureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'liaison', 'liaison__client']
    ordering = ['-date_detection']
    
    @action(detail=True, methods=['put'])
    def changer_status(self, request, pk=None):
        """Change le statut d'une coupure"""
        coupure = self.get_object()
        nouveau_status = request.data.get('status')
        
        if nouveau_status not in ['detectee', 'localisee', 'en_cours', 'reparee']:
            return Response(
                {'error': 'Statut invalide'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        coupure.status = nouveau_status
        
        # Si réparée, marquer la date de résolution
        if nouveau_status == 'reparee':
            from django.utils import timezone
            coupure.date_resolution = timezone.now()
        
        coupure.save()
        
        return Response({
            'message': f'Statut changé à {nouveau_status}',
            'coupure': CoupureSerializer(coupure).data
        })
    
    @action(detail=False, methods=['get'])
    def actives(self, request):
        """Récupère toutes les coupures actives (non réparées)"""
        coupures_actives = self.get_queryset().exclude(status='reparee')
        
        page = self.paginate_queryset(coupures_actives)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(coupures_actives, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def carte(self, request):
        """Données optimisées pour l'affichage des coupures sur la carte"""
        coupures = self.get_queryset().exclude(status='reparee')
        
        from ..serializers import CoupureCarteSerializer
        serializer = CoupureCarteSerializer(coupures, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def recalculer_position(self, request, pk=None):
        """Recalcule la position estimée de la coupure"""
        coupure = self.get_object()
        
        # Refaire l'analyse avec les données actuelles
        analyse = CoupureService.analyser_coupure(coupure.mesure_otdr)
        
        # Mettre à jour la coupure
        coupure.segment_touche = analyse['segment_touche']
        coupure.distance_sur_segment = analyse['distance_sur_segment']
        coupure.point_dynamique_proche = analyse['point_dynamique_proche']
        
        if analyse['coordonnees_estimees']:
            coupure.point_estime_lat = analyse['coordonnees_estimees']['latitude']
            coupure.point_estime_lng = analyse['coordonnees_estimees']['longitude']
        
        coupure.save()
        
        return Response({
            'message': 'Position recalculée',
            'coupure': CoupureSerializer(coupure).data,
            'analyse': analyse
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detecter_coupure(request):
    """Endpoint pour détecter automatiquement une coupure"""
    # Données requises
    liaison_id = request.data.get('liaison_id')
    distance_coupure = request.data.get('distance_coupure')
    position_technicien = request.data.get('position_technicien', 'central')
    direction_analyse = request.data.get('direction_analyse', 'vers_client')
    point_mesure_id = request.data.get('point_mesure_id')
    attenuation = request.data.get('attenuation', 0.0)
    commentaires = request.data.get('commentaires', '')
    
    # Validation
    if not liaison_id or distance_coupure is None:
        return Response(
            {'error': 'liaison_id et distance_coupure sont requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        liaison = Liaison.objects.get(id=liaison_id)
    except Liaison.DoesNotExist:
        return Response(
            {'error': 'Liaison non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Point de mesure optionnel
    point_mesure = None
    if point_mesure_id:
        try:
            point_mesure = PointDynamique.objects.get(id=point_mesure_id)
        except PointDynamique.DoesNotExist:
            return Response(
                {'error': 'Point de mesure non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Créer la mesure OTDR
    mesure_data = {
        'liaison': liaison,
        'distance_coupure': float(distance_coupure),
        'attenuation': float(attenuation),
        'type_evenement': 'coupure',
        'position_technicien': position_technicien,
        'direction_analyse': direction_analyse,
        'point_mesure': point_mesure,
        'technicien': request.user,
        'commentaires': commentaires
    }
    
    mesure = MesureOTDR.objects.create(**mesure_data)
    
    # Analyser et créer la coupure
    coupure = CoupureService.creer_coupure(mesure)
    
    # Notifier
    NotificationService.notifier_coupure_detectee(coupure)
    
    # Analyser pour données supplémentaires
    analyse = CoupureService.analyser_coupure(mesure)
    
    return Response({
        'message': 'Coupure détectée et analysée',
        'mesure_otdr': MesureOTDRSerializer(mesure).data,
        'coupure': CoupureSerializer(coupure).data,
        'analyse': {
            'distance_absolue_km': analyse['distance_absolue'],
            'precision_estimation': analyse['precision_estimation'],
            'point_proche': {
                'nom': analyse['point_dynamique_proche'].nom if analyse['point_dynamique_proche'] else None,
                'distance_km': abs(analyse['point_dynamique_proche'].distance_depuis_central - analyse['distance_absolue']) if analyse['point_dynamique_proche'] else None
            } if analyse['point_dynamique_proche'] else None,
            'segment_info': {
                'depart': analyse['segment_touche'].point_depart.nom if analyse['segment_touche'] else None,
                'arrivee': analyse['segment_touche'].point_arrivee.nom if analyse['segment_touche'] else None,
                'distance_sur_segment_km': analyse['distance_sur_segment']
            } if analyse['segment_touche'] else None,
            'coordonnees_estimees': analyse['coordonnees_estimees']
        }
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simuler_analyse_otdr(request):
    """Simule une analyse OTDR pour tester la logique de détection"""
    liaison_id = request.data.get('liaison_id')
    distance_test = request.data.get('distance_test')
    position_test = request.data.get('position_test', 'central')
    direction_test = request.data.get('direction_test', 'vers_client')
    
    if not liaison_id or distance_test is None:
        return Response(
            {'error': 'liaison_id et distance_test requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        liaison = Liaison.objects.get(id=liaison_id)
    except Liaison.DoesNotExist:
        return Response(
            {'error': 'Liaison non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Créer une mesure temporaire (non sauvegardée)
    mesure_test = MesureOTDR(
        liaison=liaison,
        distance_coupure=float(distance_test),
        position_technicien=position_test,
        direction_analyse=direction_test,
        type_evenement='coupure',
        attenuation=0.0
    )
    
    # Analyser sans sauvegarder
    analyse = CoupureService.analyser_coupure(mesure_test)
    
    return Response({
        'message': 'Simulation d\'analyse OTDR',
        'parametres': {
            'liaison': liaison.nom_liaison,
            'distance_test_km': distance_test,
            'position_technicien': position_test,
            'direction_analyse': direction_test
        },
        'resultats': {
            'distance_absolue_km': analyse['distance_absolue'],
            'precision_estimation': analyse['precision_estimation'],
            'point_proche': {
                'nom': analyse['point_dynamique_proche'].nom if analyse['point_dynamique_proche'] else None,
                'type': analyse['point_dynamique_proche'].type_point if analyse['point_dynamique_proche'] else None,
                'distance_depuis_central': analyse['point_dynamique_proche'].distance_depuis_central if analyse['point_dynamique_proche'] else None,
                'ecart_km': abs(analyse['point_dynamique_proche'].distance_depuis_central - analyse['distance_absolue']) if analyse['point_dynamique_proche'] else None
            } if analyse['point_dynamique_proche'] else None,
            'segment_touche': {
                'depart': analyse['segment_touche'].point_depart.nom if analyse['segment_touche'] else None,
                'arrivee': analyse['segment_touche'].point_arrivee.nom if analyse['segment_touche'] else None,
                'distance_segment_km': analyse['segment_touche'].distance_cable if analyse['segment_touche'] else None,
                'distance_sur_segment_km': analyse['distance_sur_segment']
            } if analyse['segment_touche'] else None,
            'coordonnees_estimees': analyse['coordonnees_estimees']
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_diagnostics(request):
    """Statistiques des diagnostics OTDR"""
    from django.db.models import Count, Avg, Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Période (30 derniers jours par défaut)
    jours = int(request.query_params.get('jours', 30))
    date_debut = timezone.now() - timedelta(days=jours)
    
    # Mesures OTDR
    mesures_stats = MesureOTDR.objects.filter(date_mesure__gte=date_debut).aggregate(
        total_mesures=Count('id'),
        coupures_detectees=Count('id', filter=Q(type_evenement='coupure')),
        attenuation_moyenne=Avg('attenuation')
    )
    
    # Coupures
    coupures_stats = Coupure.objects.filter(date_detection__gte=date_debut).aggregate(
        total_coupures=Count('id'),
        coupures_reparees=Count('id', filter=Q(status='reparee')),
        coupures_en_cours=Count('id', filter=Q(status='en_cours'))
    )
    
    # Répartition par type d'événement OTDR
    repartition_evenements = list(
        MesureOTDR.objects.filter(date_mesure__gte=date_debut)
        .values('type_evenement')
        .annotate(count=Count('id'))
    )
    
    # Liaisons les plus touchées
    liaisons_touchees = list(
        Coupure.objects.filter(date_detection__gte=date_debut)
        .values('liaison__nom_liaison', 'liaison__client__name')
        .annotate(nb_coupures=Count('id'))
        .order_by('-nb_coupures')[:10]
    )
    
    return Response({
        'periode': f'{jours} derniers jours',
        'mesures_otdr': mesures_stats,
        'coupures': coupures_stats,
        'repartition_evenements': repartition_evenements,
        'liaisons_plus_touchees': liaisons_touchees,
        'taux_resolution': round(
            (coupures_stats['coupures_reparees'] / max(coupures_stats['total_coupures'], 1)) * 100, 2
        ) if coupures_stats['total_coupures'] > 0 else 0
    })