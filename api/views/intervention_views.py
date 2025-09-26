from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from ..models import Intervention, CommitIntervention
from ..serializers import (
    InterventionListSerializer, InterventionDetailSerializer, 
    InterventionCreateSerializer, CommitInterventionSerializer
)


class InterventionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les interventions"""
    queryset = Intervention.objects.all()
    serializer_class = InterventionListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type_intervention', 'technicien_principal', 'liaison']
    search_fields = ['description', 'liaison__nom_liaison', 'liaison__client__name']
    ordering_fields = ['date_planifiee', 'created_at']
    ordering = ['-date_planifiee']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InterventionCreateSerializer
        elif self.action == 'retrieve':
            return InterventionDetailSerializer
        return InterventionListSerializer
    
    def get_queryset(self):
        """Filtrer selon le rôle de l'utilisateur"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'technicien':
            # Les techniciens ne voient que leurs interventions
            return queryset.filter(
                Q(technicien_principal=user) | 
                Q(techniciens_secondaires=user)
            ).distinct()
        elif user.role == 'commercial':
            # Les commerciaux voient seulement les interventions qui affectent leurs clients
            return queryset.filter(liaison__client__in=user.clients_assigned.all())
        
        # Les superviseurs voient tout
        return queryset
    
    @action(detail=True, methods=['put'])
    def changer_status(self, request, pk=None):
        """Changer le statut d'une intervention"""
        intervention = self.get_object()
        nouveau_status = request.data.get('status')
        
        if nouveau_status not in dict(Intervention.STATUS_CHOICES):
            return Response({'error': 'Statut invalide'}, status=status.HTTP_400_BAD_REQUEST)
        
        ancien_status = intervention.status
        intervention.status = nouveau_status
        
        # Mettre à jour les timestamps selon le statut
        if nouveau_status == 'en_cours' and not intervention.date_debut:
            intervention.date_debut = timezone.now()
        elif nouveau_status == 'terminee' and not intervention.date_fin:
            intervention.date_fin = timezone.now()
        
        intervention.save()
        
        # Créer un commit automatique pour le changement de statut
        CommitIntervention.objects.create(
            intervention=intervention,
            message_commit=f"Changement de statut: {ancien_status} -> {nouveau_status}",
            changements_json={
                'type': 'status_change',
                'ancien_status': ancien_status,
                'nouveau_status': nouveau_status
            },
            auteur=request.user
        )
        
        return Response(InterventionDetailSerializer(intervention, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def commit(self, request, pk=None):
        """Enregistrer un commit pour une intervention"""
        intervention = self.get_object()
        data = request.data.copy()
        data['intervention'] = intervention.id
        data['auteur'] = request.user.id
        
        serializer = CommitInterventionSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def historique_commits(self, request, pk=None):
        """Récupérer l'historique des commits d'une intervention"""
        intervention = self.get_object()
        commits = intervention.commits.all()
        serializer = CommitInterventionSerializer(commits, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def planning_technicien(self, request):
        """Planning des interventions pour un technicien"""
        technicien_id = request.query_params.get('technicien_id')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        queryset = self.get_queryset()
        
        if technicien_id:
            queryset = queryset.filter(
                Q(technicien_principal_id=technicien_id) |
                Q(techniciens_secondaires__id=technicien_id)
            ).distinct()
        
        if date_debut:
            queryset = queryset.filter(date_planifiee__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_planifiee__lte=date_fin)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tableau_bord(self, request):
        """Tableau de bord des interventions"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'par_status': {},
            'par_type': {},
            'en_retard': queryset.filter(
                date_planifiee__lt=timezone.now(),
                status__in=['planifiee', 'en_cours']
            ).count()
        }
        
        # Stats par statut
        for status_choice in Intervention.STATUS_CHOICES:
            status_code = status_choice[0]
            count = queryset.filter(status=status_code).count()
            stats['par_status'][status_code] = count
        
        # Stats par type
        for type_choice in Intervention.TYPE_CHOICES:
            type_code = type_choice[0]
            count = queryset.filter(type_intervention=type_code).count()
            stats['par_type'][type_code] = count
        
        return Response(stats)


class CommitInterventionViewSet(viewsets.ModelViewSet):
    """ViewSet pour les commits d'intervention"""
    queryset = CommitIntervention.objects.all()
    serializer_class = CommitInterventionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['intervention', 'auteur']
    search_fields = ['message_commit', 'description_detaillee']
    ordering_fields = ['date_commit']
    ordering = ['-date_commit']
    
    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user)