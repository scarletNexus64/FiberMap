from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class User(AbstractUser):
    """Utilisateur étendu avec rôles spécifiques"""
    ROLE_CHOICES = [
        ('technicien', 'Technicien'),
        ('superviseur', 'Superviseur'),
        ('commercial', 'Commercial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='technicien')
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Client(models.Model):
    """Client (entreprise ou particulier)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=[
        ('entreprise', 'Entreprise'),
        ('banque', 'Banque'),
        ('particulier', 'Particulier')
    ])
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TypeLiaison(models.Model):
    """Types de liaisons (LS ou GPON)"""
    LIAISON_TYPES = [
        ('LS', 'Liaison Spécialisée'),
        ('GPON', 'Liaison NBN (GPON)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=LIAISON_TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.type} - {self.description}"

class Liaison(models.Model):
    """Liaison fibre optique principale"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('en_panne', 'En panne'),
        ('en_cours', 'En cours de réparation'),
        ('planifiee', 'Planifiée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    type_liaison = models.ForeignKey(TypeLiaison, on_delete=models.CASCADE)
    nom_liaison = models.CharField(max_length=255, unique=True)
    
    # Coordonnées géographiques
    point_central_lat = models.DecimalField(max_digits=10, decimal_places=8)
    point_central_lng = models.DecimalField(max_digits=11, decimal_places=8)
    point_client_lat = models.DecimalField(max_digits=10, decimal_places=8)
    point_client_lng = models.DecimalField(max_digits=11, decimal_places=8)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    distance_totale = models.FloatField(help_text="Distance en km")
    
    # Spécifique aux liaisons spécialisées
    convertisseur_central = models.CharField(max_length=100, blank=True)
    convertisseur_client = models.CharField(max_length=100, blank=True)
    type_connectique = models.CharField(max_length=20, choices=[
        ('FC/SC', 'FC/SC'),
        ('LC/SC', 'LC/SC'),
        ('SC/SC', 'SC/SC')
    ], blank=True)
    
    # Spécifique aux liaisons GPON
    olt_source = models.CharField(max_length=100, blank=True)
    port_olt = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.nom_liaison} - {self.client.name}"

class PointDynamique(models.Model):
    """Points intermédiaires sur une liaison (chambres, manchons, etc.)"""
    TYPE_CHOICES = [
        ('chambre', 'Chambre de tirage'),
        ('manchon', 'Manchon'),
        ('convertisseur', 'Convertisseur'),
        ('fdh', 'FDH (Fiber Distribution Hub)'),
        ('splitter', 'Splitter/Répartiteur'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='points_dynamiques', on_delete=models.CASCADE)
    type_point = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nom = models.CharField(max_length=255)
    
    # Position géographique
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    
    # Position sur la liaison (distance depuis le central)
    distance_depuis_central = models.FloatField(help_text="Distance en km depuis le central")
    
    # Informations techniques
    description = models.TextField(blank=True)
    type_armoire = models.CharField(max_length=100, blank=True)
    presence_splitter = models.BooleanField(default=False)
    ratio_splitter = models.CharField(max_length=20, blank=True)  # ex: 1:8, 1:16
    port_utilise = models.CharField(max_length=50, blank=True)
    type_distribution = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['distance_depuis_central']

    def __str__(self):
        return f"{self.nom} ({self.type_point}) - {self.liaison.nom_liaison}"

class PhotoPoint(models.Model):
    """Photos associées aux points dynamiques"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    point_dynamique = models.ForeignKey(PointDynamique, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='points_photos/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class MesureOTDR(models.Model):
    """Mesures OTDR effectuées sur une liaison"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='mesures_otdr', on_delete=models.CASCADE)
    
    # Mesures
    distance_coupure = models.FloatField(help_text="Distance de la coupure en km")
    attenuation = models.FloatField(help_text="Atténuation en dB")
    type_evenement = models.CharField(max_length=50, choices=[
        ('coupure', 'Coupure'),
        ('attenuation', 'Atténuation excessive'),
        ('reflet', 'Réflexion'),
    ])
    
    # Métadonnées
    technicien = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_mesure = models.DateTimeField(auto_now_add=True)
    commentaires = models.TextField(blank=True)
    fichier_otdr = models.FileField(upload_to='otdr_files/', blank=True)

class Coupure(models.Model):
    """Coupures détectées et leur localisation"""
    STATUS_CHOICES = [
        ('detectee', 'Détectée'),
        ('en_cours', 'En cours de réparation'),
        ('reparee', 'Réparée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, on_delete=models.CASCADE)
    mesure_otdr = models.ForeignKey(MesureOTDR, on_delete=models.CASCADE)
    
    # Localisation calculée
    point_estime_lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    point_estime_lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    point_dynamique_proche = models.ForeignKey(PointDynamique, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detectee')
    description_diagnostic = models.TextField(blank=True)
    
    date_detection = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    superviseur_notifie = models.BooleanField(default=False)
    client_notifie = models.BooleanField(default=False)

class Intervention(models.Model):
    """Interventions techniques (création, modification, dépannage)"""
    TYPE_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('depannage', 'Dépannage'),
        ('maintenance', 'Maintenance préventive'),
    ]
    
    STATUS_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='interventions', on_delete=models.CASCADE)
    coupure = models.ForeignKey(Coupure, on_delete=models.SET_NULL, null=True, blank=True)
    
    type_intervention = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planifiee')
    
    # Personnel
    technicien_principal = models.ForeignKey(User, related_name='interventions_principales', on_delete=models.CASCADE)
    techniciens_secondaires = models.ManyToManyField(User, related_name='interventions_secondaires', blank=True)
    
    # Planification
    date_planifiee = models.DateTimeField()
    date_debut = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    duree_estimee = models.DurationField()
    
    # Description
    description = models.TextField()
    resume_changement = models.TextField(blank=True)
    materiel_utilise = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CommitIntervention(models.Model):
    """Historique des modifications (système de commits type Git)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    intervention = models.ForeignKey(Intervention, related_name='commits', on_delete=models.CASCADE)
    
    # Commit info
    message_commit = models.CharField(max_length=255)
    description_detaillee = models.TextField(blank=True)
    hash_commit = models.CharField(max_length=40, unique=True)  # SHA-1 like
    
    # Changements
    changements_json = models.JSONField()  # Stockage des changements effectués
    
    # Métadonnées
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_commit = models.DateTimeField(auto_now_add=True)
    
    # État avant/après (pour comparaison)
    etat_avant = models.JSONField(blank=True, null=True)
    etat_apres = models.JSONField(blank=True, null=True)

class FicheTechnique(models.Model):
    """Fiches techniques des composants réseau"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE)
    
    # Informations techniques détaillées
    modele_equipement = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    fabricant = models.CharField(max_length=100, blank=True)
    date_installation = models.DateField(null=True, blank=True)
    
    # Spécifications techniques
    specifications_json = models.JSONField(blank=True, null=True)
    
    # Documentation
    manuel_url = models.URLField(blank=True)
    notes_maintenance = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    """Système de notifications"""
    TYPE_CHOICES = [
        ('coupure', 'Coupure détectée'),
        ('intervention', 'Intervention planifiée'),
        ('maintenance', 'Maintenance requise'),
        ('alerte', 'Alerte système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE)
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    titre = models.CharField(max_length=255)
    message = models.TextField()
    
    # Liens vers les objets concernés
    liaison = models.ForeignKey(Liaison, on_delete=models.CASCADE, null=True, blank=True)
    coupure = models.ForeignKey(Coupure, on_delete=models.CASCADE, null=True, blank=True)
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, null=True, blank=True)
    
    # État
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_lecture = models.DateTimeField(null=True, blank=True)

class ParametreApplication(models.Model):
    """Paramètres configurables de l'application"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(blank=True)
    type_donnee = models.CharField(max_length=20, choices=[
        ('string', 'Texte'),
        ('integer', 'Entier'),
        ('float', 'Décimal'),
        ('boolean', 'Booléen'),
        ('json', 'JSON'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cle}: {self.valeur}"


Parfait ! Voici la checklist structurée pour FiberMap basée sur ma compréhension du projet :
📋 CHECKLIST FIBERMAP - DJANGO REST FRAMEWORK
🗃️ MODELS (Base de données)
Gestion des utilisateurs :

User (extension d'AbstractUser avec rôles : technicien/superviseur/commercial)
Notification (alertes et messages)

Gestion des clients et liaisons :

Client (entreprises, banques, particuliers)
TypeLiaison (LS ou GPON)
Liaison (liaison principale avec coordonnées central-client)
PointDynamique (chambres, manchons, convertisseurs, splitters sur la liaison)
PhotoPoint (photos des points d'intervention)

Diagnostic et maintenance :

MesureOTDR (données de mesures)
Coupure (localisation des pannes)
Intervention (planification et suivi des interventions)
CommitIntervention (historique type Git des modifications)
FicheTechnique (documentation technique des équipements)

Configuration :

ParametreApplication (paramètres système configurables)

🔄 SERIALIZERS (API REST)
Authentification :

UserSerializer (profil utilisateur)
LoginSerializer (connexion)
NotificationSerializer (alertes)

Données métier :

ClientSerializer
TypeLiaisonSerializer
LiaisonSerializer (avec nested points dynamiques)
LiaisonDetailSerializer (version complète)
PointDynamiqueSerializer
PhotoPointSerializer

Diagnostic :

MesureOTDRSerializer
CoupureSerializer (avec coordonnées calculées)
InterventionSerializer
CommitInterventionSerializer
FicheTechniqueSerializer

Vues spécialisées :

LiaisonMapSerializer (données optimisées pour la carte)
InterventionPlanningSerializer (planning technicien)

📍 ENDPOINTS & VUES (API Mobile)
🔐 Authentification :

POST /api/auth/login/ - Connexion
POST /api/auth/logout/ - Déconnexion
GET /api/auth/profile/ - Profil utilisateur
PUT /api/auth/profile/ - Modifier profil

🗺️ Cartographie (PRINCIPAL pour Flutter Map) :

GET /api/liaisons/map/ - Toutes les liaisons pour la carte
GET /api/liaisons/map/bounds/ - Liaisons dans une zone géographique
GET /api/liaisons/{id}/trace/ - Tracé complet d'une liaison
GET /api/points-dynamiques/map/ - Points sur la carte
GET /api/coupures/map/ - Coupures actives sur la carte

📡 Gestion des liaisons :

GET /api/liaisons/ - Liste des liaisons
POST /api/liaisons/ - Créer liaison
GET /api/liaisons/{id}/ - Détail liaison
PUT /api/liaisons/{id}/ - Modifier liaison
DELETE /api/liaisons/{id}/ - Supprimer liaison
GET /api/liaisons/{id}/historique/ - Historique interventions

🔧 Points d'intervention :

GET /api/points-dynamiques/ - Points d'une liaison
POST /api/points-dynamiques/ - Ajouter point
GET /api/points-dynamiques/{id}/ - Détail point
PUT /api/points-dynamiques/{id}/ - Modifier point
POST /api/points-dynamiques/{id}/photos/ - Ajouter photo

⚡ Diagnostic OTDR :

POST /api/mesures-otdr/ - Enregistrer mesure OTDR
GET /api/mesures-otdr/liaison/{id}/ - Mesures d'une liaison
POST /api/coupures/detecter/ - Détecter coupure depuis OTDR
GET /api/coupures/ - Liste des coupures
PUT /api/coupures/{id}/status/ - Changer statut coupure

👨‍🔧 Interventions :

GET /api/interventions/ - Interventions du technicien
POST /api/interventions/ - Planifier intervention
GET /api/interventions/{id}/ - Détail intervention
PUT /api/interventions/{id}/status/ - Changer statut
POST /api/interventions/{id}/commit/ - Enregistrer modification

📱 Navigation GPS :

GET /api/navigation/coupure/{id}/ - Itinéraire vers coupure
GET /api/navigation/point/{id}/ - Itinéraire vers point
POST /api/navigation/position/ - Mettre à jour position technicien

📊 Données référentielles :

GET /api/clients/ - Liste clients
GET /api/types-liaisons/ - Types de liaisons
GET /api/notifications/ - Notifications utilisateur
PUT /api/notifications/{id}/lue/ - Marquer comme lue

📈 Statistiques/Reporting :

GET /api/stats/dashboard/ - Dashboard technicien
GET /api/stats/interventions/ - Stats interventions
GET /api/stats/coupures/ - Stats des pannes

🎯 VUES SPÉCIALISÉES (ViewSets Django)
MapViewSet :

Optimisé pour Flutter Map
Filtrage géographique (bounding box)
Données allégées pour performance

LiaisonViewSet :

CRUD complet
Actions personnalisées (trace, historique)
Permissions par rôle

InterventionViewSet :

Filtrage par technicien/statut
Actions de workflow (planifier, commencer, terminer)

DiagnosticViewSet :

Traitement des mesures OTDR
Calcul automatique des positions de coupure
Génération d'alertes

NavigationViewSet :

Calcul d'itinéraires
Tracking des techniciens
Optimisation des tournées

Cette architecture permettra à votre app Flutter de :

Afficher les liaisons sur une carte interactive
Naviguer vers les points d'intervention
Saisir et consulter les diagnostics
Gérer les interventions en temps réel
Synchroniser les données hors-ligne



Je vais analyser ces documents pour comprendre le projet FiberMap. Il s'agit d'un projet de conception d'une application mobile pour le diagnostic géolocalisé des coupures et la mémoire technique des liaisons fibres optiques.
Voici les points clés que je comprends :

Objectif principal : Créer un assistant mobile pour diagnostiquer et géolocaliser les coupures de fibres optiques
Fonctionnalités principales :

Visualisation cartographique des liaisons fibres
Gestion des interventions techniques (création, modification, dépannage)
Historique des interventions avec système de commits (type Git)
Détection et localisation de coupures via mesures OTDR
Guidage GPS vers les points d'intervention
Interface de saisie assistée pour les données techniques
Gestion des utilisateurs (technicien, superviseur, commercial)


Types de liaisons gérées :

Liaisons spécialisées (LS) : point-à-point dédiées à un client
Liaisons NBN (GPON) : avec cheminement OLT → ODF → OJF → FDT → FAT → abonné


Comptes utilisateurs :

Technicien : création, mise à jour, dépannage de liaisons
Superviseur : coordination et analyse, notifications de coupures
Commercial : consultation uniquement (liaisons affectées par coupures, dates, statut)


Architecture technique :

Mode manuel : saisie des mesures OTDR
Mode automatique (futur) : intégration avec OTDR distant via splitter


Données techniques à gérer :

Points dynamiques (chambres, manchons, convertisseurs)
Fiches techniques des composants
Photos des points
Mesures OTDR
Historique des modifications



Je vais structurer un système complet qui capture tous ces éléments techniques. Les données techniques seront essentielles pour documenter précisément chaque intervention et point de réseau fibre. L'objectif est de créer une mémoire technique exhaustive et dynamique pour les équipes techniques.