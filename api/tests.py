from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from .models import (
    Client, Liaison, TypeLiaison, PointDynamique, Segment,
    DetailONT, DetailPOPLS, DetailPOPFTTH, DetailChambre, DetailManchon,
    FAT, DetailFDT, PhotoPoint, MesureOTDR, Coupure, Intervention,
    CommitIntervention, FicheTechnique, Notification, ParametreApplication
)
from .services import CoupureService, NavigationService, SegmentService, StatistiquesService

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'technicien'
        }
    
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data, password='testpass123')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'technicien')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        user = User.objects.create_user(**self.user_data)
        expected = f"{self.user_data['username']} ({self.user_data['role']})"
        self.assertEqual(str(user), expected)


class ClientModelTest(TestCase):
    """Tests pour le modèle Client"""
    
    def setUp(self):
        self.client_data = {
            'name': 'Test Client',
            'type_client': 'FTTH',
            'type_organisation': 'particulier',
            'address': '123 Test Street, Test City, 12345',
            'phone': '+33123456789',
            'email': 'client@test.com'
        }
    
    def test_create_client(self):
        client = Client.objects.create(**self.client_data)
        self.assertEqual(client.name, 'Test Client')
        self.assertEqual(client.type_organisation, 'particulier')
    
    def test_client_str_representation(self):
        client = Client.objects.create(**self.client_data)
        expected = f"{self.client_data['name']} ({self.client_data['type_client']})"
        self.assertEqual(str(client), expected)


class LiaisonModelTest(TestCase):
    """Tests pour le modèle Liaison"""
    
    def setUp(self):
        self.client = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison_data = {
            'nom_liaison': 'LIA001',
            'client': self.client,
            'type_liaison': self.type_liaison,
            'point_central_lat': '48.8566',
            'point_central_lng': '2.3522',
            'point_client_lat': '48.8606',
            'point_client_lng': '2.3376',
            'status': 'active'
        }
    
    def test_create_liaison(self):
        liaison = Liaison.objects.create(**self.liaison_data)
        self.assertEqual(liaison.nom_liaison, 'LIA001')
        self.assertEqual(liaison.client, self.client)
        self.assertEqual(liaison.status, 'active')
    
    def test_liaison_str_representation(self):
        liaison = Liaison.objects.create(**self.liaison_data)
        expected = f"LIA001 - {self.client.name}"
        self.assertEqual(str(liaison), expected)


class PointDynamiqueModelTest(TestCase):
    """Tests pour le modèle PointDynamique"""
    
    def setUp(self):
        self.client = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
    
    def test_create_point_dynamique(self):
        point = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point Test',
            type_point='ONT',
            latitude='48.8576',
            longitude='2.3400',
            distance_depuis_central=1.5,
            ordre=1
        )
        self.assertEqual(point.nom, 'Point Test')
        self.assertEqual(point.type_point, 'ONT')
        self.assertEqual(point.distance_depuis_central, 1.5)
    
    def test_point_dynamique_str_representation(self):
        point = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point Test',
            type_point='ONT',
            latitude='48.8576',
            longitude='2.3400',
            ordre=1
        )
        expected = "Point Test (ONT) - LIA001"
        self.assertEqual(str(point), expected)


class SegmentModelTest(TestCase):
    """Tests pour le modèle Segment"""
    
    def setUp(self):
        self.client = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.point1 = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point 1',
            type_point='chambre',
            latitude='48.8576',
            longitude='2.3400',
            ordre=1
        )
        self.point2 = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point 2',
            type_point='manchon',
            latitude='48.8586',
            longitude='2.3350',
            ordre=2
        )
    
    def test_create_segment(self):
        segment = Segment.objects.create(
            liaison=self.liaison,
            point_depart=self.point1,
            point_arrivee=self.point2,
            distance_gps=2.0,
            distance_cable=2.5
        )
        self.assertEqual(segment.distance_cable, 2.5)
        self.assertEqual(segment.distance_gps, 2.0)
    
    def test_segment_str_representation(self):
        segment = Segment.objects.create(
            liaison=self.liaison,
            point_depart=self.point1,
            point_arrivee=self.point2,
            distance_gps=2.0,
            distance_cable=2.5
        )
        expected = "Segment: Point 1 → Point 2"
        self.assertEqual(str(segment), expected)


class CoupureServiceTest(TestCase):
    """Tests pour CoupureService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='technicien',
            email='tech@test.com',
            role='technicien'
        )
        self.client = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.point = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point Test',
            type_point='chambre',
            latitude='48.8576',
            longitude='2.3400',
            distance_depuis_central=1.5,
            ordre=1
        )
        self.mesure = MesureOTDR.objects.create(
            liaison=self.liaison,
            distance_coupure=1.2,
            attenuation=5.0,
            type_evenement='coupure',
            position_technicien='central',
            direction_analyse='vers_client',
            technicien=self.user
        )
    
    def test_creer_coupure(self):
        coupure = CoupureService.creer_coupure(self.mesure)
        self.assertIsInstance(coupure, Coupure)
        self.assertEqual(coupure.liaison, self.liaison)
        self.assertEqual(coupure.mesure_otdr, self.mesure)
        self.assertEqual(coupure.status, 'detectee')
    
    def test_analyser_coupure(self):
        analyse = CoupureService.analyser_coupure(self.mesure)
        self.assertIn('distance_absolue', analyse)
        self.assertIn('precision_estimation', analyse)
        self.assertIsInstance(analyse['distance_absolue'], float)


class NavigationServiceTest(TestCase):
    """Tests pour NavigationService"""
    
    def test_calculer_distance_gps(self):
        # Distance entre Paris et Marseille (approximativement 660km)
        distance = NavigationService.calculer_distance_gps(
            48.8566, 2.3522,  # Paris
            43.2965, 5.3698   # Marseille
        )
        self.assertGreater(distance, 600)
        self.assertLess(distance, 700)
    
    def test_calculer_distance_gps_meme_point(self):
        distance = NavigationService.calculer_distance_gps(
            48.8566, 2.3522,
            48.8566, 2.3522
        )
        self.assertEqual(distance, 0)


class SegmentServiceTest(TestCase):
    """Tests pour SegmentService"""
    
    def test_calculer_distance_gps(self):
        # Test avec des coordonnées proches
        distance = SegmentService.calculer_distance_gps(
            48.8566, 2.3522,
            48.8576, 2.3532
        )
        self.assertGreater(distance, 0)
        self.assertLess(distance, 1)  # Moins d'1km


class APIAuthenticationTest(APITestCase):
    """Tests pour l'authentification API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client = APIClient()
    
    def test_login_valid_credentials(self):
        url = reverse('api-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
    
    def test_login_invalid_credentials(self):
        url = reverse('api-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_protected_endpoint_without_auth(self):
        url = reverse('liaisons-carte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_auth(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('liaisons-carte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LiaisonAPITest(APITestCase):
    """Tests pour l'API des liaisons"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='superviseur'
        )
        self.client_obj = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client_obj,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_liaisons_carte(self):
        url = reverse('liaisons-carte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_get_liaisons_bounds(self):
        url = reverse('liaisons-bounds')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('bounds', response.data)
        self.assertIn('center', response.data)
    
    def test_get_trace_liaison(self):
        url = reverse('trace-liaison', kwargs={'liaison_id': self.liaison.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('liaison', response.data)
        self.assertIn('trace', response.data)
        self.assertIn('statistiques', response.data)


class PointDynamiqueAPITest(APITestCase):
    """Tests pour l'API des points dynamiques"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client_obj = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client_obj,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.point = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point Test',
            type_point='ONT',
            latitude='48.8576',
            longitude='2.3400',
            ordre=1
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_points_dynamiques_carte(self):
        url = reverse('points-dynamiques-carte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class CoupureAPITest(APITestCase):
    """Tests pour l'API des coupures"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client_obj = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client_obj,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_detecter_coupure(self):
        url = reverse('detecter-coupure')
        data = {
            'liaison_id': str(self.liaison.id),
            'distance_coupure': 1.5,
            'attenuation': 5.0,
            'commentaires': 'Test de détection'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('coupure', response.data)
        self.assertIn('analyse', response.data)
    
    def test_detecter_coupure_liaison_inexistante(self):
        url = reverse('detecter-coupure')
        data = {
            'liaison_id': '00000000-0000-0000-0000-000000000000',
            'distance_coupure': 1.5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_simuler_analyse_otdr(self):
        url = reverse('simuler-analyse-otdr')
        data = {
            'liaison_id': str(self.liaison.id),
            'distance_test': 1.5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resultats', response.data)


class NavigationAPITest(APITestCase):
    """Tests pour l'API de navigation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client_obj = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client_obj,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
        self.point = PointDynamique.objects.create(
            liaison=self.liaison,
            nom='Point Test',
            type_point='ONT',
            latitude='48.8576',
            longitude='2.3400',
            ordre=1
        )
        self.client.force_authenticate(user=self.user)
    
    def test_mettre_a_jour_position(self):
        url = reverse('position-technicien')
        data = {
            'position': {
                'latitude': 48.8566,
                'longitude': 2.3522
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('position_enregistree', response.data)
    
    def test_navigation_vers_point(self):
        url = reverse('navigation-point')
        data = {
            'point_id': str(self.point.id),
            'position_actuelle': {
                'latitude': 48.8566,
                'longitude': 2.3522
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_navigation_vers_point_inexistant(self):
        url = reverse('navigation-point')
        data = {
            'point_id': '00000000-0000-0000-0000-000000000000',
            'position_actuelle': {
                'latitude': 48.8566,
                'longitude': 2.3522
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StatistiquesAPITest(APITestCase):
    """Tests pour l'API des statistiques"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='superviseur'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_statistiques_carte(self):
        url = reverse('statistiques-carte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('carte', response.data)
    
    def test_statistiques_diagnostics(self):
        url = reverse('statistiques-diagnostics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mesures_otdr', response.data)
        self.assertIn('coupures', response.data)


class RechercheGeographiqueAPITest(APITestCase):
    """Tests pour l'API de recherche géographique"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_recherche_geographique_valide(self):
        url = reverse('recherche-geographique')
        params = {
            'lat_min': 48.85,
            'lat_max': 48.87,
            'lng_min': 2.35,
            'lng_max': 2.37
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('zone', response.data)
        self.assertIn('resultats', response.data)
        self.assertIn('statistiques', response.data)
    
    def test_recherche_geographique_parametres_manquants(self):
        url = reverse('recherche-geographique')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_recherche_geographique_coordonnees_invalides(self):
        url = reverse('recherche-geographique')
        params = {
            'lat_min': 'invalid',
            'lat_max': 48.87,
            'lng_min': 2.35,
            'lng_max': 2.37
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Tests d'intégration supplémentaires
class IntegrationTest(APITestCase):
    """Tests d'intégration pour vérifier les workflows complets"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role='technicien'
        )
        self.client.force_authenticate(user=self.user)
        
        # Créer des données de test
        self.client_obj = Client.objects.create(
            name='Test Client',
            type_client='FTTH',
            type_organisation='particulier',
            address='123 Test Street, Test City, 12345',
            phone='+33123456789'
        )
        self.type_liaison = TypeLiaison.objects.create(
            type='LS',
            description='Liaison Spécialisée'
        )
        self.liaison = Liaison.objects.create(
            nom_liaison='LIA001',
            client=self.client_obj,
            type_liaison=self.type_liaison,
            point_central_lat='48.8566',
            point_central_lng='2.3522',
            point_client_lat='48.8606',
            point_client_lng='2.3376'
        )
    
    def test_workflow_detection_coupure_complete(self):
        """Test du workflow complet de détection de coupure"""
        
        # 1. Détecter une coupure
        url_detect = reverse('detecter-coupure')
        data_detect = {
            'liaison_id': str(self.liaison.id),
            'distance_coupure': 1.5,
            'attenuation': 5.0,
            'commentaires': 'Coupure détectée lors de tests'
        }
        response_detect = self.client.post(url_detect, data_detect, format='json')
        self.assertEqual(response_detect.status_code, status.HTTP_201_CREATED)
        
        coupure_id = response_detect.data['coupure']['id']
        
        # 2. Vérifier que la coupure apparaît dans la liste des coupures actives
        url_actives = reverse('coupures-carte')
        response_actives = self.client.get(url_actives)
        self.assertEqual(response_actives.status_code, status.HTTP_200_OK)
        coupure_ids = [c['id'] for c in response_actives.data]
        self.assertIn(coupure_id, coupure_ids)
        
        # 3. Mettre à jour le statut de la coupure
        url_status = reverse('coupure-status', kwargs={'pk': coupure_id})
        data_status = {'status': 'en_cours'}
        response_status = self.client.put(url_status, data_status, format='json')
        self.assertEqual(response_status.status_code, status.HTTP_200_OK)
        
        # 4. Vérifier que le statut a été mis à jour
        coupure = Coupure.objects.get(id=coupure_id)
        self.assertEqual(coupure.status, 'en_cours')


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["api"])