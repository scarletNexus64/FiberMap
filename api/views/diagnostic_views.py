from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
import math
from ..models import MesureOTDR, Coupure, Liaison, PointDynamique, Notification
from ..serializers import MesureOTDRSerializer, CoupureSerializer


def calculer_position_coupure(liaison, distance_coupure):
    """Calculer la position GPS estimée d'une coupure sur une liaison"""
    # Coordonnées du point central et client
    lat1 = float(liaison.point_central_lat)
    lng1 = float(liaison.point_central_lng)
    lat2 = float(liaison.point_client_lat)
    lng2 = float(liaison.point_client_lng)
    
    # Calculer le ratio de la distance de coupure par rapport à la distance totale
    ratio = distance_coupure / liaison.distance_totale
    
    # Interpolation linéaire simple (pour une approximation)
    lat_coupure = lat1 + (lat2 - lat1) * ratio
    lng_coupure = lng1 + (lng2 - lng1) * ratio
    
    return lat_coupure, lng_coupure


def trouver_point_dynamique_proche(liaison, lat_coupure, lng_coupure, rayon_km=0.5):
    """Trouver le point dynamique le plus proche de la coupure estimée"""
    points = liaison.points_dynamiques.all()
    point_plus_proche = None
    distance_min = float('inf')
    
    for point in points:
        # Calcul de distance approximative (formule haversine simplifiée)
        lat_diff = abs(float(point.latitude) - lat_coupure)
        lng_diff = abs(float(point.longitude) - lng_coupure)
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111  # Approximation en km
        
        if distance < distance_min and distance <= rayon_km:
            distance_min = distance
            point_plus_proche = point
    
    return point_plus_proche


class MesureOTDRViewSet(viewsets.ModelViewSet):
    """ViewSet pour les mesures OTDR"""
    queryset = MesureOTDR.objects.all()
    serializer_class = MesureOTDRSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['liaison', 'technicien', 'type_evenement']
    search_fields = ['commentaires', 'liaison__nom_liaison']
    ordering_fields = ['date_mesure', 'distance_coupure', 'attenuation']
    ordering = ['-date_mesure']
    
    def perform_create(self, serializer):
        serializer.save(technicien=self.request.user)
    
    @action(detail=False, methods=['get'])
    def par_liaison(self, request):
        """Récupérer les mesures OTDR d'une liaison spécifique"""
        liaison_id = request.query_params.get('liaison_id')
        if not liaison_id:
            return Response({'error': 'liaison_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        mesures = self.get_queryset().filter(liaison_id=liaison_id)
        serializer = self.get_serializer(mesures, many=True)
        return Response(serializer.data)


class CoupureViewSet(viewsets.ModelViewSet):
    """ViewSet pour les coupures"""
    queryset = Coupure.objects.all()
    serializer_class = CoupureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'liaison', 'superviseur_notifie', 'client_notifie']
    search_fields = ['description_diagnostic', 'liaison__nom_liaison', 'liaison__client__name']
    ordering_fields = ['date_detection', 'date_resolution']
    ordering = ['-date_detection']
    
    @action(detail=True, methods=['put'])
    def changer_status(self, request, pk=None):
        """Changer le statut d'une coupure"""
        coupure = self.get_object()
        nouveau_status = request.data.get('status')
        
        if nouveau_status not in dict(Coupure.STATUS_CHOICES):
            return Response({'error': 'Statut invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        ancien_status = coupure.status
        coupure.status = nouveau_status
        
        if nouveau_status == 'reparee' and not coupure.date_resolution:
            coupure.date_resolution = timezone.now()
        
        coupure.save()
        
        # Créer une notification pour le changement de statut
        if nouveau_status == 'reparee':
            # Notifier le superviseur et potentiellement le client
            from ..models import User
            superviseurs = User.objects.filter(role='superviseur')
            
            for superviseur in superviseurs:
                Notification.objects.create(
                    destinataire=superviseur,
                    type_notification='alerte',
                    titre=f'Coupure réparée - {coupure.liaison.nom_liaison}',
                    message=f'La coupure sur la liaison {coupure.liaison.nom_liaison} a été réparée.',
                    liaison=coupure.liaison,
                    coupure=coupure
                )
        
        return Response(CoupureSerializer(coupure, context={'request': request}).data)
    
    @action(detail=False, methods=['get'])
    def actives(self, request):
        """Récupérer toutes les coupures actives"""
        coupures_actives = self.get_queryset().filter(status__in=['detectee', 'en_cours'])
        serializer = self.get_serializer(coupures_actives, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def carte(self, request):
        """Données des coupures pour affichage sur carte"""
        coupures = self.get_queryset().filter(
            point_estime_lat__isnull=False,
            point_estime_lng__isnull=False
        )
        
        # Filtrage géographique optionnel
        lat_min = request.query_params.get('lat_min')
        lat_max = request.query_params.get('lat_max')
        lng_min = request.query_params.get('lng_min')
        lng_max = request.query_params.get('lng_max')
        
        if all([lat_min, lat_max, lng_min, lng_max]):
            coupures = coupures.filter(
                point_estime_lat__gte=lat_min,
                point_estime_lat__lte=lat_max,
                point_estime_lng__gte=lng_min,
                point_estime_lng__lte=lng_max
            )
        
        # Format optimisé pour la carte
        coupures_carte = []
        for coupure in coupures:
            coupures_carte.append({
                'id': str(coupure.id),
                'lat': float(coupure.point_estime_lat),
                'lng': float(coupure.point_estime_lng),
                'status': coupure.status,
                'liaison': coupure.liaison.nom_liaison,
                'client': coupure.liaison.client.name,
                'date_detection': coupure.date_detection.isoformat(),
                'description': coupure.description_diagnostic[:100] + '...' if len(coupure.description_diagnostic) > 100 else coupure.description_diagnostic
            })
        
        return Response(coupures_carte)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detecter_coupure(request):
    """Détecter et créer une coupure à partir d'une mesure OTDR"""
    mesure_otdr_id = request.data.get('mesure_otdr_id')
    description_diagnostic = request.data.get('description_diagnostic', '')
    
    if not mesure_otdr_id:
        return Response({'error': 'mesure_otdr_id requis'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        mesure = MesureOTDR.objects.get(id=mesure_otdr_id)
    except MesureOTDR.DoesNotExist:
        return Response({'error': 'Mesure OTDR introuvable'}, status=status.HTTP_404_NOT_FOUND)
    
    # Calculer la position estimée de la coupure
    lat_coupure, lng_coupure = calculer_position_coupure(mesure.liaison, mesure.distance_coupure)
    
    # Trouver le point dynamique le plus proche
    point_proche = trouver_point_dynamique_proche(mesure.liaison, lat_coupure, lng_coupure)
    
    # Créer la coupure
    coupure = Coupure.objects.create(
        liaison=mesure.liaison,
        mesure_otdr=mesure,
        point_estime_lat=lat_coupure,
        point_estime_lng=lng_coupure,
        point_dynamique_proche=point_proche,
        description_diagnostic=description_diagnostic
    )
    
    # Créer des notifications pour les superviseurs
    from ..models import User
    superviseurs = User.objects.filter(role='superviseur')
    
    for superviseur in superviseurs:
        Notification.objects.create(
            destinataire=superviseur,
            type_notification='coupure',
            titre=f'Nouvelle coupure détectée - {mesure.liaison.nom_liaison}',
            message=f'Une coupure a été détectée sur la liaison {mesure.liaison.nom_liaison} à {mesure.distance_coupure}km du central.',
            liaison=mesure.liaison,
            coupure=coupure
        )
    
    # Marquer la liaison en panne
    mesure.liaison.status = 'en_panne'
    mesure.liaison.save()
    
    return Response(CoupureSerializer(coupure, context={'request': request}).data, 
                    status=status.HTTP_201_CREATED)