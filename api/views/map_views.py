from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from ..models import Liaison, PointDynamique, Coupure
from ..serializers import LiaisonMapSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liaisons_carte(request):
    """Données des liaisons optimisées pour l'affichage sur carte"""
    queryset = Liaison.objects.select_related('client', 'type_liaison').all()
    
    # Filtrage géographique par bounding box
    lat_min = request.query_params.get('lat_min')
    lat_max = request.query_params.get('lat_max')
    lng_min = request.query_params.get('lng_min')
    lng_max = request.query_params.get('lng_max')
    
    if all([lat_min, lat_max, lng_min, lng_max]):
        queryset = queryset.filter(
            Q(point_central_lat__gte=lat_min, point_central_lat__lte=lat_max,
              point_central_lng__gte=lng_min, point_central_lng__lte=lng_max) |
            Q(point_client_lat__gte=lat_min, point_client_lat__lte=lat_max,
              point_client_lng__gte=lng_min, point_client_lng__lte=lng_max)
        )
    
    # Filtrage par statut
    status = request.query_params.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    # Format optimisé pour Flutter Map
    liaisons_carte = []
    for liaison in queryset:
        liaisons_carte.append({
            'id': str(liaison.id),
            'nom': liaison.nom_liaison,
            'client': liaison.client.name,
            'type': liaison.type_liaison.type,
            'status': liaison.status,
            'central': {
                'lat': float(liaison.point_central_lat),
                'lng': float(liaison.point_central_lng)
            },
            'client_point': {
                'lat': float(liaison.point_client_lat),
                'lng': float(liaison.point_client_lng)
            },
            'distance': liaison.distance_totale
        })
    
    return Response(liaisons_carte)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liaisons_bounds(request):
    """Liaisons dans une zone géographique spécifique"""
    lat_min = request.query_params.get('lat_min')
    lat_max = request.query_params.get('lat_max')
    lng_min = request.query_params.get('lng_min')
    lng_max = request.query_params.get('lng_max')
    
    if not all([lat_min, lat_max, lng_min, lng_max]):
        return Response({'error': 'Paramètres de géolocalisation requis'}, status=400)
    
    liaisons = Liaison.objects.filter(
        Q(point_central_lat__gte=lat_min, point_central_lat__lte=lat_max,
          point_central_lng__gte=lng_min, point_central_lng__lte=lng_max) |
        Q(point_client_lat__gte=lat_min, point_client_lat__lte=lat_max,
          point_client_lng__gte=lng_min, point_client_lng__lte=lng_max)
    ).select_related('client', 'type_liaison')
    
    serializer = LiaisonMapSerializer(liaisons, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def points_dynamiques_carte(request):
    """Points dynamiques pour affichage sur carte"""
    queryset = PointDynamique.objects.select_related('liaison', 'liaison__client').all()
    
    # Filtrage géographique
    lat_min = request.query_params.get('lat_min')
    lat_max = request.query_params.get('lat_max')
    lng_min = request.query_params.get('lng_min')
    lng_max = request.query_params.get('lng_max')
    
    if all([lat_min, lat_max, lng_min, lng_max]):
        queryset = queryset.filter(
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max
        )
    
    # Filtrage par type de point
    type_point = request.query_params.get('type_point')
    if type_point:
        queryset = queryset.filter(type_point=type_point)
    
    # Filtrage par liaison
    liaison_id = request.query_params.get('liaison_id')
    if liaison_id:
        queryset = queryset.filter(liaison_id=liaison_id)
    
    points_carte = []
    for point in queryset:
        points_carte.append({
            'id': str(point.id),
            'nom': point.nom,
            'type': point.type_point,
            'lat': float(point.latitude),
            'lng': float(point.longitude),
            'distance_central': point.distance_depuis_central,
            'liaison': {
                'id': str(point.liaison.id),
                'nom': point.liaison.nom_liaison,
                'client': point.liaison.client.name
            },
            'presence_splitter': point.presence_splitter,
            'ratio_splitter': point.ratio_splitter,
            'description': point.description[:100] + '...' if len(point.description) > 100 else point.description
        })
    
    return Response(points_carte)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coupures_carte(request):
    """Coupures actives pour affichage sur carte (déjà implémenté dans diagnostic_views)"""
    # Cette vue est un alias pour la vue coupures.carte dans diagnostic_views
    from .diagnostic_views import CoupureViewSet
    
    viewset = CoupureViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    return viewset.carte(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trace_liaison(request, liaison_id):
    """Tracé complet d'une liaison pour affichage sur carte"""
    try:
        liaison = Liaison.objects.select_related('client', 'type_liaison').get(id=liaison_id)
    except Liaison.DoesNotExist:
        return Response({'error': 'Liaison introuvable'}, status=404)
    
    # Points du tracé dans l'ordre
    trace_points = []
    
    # Point central
    trace_points.append({
        'lat': float(liaison.point_central_lat),
        'lng': float(liaison.point_central_lng),
        'type': 'central',
        'nom': 'Point Central',
        'distance': 0,
        'ordre': 0
    })
    
    # Points dynamiques dans l'ordre de distance
    points_dynamiques = liaison.points_dynamiques.all().order_by('distance_depuis_central')
    for i, point in enumerate(points_dynamiques):
        trace_points.append({
            'lat': float(point.latitude),
            'lng': float(point.longitude),
            'type': point.type_point,
            'nom': point.nom,
            'distance': point.distance_depuis_central,
            'ordre': i + 1,
            'id': str(point.id),
            'presence_splitter': point.presence_splitter,
            'ratio_splitter': point.ratio_splitter,
            'description': point.description
        })
    
    # Point client
    trace_points.append({
        'lat': float(liaison.point_client_lat),
        'lng': float(liaison.point_client_lng),
        'type': 'client',
        'nom': f'Client - {liaison.client.name}',
        'distance': liaison.distance_totale,
        'ordre': len(points_dynamiques) + 1
    })
    
    return Response({
        'liaison': {
            'id': str(liaison.id),
            'nom': liaison.nom_liaison,
            'client': liaison.client.name,
            'type': liaison.type_liaison.type,
            'status': liaison.status,
            'distance_totale': liaison.distance_totale
        },
        'trace': trace_points
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def navigation_vers_point(request):
    """Calculer l'itinéraire vers un point spécifique"""
    point_id = request.data.get('point_id')
    position_actuelle = request.data.get('position_actuelle')  # {lat, lng}
    
    if not point_id or not position_actuelle:
        return Response({'error': 'point_id et position_actuelle requis'}, status=400)
    
    try:
        # Peut être un PointDynamique ou une Coupure
        point = None
        point_type = request.data.get('point_type', 'point_dynamique')
        
        if point_type == 'point_dynamique':
            point = PointDynamique.objects.get(id=point_id)
            destination = {
                'lat': float(point.latitude),
                'lng': float(point.longitude),
                'nom': point.nom,
                'type': point.type_point
            }
        elif point_type == 'coupure':
            coupure = Coupure.objects.get(id=point_id)
            destination = {
                'lat': float(coupure.point_estime_lat),
                'lng': float(coupure.point_estime_lng),
                'nom': f'Coupure - {coupure.liaison.nom_liaison}',
                'type': 'coupure'
            }
        else:
            return Response({'error': 'Type de point invalide'}, status=400)
        
    except (PointDynamique.DoesNotExist, Coupure.DoesNotExist):
        return Response({'error': 'Point introuvable'}, status=404)
    
    # Retourner les coordonnées pour la navigation
    # L'application mobile utilisera ces coordonnées avec son service de navigation
    return Response({
        'origine': position_actuelle,
        'destination': destination,
        'distance_estimee': None,  # Calculé côté client
        'instructions': f"Navigation vers {destination['nom']}"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mettre_a_jour_position(request):
    """Mettre à jour la position d'un technicien (pour le tracking)"""
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    
    if not latitude or not longitude:
        return Response({'error': 'Coordonnées GPS requises'}, status=400)
    
    # Mettre à jour la position de l'utilisateur
    # (Vous pourrez étendre ceci avec un modèle Position si besoin)
    user = request.user
    user.location = f"{latitude},{longitude}"
    user.save()
    
    return Response({
        'message': 'Position mise à jour',
        'position': {
            'lat': float(latitude),
            'lng': float(longitude),
            'timestamp': user.updated_at.isoformat()
        }
    })