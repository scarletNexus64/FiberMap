from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from ..models import Notification, ParametreApplication
from ..serializers import NotificationSerializer, ParametreApplicationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les notifications (lecture seule via API)"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_notification', 'lue']
    search_fields = ['titre', 'message']
    ordering_fields = ['date_creation', 'date_lecture']
    ordering = ['-date_creation']
    
    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user)
    
    @action(detail=True, methods=['put'])
    def marquer_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        if not notification.lue:
            notification.lue = True
            notification.date_lecture = timezone.now()
            notification.save()
        
        return Response({'status': 'notification marquée comme lue'})
    
    @action(detail=False, methods=['put'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        notifications = self.get_queryset().filter(lue=False)
        notifications.update(lue=True, date_lecture=timezone.now())
        
        return Response({'status': f'{notifications.count()} notifications marquées comme lues'})
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Récupérer les notifications non lues"""
        notifications = self.get_queryset().filter(lue=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def resume(self, request):
        """Résumé des notifications"""
        queryset = self.get_queryset()
        
        resume = {
            'total': queryset.count(),
            'non_lues': queryset.filter(lue=False).count(),
            'par_type': {}
        }
        
        # Compter par type de notification
        types_count = queryset.values('type_notification').annotate(count=Count('id'))
        for item in types_count:
            resume['par_type'][item['type_notification']] = item['count']
        
        # Notifications récentes (dernières 24h)
        from datetime import timedelta
        hier = timezone.now() - timedelta(days=1)
        resume['recentes_24h'] = queryset.filter(date_creation__gte=hier).count()
        
        return Response(resume)
    
    @action(detail=False, methods=['delete'])
    def supprimer_lues(self, request):
        """Supprimer toutes les notifications lues"""
        notifications_lues = self.get_queryset().filter(lue=True)
        count = notifications_lues.count()
        notifications_lues.delete()
        
        return Response({'status': f'{count} notifications supprimées'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_notification(request):
    """Créer une notification manuelle (pour les superviseurs)"""
    if request.user.role != 'superviseur':
        return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
    
    data = request.data.copy()
    
    # Valider les destinataires
    destinataire_ids = data.get('destinataires', [])
    if not destinataire_ids:
        return Response({'error': 'Au moins un destinataire requis'}, status=status.HTTP_400_BAD_REQUEST)
    
    from ..models import User
    destinataires = User.objects.filter(id__in=destinataire_ids)
    
    notifications_creees = []
    for destinataire in destinataires:
        notification_data = {
            'destinataire': destinataire.id,
            'type_notification': data.get('type_notification'),
            'titre': data.get('titre'),
            'message': data.get('message'),
            'liaison': data.get('liaison'),
            'coupure': data.get('coupure'),
            'intervention': data.get('intervention')
        }
        
        serializer = NotificationSerializer(data=notification_data, context={'request': request})
        if serializer.is_valid():
            notification = serializer.save()
            notifications_creees.append(notification)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': f'{len(notifications_creees)} notifications créées',
        'notifications': NotificationSerializer(notifications_creees, many=True, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_notifications(request):
    """Statistiques globales des notifications (superviseurs seulement)"""
    if request.user.role != 'superviseur':
        return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)
    
    from datetime import timedelta
    from ..models import User
    
    # Période d'analyse (par défaut 30 jours)
    jours = int(request.query_params.get('jours', 30))
    date_debut = timezone.now() - timedelta(days=jours)
    
    # Stats globales
    total_notifications = Notification.objects.filter(date_creation__gte=date_debut)
    
    stats = {
        'periode': {
            'debut': date_debut.isoformat(),
            'fin': timezone.now().isoformat(),
            'jours': jours
        },
        'global': {
            'total': total_notifications.count(),
            'lues': total_notifications.filter(lue=True).count(),
            'non_lues': total_notifications.filter(lue=False).count()
        },
        'par_type': {},
        'par_utilisateur': {},
        'tendance_quotidienne': []
    }
    
    # Stats par type
    types_count = total_notifications.values('type_notification').annotate(count=Count('id'))
    for item in types_count:
        stats['par_type'][item['type_notification']] = item['count']
    
    # Stats par utilisateur
    users_count = total_notifications.values('destinataire__username', 'destinataire__role').annotate(
        total=Count('id'),
        non_lues=Count('id', filter=Q(lue=False))
    )
    
    for item in users_count:
        username = item['destinataire__username']
        stats['par_utilisateur'][username] = {
            'role': item['destinataire__role'],
            'total': item['total'],
            'non_lues': item['non_lues'],
            'taux_lecture': round((item['total'] - item['non_lues']) / item['total'] * 100, 2) if item['total'] > 0 else 0
        }
    
    # Tendance quotidienne (derniers 7 jours)
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        date_debut_jour = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        date_fin_jour = date_debut_jour + timedelta(days=1)
        
        count = Notification.objects.filter(
            date_creation__gte=date_debut_jour,
            date_creation__lt=date_fin_jour
        ).count()
        
        stats['tendance_quotidienne'].append({
            'date': date.isoformat(),
            'count': count
        })
    
    stats['tendance_quotidienne'].reverse()  # Ordre chronologique
    
    return Response(stats)


class ParametreApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les paramètres d'application (superviseurs seulement)"""
    queryset = ParametreApplication.objects.all()
    serializer_class = ParametreApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_donnee']
    search_fields = ['cle', 'description']
    ordering_fields = ['cle', 'created_at']
    ordering = ['cle']
    
    def get_permissions(self):
        """Seuls les superviseurs peuvent modifier les paramètres"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
            # Vérification du rôle dans perform_create/update
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        if self.request.user.role != 'superviseur':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les superviseurs peuvent créer des paramètres")
        serializer.save()
    
    def perform_update(self, serializer):
        if self.request.user.role != 'superviseur':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les superviseurs peuvent modifier des paramètres")
        serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.role != 'superviseur':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les superviseurs peuvent supprimer des paramètres")
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def par_type(self, request):
        """Récupérer les paramètres groupés par type"""
        types = {}
        for param in self.get_queryset():
            if param.type_donnee not in types:
                types[param.type_donnee] = []
            types[param.type_donnee].append({
                'id': str(param.id),
                'cle': param.cle,
                'valeur': param.valeur,
                'description': param.description
            })
        
        return Response(types)