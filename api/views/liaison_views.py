from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from ..models import (
    Liaison, PointDynamique, PhotoPoint, FicheTechnique, Segment,
    DetailONT, DetailPOPLS, DetailPOPFTTH, DetailChambre, DetailManchon,
    FAT, DetailFDT
)
from ..serializers import (
    LiaisonListSerializer, LiaisonDetailSerializer, LiaisonCreateSerializer,
    PointDynamiqueListSerializer, PointDynamiqueDetailSerializer, PointDynamiqueCreateSerializer,
    PhotoPointSerializer, FicheTechniqueSerializer, SegmentSerializer,
    FATSerializer, FATCreateSerializer, ChoixSerializer
)
from ..services import LiaisonService, SegmentService

class LiaisonViewSet(viewsets.ModelViewSet):
    """ViewSet pour les liaisons"""
    queryset = Liaison.objects.select_related('client', 'type_liaison', 'created_by')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type_liaison', 'client', 'client__type_client']
    search_fields = ['nom_liaison', 'client__name', 'client__raison_sociale']
    ordering_fields = ['nom_liaison', 'created_at', 'distance_totale', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LiaisonDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LiaisonCreateSerializer
        return LiaisonListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def trace(self, request, pk=None):
        """Récupérer le tracé complet d'une liaison avec segments"""
        liaison = self.get_object()
        
        # Points dynamiques avec leurs détails
        points = PointDynamiqueDetailSerializer(
            liaison.points_dynamiques.order_by('ordre'), 
            many=True, 
            context={'request': request}
        ).data
        
        # Segments
        segments = SegmentSerializer(
            liaison.segments.order_by('point_depart__ordre'), 
            many=True
        ).data
        
        return Response({
            'liaison': LiaisonDetailSerializer(liaison, context={'request': request}).data,
            'points_dynamiques': points,
            'segments': segments,
            'trace_coordonnees': self._construire_trace_complet(liaison)
        })
    
    def _construire_trace_complet(self, liaison):
        """Construit le tracé complet avec coordonnées interpolées"""
        points = liaison.points_dynamiques.order_by('ordre')
        segments = liaison.segments.order_by('point_depart__ordre')
        
        trace = []
        
        # Point central
        trace.append({
            'lat': float(liaison.point_central_lat),
            'lng': float(liaison.point_central_lng),
            'type': 'central',
            'nom': 'Central'
        })
        
        # Points dynamiques avec interpolation des segments
        for point in points:
            # Ajouter les coordonnées du tracé du segment précédent si disponible
            segment = segments.filter(point_arrivee=point).first()
            if segment and segment.trace_coords:
                for coord in segment.trace_coords:
                    trace.append({
                        'lat': coord[0],
                        'lng': coord[1],
                        'type': 'trace',
                        'segment_id': str(segment.id)
                    })
            
            # Point dynamique
            trace.append({
                'lat': float(point.latitude),
                'lng': float(point.longitude),
                'type': point.type_point,
                'nom': point.nom,
                'id': str(point.id),
                'ordre': point.ordre
            })
        
        # Point client
        trace.append({
            'lat': float(liaison.point_client_lat),
            'lng': float(liaison.point_client_lng),
            'type': 'client',
            'nom': f'Client - {liaison.client.name}'
        })
        
        return trace
    
    @action(detail=True, methods=['post'])
    def recalculer_distance(self, request, pk=None):
        """Recalcule la distance totale de la liaison"""
        liaison = self.get_object()
        distance_totale = liaison.calculer_distance_totale()
        
        return Response({
            'message': 'Distance recalculée',
            'distance_totale': distance_totale,
            'nombre_segments': liaison.segments.count()
        })
    
    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """Historique des interventions sur une liaison"""
        liaison = self.get_object()
        interventions = liaison.interventions.select_related('technicien_principal').order_by('-date_planifiee')
        
        from ..serializers import InterventionListSerializer
        
        return Response({
            'liaison': liaison.nom_liaison,
            'interventions': InterventionListSerializer(interventions, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def recherche_avancee(self, request):
        """Recherche avancée avec filtres multiples"""
        queryset = self.get_queryset()
        
        # Filtres personnalisés
        client_type = request.query_params.get('client_type')
        has_coupures = request.query_params.get('has_coupures')
        distance_min = request.query_params.get('distance_min')
        distance_max = request.query_params.get('distance_max')
        
        if client_type:
            queryset = queryset.filter(client__type_client=client_type)
        
        if has_coupures == 'true':
            queryset = queryset.filter(coupures__isnull=False).distinct()
        elif has_coupures == 'false':
            queryset = queryset.filter(coupures__isnull=True)
        
        if distance_min:
            queryset = queryset.filter(distance_totale__gte=float(distance_min))
        
        if distance_max:
            queryset = queryset.filter(distance_totale__lte=float(distance_max))
        
        # Appliquer les filtres standards
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PointDynamiqueViewSet(viewsets.ModelViewSet):
    """ViewSet pour les points dynamiques"""
    queryset = PointDynamique.objects.select_related('liaison')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_point', 'liaison', 'liaison__client']
    search_fields = ['nom', 'description', 'liaison__nom_liaison']
    ordering_fields = ['nom', 'ordre', 'distance_depuis_central', 'created_at']
    ordering = ['liaison', 'ordre']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PointDynamiqueDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PointDynamiqueCreateSerializer
        return PointDynamiqueListSerializer
    
    @action(detail=True, methods=['post'])
    def ajouter_photo(self, request, pk=None):
        """Ajouter une photo à un point dynamique"""
        point = self.get_object()
        
        serializer = PhotoPointSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(point_dynamique=point)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Récupérer toutes les photos d'un point"""
        point = self.get_object()
        photos = point.photos.all()
        serializer = PhotoPointSerializer(photos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post', 'put'])
    def fiche_technique(self, request, pk=None):
        """Gérer la fiche technique d'un point"""
        point = self.get_object()
        
        if request.method == 'GET':
            try:
                fiche = point.fichetechnique
                serializer = FicheTechniqueSerializer(fiche)
                return Response(serializer.data)
            except FicheTechnique.DoesNotExist:
                return Response({'message': 'Aucune fiche technique'}, status=status.HTTP_404_NOT_FOUND)
        
        elif request.method in ['POST', 'PUT']:
            try:
                fiche = point.fichetechnique
                serializer = FicheTechniqueSerializer(fiche, data=request.data, partial=True)
            except FicheTechnique.DoesNotExist:
                serializer = FicheTechniqueSerializer(data=request.data)
            
            if serializer.is_valid():
                serializer.save(point_dynamique=point)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'])
    def mettre_a_jour_details(self, request, pk=None):
        """Met à jour les détails spécifiques selon le type de point"""
        point = self.get_object()
        type_point = point.type_point
        
        # Choisir le bon serializer selon le type
        detail_serializer = None
        detail_instance = None
        
        try:
            if type_point == 'ONT':
                detail_instance = point.detail_ont
                detail_serializer = DetailONTSerializer
            elif type_point == 'POP_LS':
                detail_instance = point.detail_pop_ls
                detail_serializer = DetailPOPLSSerializer
            elif type_point == 'POP_FTTH':
                detail_instance = point.detail_pop_ftth
                detail_serializer = DetailPOPFTTHSerializer
            elif type_point == 'chambre':
                detail_instance = point.detail_chambre
                detail_serializer = DetailChambreSerializer
            elif type_point in ['manchon', 'manchon_aerien']:
                detail_instance = point.detail_manchon
                detail_serializer = DetailManchonSerializer
            elif type_point == 'FDT':
                detail_instance = point.detail_fdt
                detail_serializer = DetailFDTSerializer
        except:
            detail_instance = None
        
        if not detail_serializer:
            return Response(
                {'error': f'Type de point {type_point} non supporté pour les détails'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer ou mettre à jour les détails
        if detail_instance:
            serializer = detail_serializer(detail_instance, data=request.data, partial=True)
        else:
            serializer = detail_serializer(data=request.data)
        
        if serializer.is_valid():
            if not detail_instance:
                serializer.save(point_dynamique=point)
            else:
                serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SegmentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les segments"""
    queryset = Segment.objects.select_related('liaison', 'point_depart', 'point_arrivee')
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['liaison', 'point_depart', 'point_arrivee']
    ordering = ['point_depart__ordre']
    
    @action(detail=True, methods=['put'])
    def mettre_a_jour_trace(self, request, pk=None):
        """Met à jour le tracé GPS d'un segment"""
        segment = self.get_object()
        trace_coords = request.data.get('trace_coords', [])
        
        # Valider le format des coordonnées
        if not isinstance(trace_coords, list):
            return Response(
                {'error': 'trace_coords doit être une liste'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for coord in trace_coords:
            if not isinstance(coord, list) or len(coord) != 2:
                return Response(
                    {'error': 'Chaque coordonnée doit être [latitude, longitude]'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        segment.trace_coords = trace_coords
        segment.save()
        
        # Recalculer la distance totale si nécessaire
        segment.liaison.calculer_distance_totale()
        
        return Response({
            'message': 'Tracé mis à jour',
            'segment': SegmentSerializer(segment).data
        })
    
    @action(detail=True, methods=['post'])
    def recalculer_distance_gps(self, request, pk=None):
        """Recalcule la distance GPS basée sur les coordonnées"""
        segment = self.get_object()
        
        nouvelle_distance = SegmentService.calculer_distance_gps(
            float(segment.point_depart.latitude),
            float(segment.point_depart.longitude),
            float(segment.point_arrivee.latitude),
            float(segment.point_arrivee.longitude)
        )
        
        segment.distance_gps = nouvelle_distance
        segment.save()
        
        return Response({
            'message': 'Distance GPS recalculée',
            'distance_gps': nouvelle_distance
        })

class PhotoPointViewSet(viewsets.ModelViewSet):
    """ViewSet pour les photos des points"""
    queryset = PhotoPoint.objects.select_related('point_dynamique', 'uploaded_by')
    serializer_class = PhotoPointSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['point_dynamique', 'categorie', 'uploaded_by']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

class FicheTechniqueViewSet(viewsets.ModelViewSet):
    """ViewSet pour les fiches techniques"""
    queryset = FicheTechnique.objects.select_related('point_dynamique')
    serializer_class = FicheTechniqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['point_dynamique', 'fabricant']
    search_fields = ['modele_equipement', 'numero_serie', 'fabricant']

class FATViewSet(viewsets.ModelViewSet):
    """ViewSet pour les FATs indépendants"""
    queryset = FAT.objects.select_related('liaison', 'point_dynamique')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['numero_fdt', 'liaison']
    search_fields = ['numero_fat', 'numero_fdt', 'port_splitter']
    ordering_fields = ['numero_fat', 'created_at']
    ordering = ['numero_fat']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FATCreateSerializer
        return FATSerializer
    
    @action(detail=True, methods=['post'])
    def associer_liaison(self, request, pk=None):
        """Associe un FAT à une liaison existante"""
        fat = self.get_object()
        liaison_id = request.data.get('liaison_id')
        
        if not liaison_id:
            return Response(
                {'error': 'liaison_id requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            liaison = Liaison.objects.get(id=liaison_id)
            fat.liaison = liaison
            fat.save()
            
            return Response({
                'message': f'FAT {fat.numero_fat} associé à la liaison {liaison.nom_liaison}',
                'fat': FATSerializer(fat).data
            })
        except Liaison.DoesNotExist:
            return Response(
                {'error': 'Liaison non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def creer_point_dynamique(self, request, pk=None):
        """Crée un point dynamique pour ce FAT"""
        fat = self.get_object()
        
        if fat.point_dynamique:
            return Response(
                {'error': 'Ce FAT a déjà un point dynamique associé'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not fat.liaison:
            return Response(
                {'error': 'Le FAT doit être associé à une liaison'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer le point dynamique
        point_data = {
            'liaison': fat.liaison,
            'type_point': 'FAT',
            'nom': f'FAT {fat.numero_fat}',
            'latitude': fat.latitude,
            'longitude': fat.longitude,
            'ordre': fat.liaison.points_dynamiques.count(),
            'description': f'FAT {fat.numero_fat} - FDT {fat.numero_fdt}'
        }
        
        point = PointDynamique.objects.create(**point_data)
        fat.point_dynamique = point
        fat.save()
        
        return Response({
            'message': 'Point dynamique créé pour le FAT',
            'point_dynamique': PointDynamiqueDetailSerializer(point).data
        })

# Vue pour les choix/options de l'application
@action(detail=False, methods=['get'])
def choix_application(request):
    """Retourne tous les choix disponibles dans l'application"""
    choix = ChoixSerializer({})
    return Response(choix.data)