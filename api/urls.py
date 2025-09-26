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
    LiaisonViewSet, PointDynamiqueViewSet, PhotoPointViewSet, FicheTechniqueViewSet,
    SegmentViewSet, FATViewSet, choix_application
)
from .views.intervention_views import (
    InterventionViewSet, CommitInterventionViewSet
)
from .views.diagnostic_views import (
    MesureOTDRViewSet, CoupureViewSet, detecter_coupure, simuler_analyse_otdr, 
    statistiques_diagnostics
)
from .views.map_views import (
    liaisons_carte, liaisons_bounds, points_dynamiques_carte, coupures_carte,
    trace_liaison, navigation_vers_point, mettre_a_jour_position, statistiques_carte,
    recherche_geographique, calculer_itineraire_multiple
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
router.register(r'segments', SegmentViewSet)
router.register(r'photos-points', PhotoPointViewSet)
router.register(r'fiches-techniques', FicheTechniqueViewSet)
router.register(r'fats', FATViewSet)
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
    path('auth/token/', obtain_auth_token, name='api-token'),
    
    # ===============================
    # Cartographie et navigation
    # ===============================
    path('map/liaisons/', liaisons_carte, name='liaisons-carte'),
    path('map/liaisons/bounds/', liaisons_bounds, name='liaisons-bounds'),
    path('map/points-dynamiques/', points_dynamiques_carte, name='points-dynamiques-carte'),
    path('map/coupures/', coupures_carte, name='coupures-carte'),
    path('map/trace/<uuid:liaison_id>/', trace_liaison, name='trace-liaison'),
    path('map/statistiques/', statistiques_carte, name='statistiques-carte'),
    path('map/recherche-geographique/', recherche_geographique, name='recherche-geographique'),
    
    # Navigation GPS
    path('navigation/point/', navigation_vers_point, name='navigation-point'),
    path('navigation/position/', mettre_a_jour_position, name='position-technicien'),
    path('navigation/itineraire-multiple/', calculer_itineraire_multiple, name='itineraire-multiple'),
    
    # ===============================
    # Diagnostic OTDR
    # ===============================
    path('diagnostic/detecter-coupure/', detecter_coupure, name='detecter-coupure'),
    path('diagnostic/simuler-analyse/', simuler_analyse_otdr, name='simuler-analyse-otdr'),
    path('diagnostic/statistiques/', statistiques_diagnostics, name='statistiques-diagnostics'),
    
    # ===============================
    # Notifications et administration
    # ===============================
    path('notifications/creer/', creer_notification, name='creer-notification'),
    path('notifications/statistiques/', statistiques_notifications, name='stats-notifications'),
    
    # ===============================
    # Configuration et choix
    # ===============================
    path('choix/', choix_application, name='choix-application'),
    
    # ===============================
    # Routes du router DRF
    # ===============================
    path('', include(router.urls)),
]

# URLs nommées pour faciliter la documentation API
urlpatterns += [
    # ===============================
    # Endpoints spécialisés LIAISONS
    # ===============================
    path('liaisons/<uuid:pk>/trace/', LiaisonViewSet.as_view({'get': 'trace'}), name='liaison-trace'),
    path('liaisons/<uuid:pk>/historique/', LiaisonViewSet.as_view({'get': 'historique'}), name='liaison-historique'),
    path('liaisons/<uuid:pk>/recalculer-distance/', LiaisonViewSet.as_view({'post': 'recalculer_distance'}), name='liaison-recalculer-distance'),
    path('liaisons/recherche-avancee/', LiaisonViewSet.as_view({'get': 'recherche_avancee'}), name='liaison-recherche'),
    
    # ===============================
    # Endpoints spécialisés POINTS DYNAMIQUES
    # ===============================
    path('points-dynamiques/<uuid:pk>/photos/', PointDynamiqueViewSet.as_view({'post': 'ajouter_photo', 'get': 'photos'}), name='point-photos'),
    path('points-dynamiques/<uuid:pk>/fiche-technique/', PointDynamiqueViewSet.as_view({'get': 'fiche_technique', 'post': 'fiche_technique', 'put': 'fiche_technique'}), name='point-fiche'),
    path('points-dynamiques/<uuid:pk>/mettre-a-jour-details/', PointDynamiqueViewSet.as_view({'put': 'mettre_a_jour_details'}), name='point-details'),
    
    # ===============================
    # Endpoints spécialisés SEGMENTS
    # ===============================
    path('segments/<uuid:pk>/mettre-a-jour-trace/', SegmentViewSet.as_view({'put': 'mettre_a_jour_trace'}), name='segment-trace'),
    path('segments/<uuid:pk>/recalculer-distance-gps/', SegmentViewSet.as_view({'post': 'recalculer_distance_gps'}), name='segment-distance-gps'),
    
    # ===============================
    # Endpoints spécialisés FAT
    # ===============================
    path('fats/<uuid:pk>/associer-liaison/', FATViewSet.as_view({'post': 'associer_liaison'}), name='fat-associer-liaison'),
    path('fats/<uuid:pk>/creer-point-dynamique/', FATViewSet.as_view({'post': 'creer_point_dynamique'}), name='fat-creer-point'),
    
    # ===============================
    # Endpoints spécialisés INTERVENTIONS
    # ===============================
    path('interventions/<uuid:pk>/status/', InterventionViewSet.as_view({'put': 'changer_status'}), name='intervention-status'),
    path('interventions/<uuid:pk>/commit/', InterventionViewSet.as_view({'post': 'commit'}), name='intervention-commit'),
    path('interventions/<uuid:pk>/commits/', InterventionViewSet.as_view({'get': 'historique_commits'}), name='intervention-commits'),
    path('interventions/planning/', InterventionViewSet.as_view({'get': 'planning_technicien'}), name='intervention-planning'),
    path('interventions/dashboard/', InterventionViewSet.as_view({'get': 'tableau_bord'}), name='intervention-dashboard'),
    
    # ===============================
    # Endpoints spécialisés MESURES OTDR
    # ===============================
    path('mesures-otdr/<uuid:pk>/analyser-coupure/', MesureOTDRViewSet.as_view({'post': 'analyser_coupure'}), name='mesure-analyser-coupure'),
    
    # ===============================
    # Endpoints spécialisés COUPURES
    # ===============================
    path('coupures/<uuid:pk>/status/', CoupureViewSet.as_view({'put': 'changer_status'}), name='coupure-status'),
    path('coupures/<uuid:pk>/recalculer-position/', CoupureViewSet.as_view({'post': 'recalculer_position'}), name='coupure-recalculer-position'),
    path('coupures/actives/', CoupureViewSet.as_view({'get': 'actives'}), name='coupures-actives'),
    path('coupures/carte/', CoupureViewSet.as_view({'get': 'carte'}), name='coupures-carte-alt'),
    
    # ===============================
    # Endpoints spécialisés NOTIFICATIONS
    # ===============================
    path('notifications/<uuid:pk>/lue/', NotificationViewSet.as_view({'put': 'marquer_lue'}), name='notification-lue'),
    path('notifications/toutes-lues/', NotificationViewSet.as_view({'put': 'marquer_toutes_lues'}), name='notifications-toutes-lues'),
    path('notifications/non-lues/', NotificationViewSet.as_view({'get': 'non_lues'}), name='notifications-non-lues'),
    path('notifications/resume/', NotificationViewSet.as_view({'get': 'resume'}), name='notifications-resume'),
    
    # ===============================
    # Endpoints spécialisés CLIENTS
    # ===============================
    path('clients/<uuid:pk>/liaisons/', ClientViewSet.as_view({'get': 'liaisons'}), name='client-liaisons'),
    path('clients/statistiques/', ClientViewSet.as_view({'get': 'statistiques'}), name='client-stats'),
    
    # ===============================
    # Endpoints spécialisés PARAMÈTRES
    # ===============================
    path('parametres/par-type/', ParametreApplicationViewSet.as_view({'get': 'par_type'}), name='parametres-par-type'),
]