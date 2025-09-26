"""
Services pour la logique métier FiberMap
"""
import math
from typing import Dict, List, Tuple, Optional
from django.db.models import Sum, Q
from geopy.distance import geodesic
from .models import (
    Liaison, PointDynamique, Segment, MesureOTDR, Coupure,
    Client, FAT, Intervention, Notification
)

class SegmentService:
    """Service pour gérer les segments de liaison"""

    @staticmethod
    def calculer_distance_gps(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcule la distance GPS entre deux points en km"""
        return geodesic((lat1, lng1), (lat2, lng2)).kilometers

    @staticmethod
    def creer_segment_auto(point_depart: PointDynamique, point_arrivee: PointDynamique, 
                          distance_cable: float = None) -> Segment:
        """Crée automatiquement un segment entre deux points"""
        distance_gps = SegmentService.calculer_distance_gps(
            float(point_depart.latitude), float(point_depart.longitude),
            float(point_arrivee.latitude), float(point_arrivee.longitude)
        )
        
        # Si distance_cable n'est pas fournie, utiliser la distance GPS + 20%
        if distance_cable is None:
            distance_cable = distance_gps * 1.2
        
        segment = Segment.objects.create(
            liaison=point_depart.liaison,
            point_depart=point_depart,
            point_arrivee=point_arrivee,
            distance_gps=distance_gps,
            distance_cable=distance_cable,
            trace_coords=[]
        )
        
        # Recalculer la distance totale de la liaison
        point_depart.liaison.calculer_distance_totale()
        
        return segment

    @staticmethod
    def recalculer_distances_cumulees(liaison: Liaison):
        """Recalcule les distances cumulées de tous les points d'une liaison"""
        points = liaison.points_dynamiques.order_by('ordre')
        distance_cumulee = 0.0
        
        for i, point in enumerate(points):
            point.distance_depuis_central = distance_cumulee
            point.save()
            
            # Trouver le segment vers le point suivant
            if i < len(points) - 1:
                try:
                    segment = Segment.objects.get(
                        point_depart=point,
                        point_arrivee=points[i + 1]
                    )
                    distance_cumulee += segment.distance_cable
                except Segment.DoesNotExist:
                    pass

class CoupureService:
    """Service pour analyser et localiser les coupures"""

    @staticmethod
    def analyser_coupure(mesure_otdr: MesureOTDR) -> Dict:
        """Analyse une mesure OTDR et localise la coupure"""
        liaison = mesure_otdr.liaison
        distance_coupure = mesure_otdr.distance_coupure
        
        # Ajuster la distance selon la direction et la position
        distance_absolue = CoupureService._calculer_distance_absolue(
            mesure_otdr, distance_coupure
        )
        
        # Trouver le segment touché
        segment_info = CoupureService._trouver_segment_touche(liaison, distance_absolue)
        
        # Calculer les coordonnées estimées
        coords_estimees = CoupureService._calculer_coordonnees_coupure(segment_info, distance_absolue)
        
        # Trouver le point dynamique le plus proche
        point_proche = CoupureService._trouver_point_proche(liaison, distance_absolue)
        
        return {
            'distance_absolue': distance_absolue,
            'segment_touche': segment_info['segment'] if segment_info else None,
            'distance_sur_segment': segment_info['distance_sur_segment'] if segment_info else None,
            'coordonnees_estimees': coords_estimees,
            'point_dynamique_proche': point_proche,
            'precision_estimation': CoupureService._calculer_precision(liaison, distance_absolue)
        }

    @staticmethod
    def _calculer_distance_absolue(mesure_otdr: MesureOTDR, distance_mesure: float) -> float:
        """Calcule la distance absolue depuis le central en tenant compte de la position et direction"""
        if mesure_otdr.position_technicien == 'central':
            if mesure_otdr.direction_analyse == 'vers_client':
                return distance_mesure
            else:
                # Mesure depuis central vers central (impossible normalement)
                return distance_mesure
                
        elif mesure_otdr.position_technicien == 'client':
            if mesure_otdr.direction_analyse == 'vers_central':
                # Distance totale - distance mesurée
                return mesure_otdr.liaison.distance_totale - distance_mesure
            else:
                # Mesure depuis client vers client
                return mesure_otdr.liaison.distance_totale - distance_mesure
                
        elif mesure_otdr.position_technicien == 'intermediaire' and mesure_otdr.point_mesure:
            point_position = mesure_otdr.point_mesure.distance_depuis_central
            if mesure_otdr.direction_analyse == 'vers_central':
                return point_position - distance_mesure
            else:
                return point_position + distance_mesure
                
        return distance_mesure

    @staticmethod
    def _trouver_segment_touche(liaison: Liaison, distance_absolue: float) -> Optional[Dict]:
        """Trouve le segment où se situe la coupure"""
        segments = liaison.segments.order_by('point_depart__ordre')
        distance_parcourue = 0.0
        
        for segment in segments:
            distance_fin_segment = distance_parcourue + segment.distance_cable
            
            if distance_parcourue <= distance_absolue <= distance_fin_segment:
                return {
                    'segment': segment,
                    'distance_sur_segment': distance_absolue - distance_parcourue,
                    'distance_debut': distance_parcourue,
                    'distance_fin': distance_fin_segment
                }
            
            distance_parcourue = distance_fin_segment
        
        return None

    @staticmethod
    def _calculer_coordonnees_coupure(segment_info: Optional[Dict], distance_absolue: float) -> Optional[Dict]:
        """Calcule les coordonnées GPS estimées de la coupure"""
        if not segment_info:
            return None
            
        segment = segment_info['segment']
        ratio = segment_info['distance_sur_segment'] / segment.distance_cable
        
        # Interpolation linéaire entre les deux points
        lat_debut = float(segment.point_depart.latitude)
        lng_debut = float(segment.point_depart.longitude)
        lat_fin = float(segment.point_arrivee.latitude)
        lng_fin = float(segment.point_arrivee.longitude)
        
        lat_estimee = lat_debut + (lat_fin - lat_debut) * ratio
        lng_estimee = lng_debut + (lng_fin - lng_debut) * ratio
        
        return {
            'latitude': lat_estimee,
            'longitude': lng_estimee,
            'ratio_segment': ratio
        }

    @staticmethod
    def _trouver_point_proche(liaison: Liaison, distance_absolue: float) -> Optional[PointDynamique]:
        """Trouve le point dynamique le plus proche de la coupure"""
        points = liaison.points_dynamiques.all()
        point_proche = None
        distance_min = float('inf')
        
        for point in points:
            distance_point = abs(point.distance_depuis_central - distance_absolue)
            if distance_point < distance_min:
                distance_min = distance_point
                point_proche = point
        
        return point_proche

    @staticmethod
    def _calculer_precision(liaison: Liaison, distance_absolue: float) -> str:
        """Calcule la précision de l'estimation"""
        # Logique pour estimer la précision basée sur divers facteurs
        if distance_absolue < 1.0:  # Moins de 1km
            return 'haute'
        elif distance_absolue < 5.0:  # Moins de 5km
            return 'moyenne'
        else:
            return 'faible'

    @staticmethod
    def creer_coupure(mesure_otdr: MesureOTDR) -> Coupure:
        """Crée une coupure basée sur une mesure OTDR"""
        analyse = CoupureService.analyser_coupure(mesure_otdr)
        
        coupure = Coupure.objects.create(
            liaison=mesure_otdr.liaison,
            mesure_otdr=mesure_otdr,
            segment_touche=analyse['segment_touche'],
            distance_sur_segment=analyse['distance_sur_segment'],
            point_dynamique_proche=analyse['point_dynamique_proche']
        )
        
        # Ajouter les coordonnées si disponibles
        if analyse['coordonnees_estimees']:
            coupure.point_estime_lat = analyse['coordonnees_estimees']['latitude']
            coupure.point_estime_lng = analyse['coordonnees_estimees']['longitude']
            coupure.save()
        
        return coupure

class NavigationService:
    """Service pour la navigation et le guidage GPS"""

    @staticmethod
    def calculer_itineraire_vers_point(point_dynamique: PointDynamique, 
                                     position_actuelle: Dict[str, float]) -> Dict:
        """Calcule l'itinéraire vers un point dynamique"""
        lat_actuelle = position_actuelle['latitude']
        lng_actuelle = position_actuelle['longitude']
        
        lat_cible = float(point_dynamique.latitude)
        lng_cible = float(point_dynamique.longitude)
        
        # Distance directe
        distance_directe = geodesic((lat_actuelle, lng_actuelle), (lat_cible, lng_cible)).kilometers
        
        # Calculer l'azimut (direction)
        azimut = NavigationService._calculer_azimut(
            lat_actuelle, lng_actuelle, lat_cible, lng_cible
        )
        
        return {
            'point_cible': {
                'id': point_dynamique.id,
                'nom': point_dynamique.nom,
                'type': point_dynamique.type_point,
                'latitude': lat_cible,
                'longitude': lng_cible
            },
            'distance_directe_km': round(distance_directe, 3),
            'distance_directe_m': round(distance_directe * 1000),
            'azimut_degres': round(azimut, 1),
            'direction_cardinale': NavigationService._azimut_vers_direction(azimut),
            'instructions': NavigationService._generer_instructions(distance_directe, azimut)
        }

    @staticmethod
    def _calculer_azimut(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcule l'azimut entre deux points"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng_rad = math.radians(lng2 - lng1)
        
        y = math.sin(delta_lng_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng_rad)
        
        azimut_rad = math.atan2(y, x)
        azimut_deg = math.degrees(azimut_rad)
        
        return (azimut_deg + 360) % 360

    @staticmethod
    def _azimut_vers_direction(azimut: float) -> str:
        """Convertit un azimut en direction cardinale"""
        directions = [
            "Nord", "Nord-Est", "Est", "Sud-Est",
            "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"
        ]
        index = round(azimut / 45) % 8
        return directions[index]

    @staticmethod
    def _generer_instructions(distance: float, azimut: float) -> List[str]:
        """Génère des instructions de navigation"""
        direction = NavigationService._azimut_vers_direction(azimut)
        
        if distance < 0.1:  # Moins de 100m
            return [f"Vous êtes arrivé à destination (moins de {round(distance * 1000)}m)"]
        elif distance < 1.0:  # Moins de 1km
            return [f"Dirigez-vous vers le {direction} sur {round(distance * 1000)}m"]
        else:
            return [f"Dirigez-vous vers le {direction} sur {round(distance, 1)}km"]

    @staticmethod
    def calculer_distance_gps(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcule la distance GPS entre deux points en km"""
        return geodesic((lat1, lng1), (lat2, lng2)).kilometers

class StatistiquesService:
    """Service pour calculer les statistiques"""

    @staticmethod
    def calculer_statistiques_globales() -> Dict:
        """Calcule les statistiques globales de l'application"""
        return {
            'liaisons': StatistiquesService._stats_liaisons(),
            'points_dynamiques': StatistiquesService._stats_points(),
            'interventions': StatistiquesService._stats_interventions(),
            'coupures': StatistiquesService._stats_coupures(),
            'clients': StatistiquesService._stats_clients()
        }

    @staticmethod
    def _stats_liaisons() -> Dict:
        """Statistiques des liaisons"""
        total = Liaison.objects.count()
        actives = Liaison.objects.filter(status='active').count()
        en_panne = Liaison.objects.filter(status='en_panne').count()
        en_cours = Liaison.objects.filter(status='en_cours').count()
        
        return {
            'total': total,
            'actives': actives,
            'en_panne': en_panne,
            'en_cours_reparation': en_cours,
            'distance_totale_km': Liaison.objects.aggregate(
                total=Sum('distance_totale')
            )['total'] or 0
        }

    @staticmethod
    def _stats_points() -> Dict:
        """Statistiques des points dynamiques"""
        total = PointDynamique.objects.count()
        
        stats_par_type = {}
        for type_code, type_label in PointDynamique.TYPE_CHOICES:
            count = PointDynamique.objects.filter(type_point=type_code).count()
            stats_par_type[type_code] = {
                'label': type_label,
                'count': count
            }
        
        return {
            'total': total,
            'par_type': stats_par_type
        }

    @staticmethod
    def _stats_interventions() -> Dict:
        """Statistiques des interventions"""
        total = Intervention.objects.count()
        en_cours = Intervention.objects.filter(status='en_cours').count()
        terminees = Intervention.objects.filter(status='terminee').count()
        planifiees = Intervention.objects.filter(status='planifiee').count()
        
        return {
            'total': total,
            'en_cours': en_cours,
            'terminees': terminees,
            'planifiees': planifiees
        }

    @staticmethod
    def _stats_coupures() -> Dict:
        """Statistiques des coupures"""
        total = Coupure.objects.count()
        detectees = Coupure.objects.filter(status='detectee').count()
        en_cours = Coupure.objects.filter(status='en_cours').count()
        reparees = Coupure.objects.filter(status='reparee').count()
        
        return {
            'total': total,
            'detectees': detectees,
            'en_cours_reparation': en_cours,
            'reparees': reparees
        }

    @staticmethod
    def _stats_clients() -> Dict:
        """Statistiques des clients"""
        total = Client.objects.count()
        ls = Client.objects.filter(type_client='LS').count()
        ftth = Client.objects.filter(type_client='FTTH').count()
        
        return {
            'total': total,
            'clients_ls': ls,
            'clients_ftth': ftth
        }

class LiaisonService:
    """Service pour la gestion des liaisons"""

    @staticmethod
    def creer_liaison_complete(liaison_data: Dict, points_data: List[Dict]) -> Liaison:
        """Crée une liaison avec tous ses points dynamiques"""
        # Créer la liaison
        liaison = Liaison.objects.create(**liaison_data)
        
        # Créer les points dynamiques
        points_crees = []
        for i, point_data in enumerate(points_data):
            point_data['liaison'] = liaison
            point_data['ordre'] = i
            point = PointDynamique.objects.create(**point_data)
            points_crees.append(point)
        
        # Créer les segments automatiquement
        for i in range(len(points_crees) - 1):
            SegmentService.creer_segment_auto(points_crees[i], points_crees[i + 1])
        
        return liaison

    @staticmethod
    def ajouter_point_dynamique(liaison: Liaison, point_data: Dict, position: int = None) -> PointDynamique:
        """Ajoute un point dynamique à une liaison existante"""
        if position is None:
            position = liaison.points_dynamiques.count()
        
        # Décaler les points suivants
        points_suivants = liaison.points_dynamiques.filter(ordre__gte=position)
        for point in points_suivants:
            point.ordre += 1
            point.save()
        
        # Créer le nouveau point
        point_data['liaison'] = liaison
        point_data['ordre'] = position
        nouveau_point = PointDynamique.objects.create(**point_data)
        
        # Recréer les segments affectés
        LiaisonService._recreer_segments_autour_point(nouveau_point)
        
        # Recalculer les distances
        SegmentService.recalculer_distances_cumulees(liaison)
        
        return nouveau_point

    @staticmethod
    def _recreer_segments_autour_point(point: PointDynamique):
        """Recrée les segments autour d'un point inséré"""
        liaison = point.liaison
        points = list(liaison.points_dynamiques.order_by('ordre'))
        index = points.index(point)
        
        # Supprimer l'ancien segment si il existait
        if index > 0 and index < len(points) - 1:
            try:
                ancien_segment = Segment.objects.get(
                    point_depart=points[index - 1],
                    point_arrivee=points[index + 1]
                )
                ancien_segment.delete()
            except Segment.DoesNotExist:
                pass
        
        # Créer nouveaux segments
        if index > 0:
            SegmentService.creer_segment_auto(points[index - 1], point)
        if index < len(points) - 1:
            SegmentService.creer_segment_auto(point, points[index + 1])

class NotificationService:
    """Service pour gérer les notifications"""

    @staticmethod
    def notifier_coupure_detectee(coupure: Coupure):
        """Notifie les superviseurs d'une nouvelle coupure"""
        from .models import User
        
        superviseurs = User.objects.filter(role='superviseur')
        
        for superviseur in superviseurs:
            Notification.objects.create(
                destinataire=superviseur,
                type_notification='coupure',
                priorite='haute',
                titre=f"Coupure détectée - {coupure.liaison.nom_liaison}",
                message=f"Une coupure a été détectée sur la liaison {coupure.liaison.nom_liaison} "
                       f"du client {coupure.liaison.client.name}. "
                       f"Point proche estimé: {coupure.point_dynamique_proche.nom if coupure.point_dynamique_proche else 'Non déterminé'}",
                liaison_concernee=coupure.liaison,
                coupure_concernee=coupure
            )

    @staticmethod
    def notifier_intervention_planifiee(intervention: Intervention):
        """Notifie une intervention planifiée"""
        Notification.objects.create(
            destinataire=intervention.technicien_principal,
            type_notification='intervention',
            priorite='normale',
            titre=f"Intervention planifiée - {intervention.type_intervention}",
            message=f"Une intervention {intervention.type_intervention} a été planifiée "
                   f"pour le {intervention.date_planifiee.strftime('%d/%m/%Y à %H:%M')}",
            intervention_concernee=intervention,
            liaison_concernee=intervention.liaison
        )