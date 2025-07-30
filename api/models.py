from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import hashlib
import time

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

    def __str__(self):
        return f"{self.username} ({self.role})"

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

    class Meta:
        ordering = ['name']

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

    class Meta:
        verbose_name = "Type de liaison"
        verbose_name_plural = "Types de liaisons"

class Liaison(models.Model):
    """Liaison fibre optique principale"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('en_panne', 'En panne'),
        ('en_cours', 'En cours de réparation'),
        ('planifiee', 'Planifiée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='liaisons')
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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='liaisons_creees')

    def __str__(self):
        return f"{self.nom_liaison} - {self.client.name}"

    class Meta:
        ordering = ['-created_at']

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
        verbose_name = "Point dynamique"
        verbose_name_plural = "Points dynamiques"

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

    def __str__(self):
        return f"Photo - {self.point_dynamique.nom}"

    class Meta:
        ordering = ['-uploaded_at']

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

    def __str__(self):
        return f"OTDR {self.liaison.nom_liaison} - {self.date_mesure.strftime('%d/%m/%Y')}"

    class Meta:
        ordering = ['-date_mesure']
        verbose_name = "Mesure OTDR"
        verbose_name_plural = "Mesures OTDR"

class Coupure(models.Model):
    """Coupures détectées et leur localisation"""
    STATUS_CHOICES = [
        ('detectee', 'Détectée'),
        ('en_cours', 'En cours de réparation'),
        ('reparee', 'Réparée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, on_delete=models.CASCADE, related_name='coupures')
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

    def __str__(self):
        return f"Coupure {self.liaison.nom_liaison} - {self.status}"

    class Meta:
        ordering = ['-date_detection']

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

    def __str__(self):
        return f"{self.type_intervention} - {self.liaison.nom_liaison}"

    class Meta:
        ordering = ['-date_planifiee']

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

    def save(self, *args, **kwargs):
        if not self.hash_commit:
            # Générer un hash unique pour le commit
            timestamp = str(time.time())
            content = f"{self.message_commit}{timestamp}"
            self.hash_commit = hashlib.sha1(content.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hash_commit[:8]} - {self.message_commit}"

    class Meta:
        ordering = ['-date_commit']

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

    def __str__(self):
        return f"Fiche technique - {self.point_dynamique.nom}"

    class Meta:
        verbose_name = "Fiche technique"
        verbose_name_plural = "Fiches techniques"

class Notification(models.Model):
    """Système de notifications"""
    TYPE_CHOICES = [
        ('coupure', 'Coupure détectée'),
        ('intervention', 'Intervention planifiée'),
        ('maintenance', 'Maintenance requise'),
        ('alerte', 'Alerte système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
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

    def __str__(self):
        return f"{self.titre} - {self.destinataire.username}"

    class Meta:
        ordering = ['-date_creation']

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

    class Meta:
        verbose_name = "Paramètre application"
        verbose_name_plural = "Paramètres application"