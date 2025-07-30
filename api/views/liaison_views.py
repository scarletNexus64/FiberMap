from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from ..models import Liaison, PointDynamique, PhotoPoint, FicheTechnique
from ..serializers import (
    LiaisonSerializer, LiaisonDetailSerializer, PointDynamiqueSerializer,
    PhotoPointSerializer, FicheTechniqueSerializer
)


class LiaisonViewSet(viewsets.ModelViewSet):
    """ViewSet pour les liaisons"""
    queryset = Liaison.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type_liaison', 'client']
    search_fields = ['nom_liaison', 'client__name']
    ordering_fields = ['nom_liaison', 'created_at', 'distance_totale']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LiaisonDetailSerializer
        return LiaisonSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def trace(self, request, pk=None):
        """Récupérer le tracé complet d'une liaison avec tous ses points"""
        liaison = self.get_object()
        points = liaison.points_dynamiques.all()
        
        # Construire le tracé avec les coordonnées dans l'ordre
        trace_points = [
            {
                'lat': float(liaison.point_central_lat),
                'lng': float(liaison.point_central_lng),
                'type': 'central',
                'nom': 'Point Central'
            }
        ]
        
        for point in points:
            trace_points.append({
                'lat': float(point.latitude),
                'lng': float(point.longitude),
                'type': point.type_point,
                'nom': point.nom,
                'distance': point.distance_depuis_central
            })
        
        trace_points.append({
            'lat': float(liaison.point_client_lat),
            'lng': float(liaison.point_client_lng),
            'type': 'client',
            'nom': f'Client - {liaison.client.name}'
        })
        
        return Response({
            'liaison': LiaisonDetailSerializer(liaison, context={'request': request}).data,
            'trace': trace_points
        })
    
    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """Historique des interventions d'une liaison"""
        liaison = self.get_object()
        interventions = liaison.interventions.all()
        from ..serializers import InterventionSerializer
        serializer = InterventionSerializer(interventions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recherche_avancee(self, request):
        """Recherche avancée avec filtres géographiques"""
        lat_min = request.query_params.get('lat_min')
        lat_max = request.query_params.get('lat_max')
        lng_min = request.query_params.get('lng_min')
        lng_max = request.query_params.get('lng_max')
        
        queryset = self.get_queryset()
        
        if all([lat_min, lat_max, lng_min, lng_max]):
            # Filtrer par zone géographique (bounding box)
            queryset = queryset.filter(
                Q(point_central_lat__gte=lat_min, point_central_lat__lte=lat_max,
                  point_central_lng__gte=lng_min, point_central_lng__lte=lng_max) |
                Q(point_client_lat__gte=lat_min, point_client_lat__lte=lat_max,
                  point_client_lng__gte=lng_min, point_client_lng__lte=lng_max)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PointDynamiqueViewSet(viewsets.ModelViewSet):
    """ViewSet pour les points dynamiques"""
    queryset = PointDynamique.objects.all()
    serializer_class = PointDynamiqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_point', 'liaison', 'presence_splitter']
    search_fields = ['nom', 'description']
    ordering_fields = ['distance_depuis_central', 'created_at']
    ordering = ['distance_depuis_central']
    
    @action(detail=True, methods=['post'])
    def ajouter_photo(self, request, pk=None):
        """Ajouter une photo à un point dynamique"""
        point = self.get_object()
        data = request.data.copy()
        data['point_dynamique'] = point.id
        data['uploaded_by'] = request.user.id
        
        serializer = PhotoPointSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
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
                serializer = FicheTechniqueSerializer(fiche, context={'request': request})
                return Response(serializer.data)
            except FicheTechnique.DoesNotExist:
                return Response({'detail': 'Aucune fiche technique trouvée'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data['point_dynamique'] = point.id
            
            serializer = FicheTechniqueSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'PUT':
            try:
                fiche = point.fichetechnique
                serializer = FicheTechniqueSerializer(fiche, data=request.data, 
                                                    partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except FicheTechnique.DoesNotExist:
                return Response({'detail': 'Aucune fiche technique trouvée'}, 
                              status=status.HTTP_404_NOT_FOUND)


class PhotoPointViewSet(viewsets.ModelViewSet):
    """ViewSet pour les photos des points"""
    queryset = PhotoPoint.objects.all()
    serializer_class = PhotoPointSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['point_dynamique', 'uploaded_by']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class FicheTechniqueViewSet(viewsets.ModelViewSet):
    """ViewSet pour les fiches techniques"""
    queryset = FicheTechnique.objects.all()
    serializer_class = FicheTechniqueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['point_dynamique', 'fabricant']
    search_fields = ['modele_equipement', 'numero_serie', 'fabricant']
    ordering_fields = ['date_installation', 'created_at']
    ordering = ['-created_at']