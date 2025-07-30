from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import hello
from .views.auth_views import (
    login_view, logout_view, profile_view
)
from .views.client_views import (
    ClientViewSet, TypeLiaisonViewSet
)
from .views.liaison_views import (
    LiaisonViewSet, PointDynamiqueViewSet, PhotoPointViewSet, FicheTechniqueViewSet
)
from .views.intervention_views import (
    InterventionViewSet, CommitInterventionViewSet
)
from .views.diagnostic_views import (
    MesureOTDRViewSet, CoupureViewSet, detecter_coupure
)
from .views.map_views import (
    liaisons_carte, liaisons_bounds, points_dynamiques_carte, coupures_carte,
    trace_liaison, navigation_vers_point, mettre_a_jour_position
)
from .views.notification_views import (
    NotificationViewSet, creer_notification, statistiques_notifications, ParametreApplicationViewSet
)

# Configuration du router DRF
router = DefaultRouter()

# Enregistrement des ViewSets
router.register(r'users', NotificationViewSet, basename='user-notifications')
router.register(r'clients', ClientViewSet)
router.register(r'types-liaisons', TypeLiaisonViewSet)
router.register(r'liaisons', LiaisonViewSet)
router.register(r'points-dynamiques', PointDynamiqueViewSet)
router.register(r'photos-points', PhotoPointViewSet)
router.register(r'fiches-techniques', FicheTechniqueViewSet)
router.register(r'interventions', InterventionViewSet)
router.register(r'commits-interventions', CommitInterventionViewSet)
router.register(r'mesures-otdr', MesureOTDRViewSet)
router.register(r'coupures', CoupureViewSet)
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'parametres', ParametreApplicationViewSet)

urlpatterns = [
    # ===============================
    # Endpoint de test
    # ===============================
    path('hello/', hello, name='api-hello'),
    
    # ===============================
    # Authentification
    # ===============================
    path('auth/login/', login_view, name='api-login'),
    path('auth/logout/', logout_view, name='api-logout'),
    path('auth/profile/', profile_view, name='api-profile'),
    path('auth/token/', obtain_auth_token, name='api-token'),  # DRF token auth
    
    # ===============================
    # Cartographie et navigation
    # ===============================
    path('map/liaisons/', liaisons_carte, name='liaisons-carte'),
    path('map/liaisons/bounds/', liaisons_bounds, name='liaisons-bounds'),
    path('map/points-dynamiques/', points_dynamiques_carte, name='points-dynamiques-carte'),
    path('map/coupures/', coupures_carte, name='coupures-carte'),
    path('map/trace/<uuid:liaison_id>/', trace_liaison, name='trace-liaison'),
    
    # Navigation GPS
    path('navigation/point/', navigation_vers_point, name='navigation-point'),
    path('navigation/position/', mettre_a_jour_position, name='position-technicien'),
    
    # ===============================
    # Diagnostic OTDR
    # ===============================
    path('diagnostic/detecter-coupure/', detecter_coupure, name='detecter-coupure'),
    
    # ===============================
    # Notifications et administration
    # ===============================
    path('notifications/creer/', creer_notification, name='creer-notification'),
    path('notifications/statistiques/', statistiques_notifications, name='stats-notifications'),
    
    # ===============================
    # Routes du router DRF
    # ===============================
    path('', include(router.urls)),
]

# URLs nommées pour faciliter la documentation API
urlpatterns += [
    # Endpoints spécialisés avec noms explicites
    path('liaisons/<uuid:pk>/trace/', LiaisonViewSet.as_view({'get': 'trace'}), name='liaison-trace'),
    path('liaisons/<uuid:pk>/historique/', LiaisonViewSet.as_view({'get': 'historique'}), name='liaison-historique'),
    path('liaisons/recherche-avancee/', LiaisonViewSet.as_view({'get': 'recherche_avancee'}), name='liaison-recherche'),
    
    path('points-dynamiques/<uuid:pk>/photos/', PointDynamiqueViewSet.as_view({'post': 'ajouter_photo', 'get': 'photos'}), name='point-photos'),
    path('points-dynamiques/<uuid:pk>/fiche-technique/', PointDynamiqueViewSet.as_view({'get': 'fiche_technique', 'post': 'fiche_technique', 'put': 'fiche_technique'}), name='point-fiche'),
    
    path('interventions/<uuid:pk>/status/', InterventionViewSet.as_view({'put': 'changer_status'}), name='intervention-status'),
    path('interventions/<uuid:pk>/commit/', InterventionViewSet.as_view({'post': 'commit'}), name='intervention-commit'),
    path('interventions/<uuid:pk>/commits/', InterventionViewSet.as_view({'get': 'historique_commits'}), name='intervention-commits'),
    path('interventions/planning/', InterventionViewSet.as_view({'get': 'planning_technicien'}), name='intervention-planning'),
    path('interventions/dashboard/', InterventionViewSet.as_view({'get': 'tableau_bord'}), name='intervention-dashboard'),
    
    path('coupures/<uuid:pk>/status/', CoupureViewSet.as_view({'put': 'changer_status'}), name='coupure-status'),
    path('coupures/actives/', CoupureViewSet.as_view({'get': 'actives'}), name='coupures-actives'),
    path('coupures/carte/', CoupureViewSet.as_view({'get': 'carte'}), name='coupures-carte-alt'),
    
    path('notifications/<uuid:pk>/lue/', NotificationViewSet.as_view({'put': 'marquer_lue'}), name='notification-lue'),
    path('notifications/toutes-lues/', NotificationViewSet.as_view({'put': 'marquer_toutes_lues'}), name='notifications-toutes-lues'),
    path('notifications/non-lues/', NotificationViewSet.as_view({'get': 'non_lues'}), name='notifications-non-lues'),
    path('notifications/resume/', NotificationViewSet.as_view({'get': 'resume'}), name='notifications-resume'),
    
    path('clients/<uuid:pk>/liaisons/', ClientViewSet.as_view({'get': 'liaisons'}), name='client-liaisons'),
    path('clients/statistiques/', ClientViewSet.as_view({'get': 'statistiques'}), name='client-stats'),
    
    path('parametres/par-type/', ParametreApplicationViewSet.as_view({'get': 'par_type'}), name='parametres-par-type'),
]