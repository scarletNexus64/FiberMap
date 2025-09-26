from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from ..models import Liaison, PointDynamique, Coupure
from ..serializers import LiaisonCarteSerializer, CoupureCarteSerializer, PointDynamiqueListSerializer
from ..services import NavigationService, StatistiquesService, SegmentService

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liaisons_carte(request):
    """Récupère toutes les liaisons pour l'affichage sur la carte"""
    # Filtres optionnels
    client_id = request.query_params.get('client_id')
    type_liaison = request.query_params.get('type_liaison')
    status_filter = request.query_params.get('status')
    
    queryset = Liaison.objects.select_related('client', 'type_liaison').prefetch_related(
        'points_dynamiques', 'segments'
    )
    
    if client_id:
        queryset = queryset.filter(client_id=client_id)
    
    if type_liaison:
        queryset = queryset.filter(type_liaison__type=type_liaison)
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    serializer = LiaisonCarteSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liaisons_bounds(request):
    """Calcule les bounds (limites géographiques) de toutes les liaisons"""
    liaisons = Liaison.objects.all()
    
    if not liaisons.exists():
        return Response({
            'bounds': None,
            'center': None
        })
    
    # Calculer les bounds
    lats = []
    lngs = []
    
    for liaison in liaisons:
        lats.extend([float(liaison.point_central_lat), float(liaison.point_client_lat)])
        lngs.extend([float(liaison.point_central_lng), float(liaison.point_client_lng)])
        
        # Ajouter les points dynamiques
        for point in liaison.points_dynamiques.all():
            lats.append(float(point.latitude))
            lngs.append(float(point.longitude))
    
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    
    return Response({
        'bounds': {
            'southwest': {'lat': min_lat, 'lng': min_lng},
            'northeast': {'lat': max_lat, 'lng': max_lng}
        },
        'center': {'lat': center_lat, 'lng': center_lng}
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def points_dynamiques_carte(request):
    """Récupère les points dynamiques pour la carte"""
    # Filtres
    type_point = request.query_params.get('type_point')
    liaison_id = request.query_params.get('liaison_id')
    
    queryset = PointDynamique.objects.select_related('liaison')
    
    if type_point:
        queryset = queryset.filter(type_point=type_point)
    
    if liaison_id:
        queryset = queryset.filter(liaison_id=liaison_id)
    
    serializer = PointDynamiqueListSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coupures_carte(request):
    """Récupère les coupures actives pour la carte"""
    coupures = Coupure.objects.exclude(status='reparee').select_related(
        'liaison', 'liaison__client'
    )
    
    serializer = CoupureCarteSerializer(coupures, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trace_liaison(request, liaison_id):
    """Récupère le tracé détaillé d'une liaison spécifique"""
    try:
        liaison = Liaison.objects.get(id=liaison_id)
    except Liaison.DoesNotExist:
        return Response(
            {'error': 'Liaison non trouvée'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Construire le tracé complet
    points = liaison.points_dynamiques.order_by('ordre')
    segments = liaison.segments.order_by('point_depart__ordre')
    
    trace_complet = []
    
    # Point central
    trace_complet.append({
        'lat': float(liaison.point_central_lat),
        'lng': float(liaison.point_central_lng),
        'type': 'central',
        'nom': 'Central',
        'info': {
            'liaison': liaison.nom_liaison,
            'client': liaison.client.name
        }
    })
    
    # Points dynamiques avec segments
    for point in points:
        # Segment vers ce point
        segment = segments.filter(point_arrivee=point).first()
        if segment and segment.trace_coords:
            for i, coord in enumerate(segment.trace_coords):
                trace_complet.append({
                    'lat': coord[0],
                    'lng': coord[1],
                    'type': 'trace_segment',
                    'segment_id': str(segment.id),
                    'trace_index': i
                })
        
        # Point dynamique
        trace_complet.append({
            'lat': float(point.latitude),
            'lng': float(point.longitude),
            'type': point.type_point,
            'nom': point.nom,
            'id': str(point.id),
            'ordre': point.ordre,
            'distance_depuis_central': point.distance_depuis_central,
            'info': {
                'description': point.description,
                'commentaire': point.commentaire_technicien
            }
        })
    
    # Point client
    trace_complet.append({
        'lat': float(liaison.point_client_lat),
        'lng': float(liaison.point_client_lng),
        'type': 'client',
        'nom': f'Client - {liaison.client.name}',
        'info': {
            'adresse': liaison.client.address,
            'type_client': liaison.client.type_client
        }
    })
    
    return Response({
        'liaison': LiaisonCarteSerializer(liaison).data,
        'trace': trace_complet,
        'statistiques': {
            'nb_points': points.count(),
            'nb_segments': segments.count(),
            'distance_totale_km': liaison.distance_totale,
            'distance_gps_directe_km': round(
                SegmentService.calculer_distance_gps(
                    float(liaison.point_central_lat),
                    float(liaison.point_central_lng),
                    float(liaison.point_client_lat),
                    float(liaison.point_client_lng)
                ), 3
            )
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def navigation_vers_point(request):
    """Calcule la navigation vers un point dynamique"""
    point_id = request.data.get('point_id')
    position_actuelle = request.data.get('position_actuelle')
    
    if not point_id or not position_actuelle:
        return Response(
            {'error': 'point_id et position_actuelle requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validation position
    if not all(k in position_actuelle for k in ['latitude', 'longitude']):
        return Response(
            {'error': 'position_actuelle doit contenir latitude et longitude'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        point = PointDynamique.objects.get(id=point_id)
    except PointDynamique.DoesNotExist:
        return Response(
            {'error': 'Point dynamique non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculer l'itinéraire
    itineraire = NavigationService.calculer_itineraire_vers_point(point, position_actuelle)
    
    return Response(itineraire)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mettre_a_jour_position(request):
    """Met à jour la position du technicien"""
    position = request.data.get('position')
    
    if not position or not all(k in position for k in ['latitude', 'longitude']):
        return Response(
            {'error': 'Position avec latitude et longitude requise'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Stocker la position (dans le cache ou session)
    request.session['position_technicien'] = position
    
    # Optionnel: calculer les points proches
    points_proches = []
    if request.data.get('calculer_points_proches', False):
        rayon_km = float(request.data.get('rayon_km', 1.0))
        
        # Simple approximation pour trouver les points proches
        # Dans un vrai projet, utiliser PostGIS ou une recherche géospatiale
        tous_points = PointDynamique.objects.all()
        
        for point in tous_points:
            distance = NavigationService.calculer_distance_gps(
                position['latitude'], position['longitude'],
                float(point.latitude), float(point.longitude)
            )
            
            if distance <= rayon_km:
                points_proches.append({
                    'point': PointDynamiqueListSerializer(point).data,
                    'distance_km': round(distance, 3)
                })
        
        # Trier par distance
        points_proches.sort(key=lambda x: x['distance_km'])
    
    return Response({
        'message': 'Position mise à jour',
        'position_enregistree': position,
        'points_proches': points_proches[:10] if points_proches else []
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_carte(request):
    """Statistiques pour le dashboard de la carte"""
    stats = StatistiquesService.calculer_statistiques_globales()
    
    # Ajout de statistiques spécifiques à la carte
    stats['carte'] = {
        'nb_liaisons_avec_coupures': Liaison.objects.filter(
            coupures__status__in=['detectee', 'localisee', 'en_cours']
        ).distinct().count(),
        'nb_points_sans_photos': PointDynamique.objects.filter(
            photos__isnull=True
        ).count(),
        'couverture_geographique': {
            'nb_zones_actives': stats['liaisons']['actives'],  # Approximation
            'distance_totale_reseau_km': stats['liaisons']['distance_totale_km']
        }
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recherche_geographique(request):
    """Recherche géographique dans une zone"""
    # Paramètres de la zone
    lat_min = request.query_params.get('lat_min')
    lat_max = request.query_params.get('lat_max')
    lng_min = request.query_params.get('lng_min')
    lng_max = request.query_params.get('lng_max')
    
    if not all([lat_min, lat_max, lng_min, lng_max]):
        return Response(
            {'error': 'Paramètres de zone requis: lat_min, lat_max, lng_min, lng_max'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        lat_min, lat_max = float(lat_min), float(lat_max)
        lng_min, lng_max = float(lng_min), float(lng_max)
    except ValueError:
        return Response(
            {'error': 'Coordonnées invalides'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rechercher les éléments dans la zone
    
    # Liaisons (points centraux et clients dans la zone)
    liaisons = Liaison.objects.filter(
        Q(point_central_lat__range=(lat_min, lat_max), 
          point_central_lng__range=(lng_min, lng_max)) |
        Q(point_client_lat__range=(lat_min, lat_max), 
          point_client_lng__range=(lng_min, lng_max))
    )
    
    # Points dynamiques dans la zone
    points = PointDynamique.objects.filter(
        latitude__range=(lat_min, lat_max),
        longitude__range=(lng_min, lng_max)
    )
    
    # Coupures dans la zone
    coupures = Coupure.objects.filter(
        point_estime_lat__range=(lat_min, lat_max),
        point_estime_lng__range=(lng_min, lng_max)
    ).exclude(status='reparee')
    
    return Response({
        'zone': {
            'lat_min': lat_min, 'lat_max': lat_max,
            'lng_min': lng_min, 'lng_max': lng_max
        },
        'resultats': {
            'liaisons': LiaisonCarteSerializer(liaisons, many=True).data,
            'points_dynamiques': PointDynamiqueListSerializer(points, many=True).data,
            'coupures': CoupureCarteSerializer(coupures, many=True).data
        },
        'statistiques': {
            'nb_liaisons': liaisons.count(),
            'nb_points_dynamiques': points.count(),
            'nb_coupures_actives': coupures.count()
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_itineraire_multiple(request):
    """Calcule un itinéraire passant par plusieurs points"""
    points_ids = request.data.get('points_ids', [])
    position_depart = request.data.get('position_depart')
    optimiser_ordre = request.data.get('optimiser_ordre', False)
    
    if not points_ids or not position_depart:
        return Response(
            {'error': 'points_ids et position_depart requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Récupérer les points
    points = PointDynamique.objects.filter(id__in=points_ids)
    if points.count() != len(points_ids):
        return Response(
            {'error': 'Certains points sont introuvables'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculer les distances vers chaque point
    etapes = []
    position_courante = position_depart
    
    points_liste = list(points)
    
    # Si optimisation demandée, réorganiser par distance (simple heuristique)
    if optimiser_ordre:
        points_restants = points_liste.copy()
        points_optimises = []
        
        while points_restants:
            # Trouver le point le plus proche
            distances = []
            for point in points_restants:
                distance = NavigationService.calculer_distance_gps(
                    position_courante['latitude'], position_courante['longitude'],
                    float(point.latitude), float(point.longitude)
                )
                distances.append((point, distance))
            
            # Prendre le plus proche
            point_suivant, distance_min = min(distances, key=lambda x: x[1])
            points_optimises.append(point_suivant)
            points_restants.remove(point_suivant)
            
            # Mettre à jour position courante
            position_courante = {
                'latitude': float(point_suivant.latitude),
                'longitude': float(point_suivant.longitude)
            }
        
        points_liste = points_optimises
    
    # Calculer l'itinéraire final
    position_courante = position_depart
    distance_totale = 0
    
    for i, point in enumerate(points_liste):
        itineraire_etape = NavigationService.calculer_itineraire_vers_point(
            point, position_courante
        )
        
        etapes.append({
            'etape': i + 1,
            'point': PointDynamiqueListSerializer(point).data,
            'navigation': itineraire_etape,
            'distance_cumulative_km': distance_totale + itineraire_etape['distance_directe_km']
        })
        
        distance_totale += itineraire_etape['distance_directe_km']
        
        # Mettre à jour position pour prochaine étape
        position_courante = {
            'latitude': float(point.latitude),
            'longitude': float(point.longitude)
        }
    
    return Response({
        'itineraire_multiple': {
            'position_depart': position_depart,
            'optimise': optimiser_ordre,
            'nb_etapes': len(points_liste),
            'distance_totale_km': round(distance_totale, 3),
            'etapes': etapes
        }
    })