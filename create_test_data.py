#!/usr/bin/env python
"""
Script pour créer des données de test pour FiberMap
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FiberMap.settings')
django.setup()

from api.models import (
    User, Client, TypeLiaison, Liaison, PointDynamique, 
    MesureOTDR, Coupure, Intervention, Notification, ParametreApplication
)

def create_test_data():
    print("🚀 Création des données de test pour FiberMap...")
    
    # 1. Créer des utilisateurs de test
    print("👥 Création des utilisateurs...")
    
    technicien = User.objects.create_user(
        username='jean.technicien',
        email='jean@fibermap.com',
        password='password123',
        first_name='Jean',
        last_name='Dupont',
        role='technicien',
        phone='+33123456789',
        location='Paris, France'
    )
    
    superviseur = User.objects.create_user(
        username='marie.superviseur',
        email='marie@fibermap.com',
        password='password123',
        first_name='Marie',
        last_name='Martin',
        role='superviseur',
        phone='+33987654321',
        location='Lyon, France'
    )
    
    commercial = User.objects.create_user(
        username='paul.commercial',
        email='paul@fibermap.com',
        password='password123',
        first_name='Paul',
        last_name='Durand',
        role='commercial',
        phone='+33555666777',
        location='Marseille, France'
    )
    
    # 2. Créer des types de liaisons
    print("📡 Création des types de liaisons...")
    
    type_ls = TypeLiaison.objects.create(
        type='LS',
        description='Liaison Spécialisée point-à-point'
    )
    
    type_gpon = TypeLiaison.objects.create(
        type='GPON',
        description='Liaison NBN (Gigabit Passive Optical Network)'
    )
    
    # 3. Créer des clients
    print("🏢 Création des clients...")
    
    client_entreprise = Client.objects.create(
        name='TechCorp Solutions',
        type='entreprise',
        address='123 Avenue des Entreprises, 75001 Paris',
        phone='+33140123456',
        email='contact@techcorp.fr'
    )
    
    client_banque = Client.objects.create(
        name='Banque Nationale',
        type='banque',
        address='456 Boulevard Financier, 69000 Lyon',
        phone='+33478987654',
        email='it@banquenationale.fr'
    )
    
    client_particulier = Client.objects.create(
        name='Résidence Les Jardins',
        type='particulier',
        address='789 Rue des Particuliers, 13000 Marseille',
        phone='+33491555777',
        email='syndic@lesjardin.fr'
    )
    
    # 4. Créer des liaisons
    print("🔗 Création des liaisons...")
    
    liaison1 = Liaison.objects.create(
        client=client_entreprise,
        type_liaison=type_ls,
        nom_liaison='LS-TECHCORP-001',
        point_central_lat=Decimal('48.8566'),    # Paris Centre
        point_central_lng=Decimal('2.3522'),
        point_client_lat=Decimal('48.8606'),     # Client Paris
        point_client_lng=Decimal('2.3376'),
        status='active',
        distance_totale=2.5,
        convertisseur_central='Cisco SFP-1GB-LX',
        convertisseur_client='Cisco SFP-1GB-LX',
        type_connectique='SC/SC',
        created_by=technicien
    )
    
    liaison2 = Liaison.objects.create(
        client=client_banque,
        type_liaison=type_gpon,
        nom_liaison='GPON-BANQUE-001',
        point_central_lat=Decimal('45.7640'),    # Lyon Centre
        point_central_lng=Decimal('4.8357'),
        point_client_lat=Decimal('45.7578'),     # Client Lyon
        point_client_lng=Decimal('4.8320'),
        status='active',
        distance_totale=1.8,
        olt_source='Huawei MA5800-X7',
        port_olt='0/1/0/1',
        created_by=technicien
    )
    
    liaison3 = Liaison.objects.create(
        client=client_particulier,
        type_liaison=type_gpon,
        nom_liaison='GPON-JARDINS-001',
        point_central_lat=Decimal('43.2965'),    # Marseille Centre
        point_central_lng=Decimal('5.3698'),
        point_client_lat=Decimal('43.3047'),     # Client Marseille
        point_client_lng=Decimal('5.3756'),
        status='en_panne',  # Cette liaison a une panne
        distance_totale=3.2,
        olt_source='Nokia ISAM FX',
        port_olt='1/1/1/8',
        created_by=technicien
    )
    
    # 5. Créer des points dynamiques
    print("📍 Création des points dynamiques...")
    
    # Points pour liaison 1 (Paris)
    point1_1 = PointDynamique.objects.create(
        liaison=liaison1,
        type_point='chambre',
        nom='Chambre Rivoli',
        latitude=Decimal('48.8586'),
        longitude=Decimal('2.3449'),
        distance_depuis_central=0.8,
        description='Chambre de tirage principale rue Rivoli',
        type_armoire='Urbaine 600x800',
        presence_splitter=False
    )
    
    point1_2 = PointDynamique.objects.create(
        liaison=liaison1,
        type_point='manchon',
        nom='Manchon Tuileries',
        latitude=Decimal('48.8596'),
        longitude=Decimal('2.3412'),
        distance_depuis_central=1.5,
        description='Manchon de raccordement Jardin des Tuileries',
        presence_splitter=False
    )
    
    # Points pour liaison 2 (Lyon)
    point2_1 = PointDynamique.objects.create(
        liaison=liaison2,
        type_point='fdh',
        nom='FDH Bellecour',
        latitude=Decimal('45.7589'),
        longitude=Decimal('4.8318'),
        distance_depuis_central=0.6,
        description='FDH principal Place Bellecour',
        type_armoire='ARCEP Standard',
        presence_splitter=True,
        ratio_splitter='1:8'
    )
    
    point2_2 = PointDynamique.objects.create(
        liaison=liaison2,
        type_point='splitter',
        nom='Splitter République',
        latitude=Decimal('45.7569'),
        longitude=Decimal('4.8319'),
        distance_depuis_central=1.2,
        description='Splitter secondaire Place de la République',
        presence_splitter=True,
        ratio_splitter='1:16'
    )
    
    # Points pour liaison 3 (Marseille)
    point3_1 = PointDynamique.objects.create(
        liaison=liaison3,
        type_point='chambre',
        nom='Chambre Canebière',
        latitude=Decimal('43.2985'),
        longitude=Decimal('5.3727'),
        distance_depuis_central=1.1,
        description='Chambre principale La Canebière',
        type_armoire='Souterraine',
        presence_splitter=False
    )
    
    # 6. Créer des mesures OTDR et une coupure
    print("⚡ Création des mesures OTDR et coupures...")
    
    # Mesure OTDR normale
    mesure_ok = MesureOTDR.objects.create(
        liaison=liaison1,
        distance_coupure=0.0,  # Pas de coupure
        attenuation=0.8,
        type_evenement='attenuation',
        technicien=technicien,
        commentaires='Mesure normale, liaison opérationnelle'
    )
    
    # Mesure OTDR avec coupure
    mesure_coupure = MesureOTDR.objects.create(
        liaison=liaison3,
        distance_coupure=1.5,  # Coupure à 1.5km
        attenuation=15.2,      # Forte atténuation
        type_evenement='coupure',
        technicien=technicien,
        commentaires='Coupure détectée, forte atténuation'
    )
    
    # Créer la coupure
    coupure = Coupure.objects.create(
        liaison=liaison3,
        mesure_otdr=mesure_coupure,
        point_estime_lat=Decimal('43.3006'),  # Position estimée de la coupure
        point_estime_lng=Decimal('5.3737'),
        point_dynamique_proche=point3_1,
        status='detectee',
        description_diagnostic='Coupure détectée à 1.5km du central, probablement due à des travaux de voirie',
        superviseur_notifie=True,
        client_notifie=False
    )
    
    # 7. Créer des interventions
    print("🔧 Création des interventions...")
    
    # Intervention de dépannage pour la coupure
    intervention_depannage = Intervention.objects.create(
        liaison=liaison3,
        coupure=coupure,
        type_intervention='depannage',
        status='planifiee',
        technicien_principal=technicien,
        date_planifiee=datetime.now() + timedelta(hours=2),
        duree_estimee=timedelta(hours=4),
        description='Réparation de la coupure fibre détectée à 1.5km du central'
    )
    
    # Intervention de maintenance préventive
    intervention_maintenance = Intervention.objects.create(
        liaison=liaison1,
        type_intervention='maintenance',
        status='terminee',
        technicien_principal=technicien,
        date_planifiee=datetime.now() - timedelta(days=1),
        date_debut=datetime.now() - timedelta(days=1),
        date_fin=datetime.now() - timedelta(days=1, hours=-3),
        duree_estimee=timedelta(hours=3),
        description='Maintenance préventive et nettoyage des connecteurs',
        resume_changement='Nettoyage des connecteurs effectué, tests OTDR OK',
        materiel_utilise='Kit de nettoyage fibre, OTDR portable'
    )
    
    # 8. Créer des notifications
    print("🔔 Création des notifications...")
    
    # Notification de coupure pour le superviseur
    Notification.objects.create(
        destinataire=superviseur,
        type_notification='coupure',
        titre='Coupure détectée - GPON-JARDINS-001',
        message=f'Une coupure a été détectée sur la liaison {liaison3.nom_liaison} à 1.5km du central. Intervention planifiée.',
        liaison=liaison3,
        coupure=coupure,
        lue=False
    )
    
    # Notification d'intervention pour le technicien
    Notification.objects.create(
        destinataire=technicien,
        type_notification='intervention',
        titre='Intervention planifiée - Dépannage',
        message=f'Intervention de dépannage planifiée sur {liaison3.nom_liaison} dans 2 heures.',
        liaison=liaison3,
        intervention=intervention_depannage,
        lue=False
    )
    
    # Notification de maintenance terminée pour le commercial
    Notification.objects.create(
        destinataire=commercial,
        type_notification='maintenance',
        titre='Maintenance terminée - LS-TECHCORP-001',
        message=f'La maintenance préventive de la liaison {liaison1.nom_liaison} a été terminée avec succès.',
        liaison=liaison1,
        intervention=intervention_maintenance,
        lue=False
    )
    
    # 9. Créer des paramètres d'application
    print("⚙️ Création des paramètres d'application...")
    
    ParametreApplication.objects.create(
        cle='seuil_attenuation_alerte',
        valeur='10.0',
        description='Seuil d\'atténuation en dB pour déclencher une alerte',
        type_donnee='float'
    )
    
    ParametreApplication.objects.create(
        cle='rayon_recherche_point_proche',
        valeur='0.5',
        description='Rayon en km pour rechercher le point dynamique le plus proche d\'une coupure',
        type_donnee='float'
    )
    
    ParametreApplication.objects.create(
        cle='notification_email_active',
        valeur='true',
        description='Activer les notifications par email',
        type_donnee='boolean'
    )
    
    ParametreApplication.objects.create(
        cle='config_carte_defaut',
        valeur='{"zoom": 10, "centre": {"lat": 46.603354, "lng": 1.888334}}',
        description='Configuration par défaut de la carte (centre France)',
        type_donnee='json'
    )
    
    print("✅ Données de test créées avec succès!")
    print("\n📊 Résumé des données créées:")
    print(f"   • {User.objects.count()} utilisateurs")
    print(f"   • {Client.objects.count()} clients")
    print(f"   • {TypeLiaison.objects.count()} types de liaisons")
    print(f"   • {Liaison.objects.count()} liaisons")
    print(f"   • {PointDynamique.objects.count()} points dynamiques")
    print(f"   • {MesureOTDR.objects.count()} mesures OTDR")
    print(f"   • {Coupure.objects.count()} coupure")
    print(f"   • {Intervention.objects.count()} interventions")
    print(f"   • {Notification.objects.count()} notifications")
    print(f"   • {ParametreApplication.objects.count()} paramètres")
    
    print("\n🔑 Comptes de connexion:")
    print("   Admin:         admin / admin123")
    print("   Technicien:    jean.technicien / password123")
    print("   Superviseur:   marie.superviseur / password123")
    print("   Commercial:    paul.commercial / password123")
    
    print("\n🌐 URLs importantes:")
    print("   Admin Django:  http://127.0.0.1:8000/admin/")
    print("   API Root:      http://127.0.0.1:8000/api/")
    print("   API Docs:      http://127.0.0.1:8000/api/schema/swagger-ui/")
    print("   API Schema:    http://127.0.0.1:8000/api/schema/redoc/")

if __name__ == '__main__':
    create_test_data()