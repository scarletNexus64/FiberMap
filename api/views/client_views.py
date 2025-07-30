from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Client, TypeLiaison
from ..serializers import ClientSerializer, TypeLiaisonSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet pour les clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type']
    search_fields = ['name', 'address', 'phone', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def liaisons(self, request, pk=None):
        """Récupérer les liaisons d'un client"""
        client = self.get_object()
        liaisons = client.liaisons.all()
        from ..serializers import LiaisonSerializer
        serializer = LiaisonSerializer(liaisons, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des clients"""
        stats = {
            'total': Client.objects.count(),
            'par_type': {}
        }
        
        for type_choice in Client._meta.get_field('type').choices:
            type_code = type_choice[0]
            count = Client.objects.filter(type=type_code).count()
            stats['par_type'][type_code] = count
            
        return Response(stats)


class TypeLiaisonViewSet(viewsets.ModelViewSet):
    """ViewSet pour les types de liaisons"""
    queryset = TypeLiaison.objects.all()
    serializer_class = TypeLiaisonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type']
    search_fields = ['type', 'description']