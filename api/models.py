from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import hashlib
import time

# ========================
# CHOIX CONSTANTS
# ========================

COULEUR_CHOICES = [
    ('blue', 'Bleu'),
    ('orange', 'Orange'),
    ('vert', 'Vert'),
    ('marron', 'Marron'),
    ('gris', 'Gris'),
    ('blanc', 'Blanc'),
    ('rouge', 'Rouge'),
    ('noir', 'Noir'),
    ('jaune', 'Jaune'),
    ('violet', 'Violet'),
    ('rose', 'Rose'),
    ('turquoise', 'Turquoise'),
]

CAPACITE_CABLE_CHOICES = [
    (96, '96 FO'),
    (48, '48 FO'),
    (24, '24 FO'),
    (18, '18 FO'),
    (12, '12 FO'),
    (6, '6 FO'),
    (2, '2 FO'),
]

CONNECTEUR_CHOICES = [
    ('FC', 'FC'),
    ('LC', 'LC'),
    ('SC', 'SC'),
]

# ========================
# MODÈLES UTILISATEUR
# ========================

class User(AbstractUser):
    """Utilisateur étendu avec rôles spécifiques"""
    ROLE_CHOICES = [
        ('technicien', 'Technicien'),
        ('superviseur', 'Superviseur'),
        ('commercial', 'Commercial'),
        ('admin', 'Administrateur'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='technicien')
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

# ========================
# MODÈLES CLIENT
# ========================

class Client(models.Model):
    """Client (entreprise ou particulier)"""
    TYPE_CLIENT_CHOICES = [
        ('LS', 'Client LS (Liaison Spécialisée)'),
        ('FTTH', 'Client FTTH'),
    ]
    
    TYPE_ORGANISATION_CHOICES = [
        ('entreprise', 'Entreprise'),
        ('banque', 'Banque'),
        ('particulier', 'Particulier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type_client = models.CharField(max_length=10, choices=TYPE_CLIENT_CHOICES)
    type_organisation = models.CharField(max_length=50, choices=TYPE_ORGANISATION_CHOICES)
    raison_sociale = models.CharField(max_length=255, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    
    # Pour clients FTTH
    numero_ligne = models.CharField(max_length=50, blank=True)
    nom_ligne = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.type_client})"

    class Meta:
        ordering = ['name']

# ========================
# MODÈLES LIAISON
# ========================

class TypeLiaison(models.Model):
    """Types de liaisons"""
    LIAISON_TYPES = [
        ('LS', 'Liaison Spécialisée'),
        ('FTTH', 'FTTH (Fiber To The Home)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=10, choices=LIAISON_TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_type_display()

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
    distance_totale = models.FloatField(help_text="Distance totale calculée en km", default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='liaisons_creees')

    def calculer_distance_totale(self):
        """Calcule la distance totale à partir des segments"""
        total = self.segments.aggregate(total=models.Sum('distance_cable'))['total'] or 0
        self.distance_totale = total
        self.save()
        return total

    def __str__(self):
        return f"{self.nom_liaison} - {self.client.name}"

    class Meta:
        ordering = ['-created_at']

# ========================
# MODÈLES POINTS DYNAMIQUES
# ========================

class PointDynamique(models.Model):
    """Points intermédiaires sur une liaison"""
    TYPE_CHOICES = [
        # Points terminaux
        ('ONT', 'ONT (Optical Network Terminal)'),
        ('POP_LS', 'POP LS (Point of Presence LS)'),
        ('POP_FTTH', 'POP FTTH (Point of Presence FTTH)'),
        
        # Points réseau
        ('chambre', 'Chambre de tirage'),
        ('manchon', 'Manchon'),
        ('manchon_aerien', 'Manchon aérien/distribution'),
        ('FAT', 'FAT (Fiber Access Terminal)'),
        ('FDT', 'FDT (Fiber Distribution Terminal)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='points_dynamiques', on_delete=models.CASCADE)
    type_point = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nom = models.CharField(max_length=255)
    ordre = models.IntegerField(help_text="Ordre du point dans la liaison", default=0)
    
    # Position géographique
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    
    # Position sur la liaison
    distance_depuis_central = models.FloatField(help_text="Distance cumulée en km depuis le central", default=0)
    
    # Informations générales
    description = models.TextField(blank=True)
    commentaire_technicien = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['liaison', 'ordre']
        verbose_name = "Point dynamique"
        verbose_name_plural = "Points dynamiques"
        unique_together = [['liaison', 'ordre']]

    def __str__(self):
        return f"{self.nom} ({self.type_point}) - {self.liaison.nom_liaison}"

# ========================
# DÉTAILS POINTS TERMINAUX
# ========================

class DetailONT(models.Model):
    """Détails spécifiques pour ONT"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_ont')
    numero_serie = models.CharField(max_length=100)
    numero_ligne = models.CharField(max_length=50)
    nom_ligne = models.CharField(max_length=100)
    couleur_brin_fat = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    moue_cable = models.FloatField(help_text="Moue de câble en mètres", default=0)

    def __str__(self):
        return f"ONT - {self.numero_serie}"

class DetailPOPLS(models.Model):
    """Détails spécifiques pour POP LS"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_pop_ls')
    
    # Convertisseur
    nombre_brins_convertisseur = models.IntegerField(choices=[(1, '1'), (2, '2')])
    type_connecteur_convertisseur = models.CharField(max_length=10, choices=CONNECTEUR_CHOICES)
    
    # Tiroir optique
    nombre_brins_tiroir = models.IntegerField(choices=[(1, '1'), (2, '2')])
    capacite_cable = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    numero_port_tiroir = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    type_connecteur_tiroir = models.CharField(max_length=10, choices=CONNECTEUR_CHOICES)
    moue_cable = models.FloatField(help_text="Moue de câble en mètres", default=0)

    def __str__(self):
        return f"POP LS - {self.point_dynamique.nom}"

class DetailPOPFTTH(models.Model):
    """Détails spécifiques pour POP FTTH"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_pop_ftth')
    
    # OLT
    reference_olt = models.CharField(max_length=100)
    port_olt = models.CharField(max_length=50)
    
    # ODF
    reference_odf = models.CharField(max_length=100)
    numero_fdt = models.CharField(max_length=50)
    quantieme_cassette = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    numero_port_cassette = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    capacite_cable = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin = models.CharField(max_length=20, choices=COULEUR_CHOICES)

    def __str__(self):
        return f"POP FTTH - {self.reference_olt}"

# ========================
# DÉTAILS POINTS RÉSEAU
# ========================

class DetailChambre(models.Model):
    """Détails spécifiques pour chambres"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_chambre')
    
    # Côté venant du central
    capacite_cable_central = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron_central = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin_central = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    moue_cable_central = models.FloatField(help_text="Moue côté central en mètres", default=0)
    
    # Côté allant vers le client
    capacite_cable_client = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron_client = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin_client = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    moue_cable_client = models.FloatField(help_text="Moue côté client en mètres", default=0)

    def __str__(self):
        return f"Chambre - {self.point_dynamique.nom}"

class DetailManchon(models.Model):
    """Détails spécifiques pour manchons"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_manchon')
    
    # Câble entrant
    capacite_cable_entrant = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron_entrant = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin_entrant = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    
    # Câble sortant
    capacite_cable_sortant = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron_sortant = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin_sortant = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    
    moue_cable = models.FloatField(help_text="Moue de câble en mètres", default=0)
    is_aerien = models.BooleanField(default=False)

    def __str__(self):
        type_manchon = "aérien" if self.is_aerien else "souterrain"
        return f"Manchon {type_manchon} - {self.point_dynamique.nom}"

class FAT(models.Model):
    """FAT (Fiber Access Terminal) - peut exister indépendamment"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_fat = models.CharField(max_length=50, unique=True)
    numero_fdt = models.CharField(max_length=50)
    
    # Position géographique
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    
    # Informations techniques
    port_splitter = models.CharField(max_length=20)
    capacite_cable_entrant = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_toron = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_brin = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    moue_cable_poteau = models.FloatField(help_text="Moue sur le poteau en mètres", default=0)
    
    # Liaison optionnelle
    liaison = models.ForeignKey(Liaison, on_delete=models.SET_NULL, null=True, blank=True, related_name='fats')
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.SET_NULL, null=True, blank=True, related_name='detail_fat')
    
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FAT {self.numero_fat} - FDT {self.numero_fdt}"

    class Meta:
        verbose_name = "FAT"
        verbose_name_plural = "FATs"

class DetailFDT(models.Model):
    """Détails spécifiques pour FDT"""
    point_dynamique = models.OneToOneField(PointDynamique, on_delete=models.CASCADE, related_name='detail_fdt')
    numero_fdt = models.CharField(max_length=50)
    
    # Côté transport (venant du central)
    capacite_cable_transport = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_brin_transport = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_toron_transport = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    cassette_transport = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    port_cassette_transport = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Côté distribution (allant au FAT)
    capacite_cable_distribution = models.IntegerField(choices=CAPACITE_CABLE_CHOICES)
    couleur_brin_distribution = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    couleur_toron_distribution = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    cassette_distribution = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    port_cassette_distribution = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])

    def __str__(self):
        return f"FDT {self.numero_fdt}"

# ========================
# SEGMENTS DE LIAISON
# ========================

class Segment(models.Model):
    """Segment entre deux points dynamiques"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, on_delete=models.CASCADE, related_name='segments')
    
    point_depart = models.ForeignKey(PointDynamique, on_delete=models.CASCADE, related_name='segments_depart')
    point_arrivee = models.ForeignKey(PointDynamique, on_delete=models.CASCADE, related_name='segments_arrivee')
    
    # Distances
    distance_gps = models.FloatField(help_text="Distance GPS en km")
    distance_cable = models.FloatField(help_text="Distance réelle du câble posé en km (incluant moue)")
    
    # Tracé
    trace_coords = models.JSONField(help_text="Coordonnées du tracé [[lat, lng], ...]", default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Segment: {self.point_depart.nom} → {self.point_arrivee.nom}"

    class Meta:
        unique_together = [['point_depart', 'point_arrivee']]
        ordering = ['point_depart__ordre']

# ========================
# PHOTOS
# ========================

class PhotoPoint(models.Model):
    """Photos associées aux points dynamiques"""
    CATEGORIE_CHOICES = [
        ('site', 'Site/Environnement'),
        ('equipement', 'Équipement'),
        ('manchon', 'Manchon'),
        ('chambre_ext', 'Extérieur chambre'),
        ('chambre_int', 'Intérieur chambre'),
        ('tiroir', 'Tiroir optique'),
        ('convertisseur', 'Convertisseur'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    point_dynamique = models.ForeignKey(PointDynamique, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='points_photos/')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo {self.categorie} - {self.point_dynamique.nom}"

    class Meta:
        ordering = ['-uploaded_at']

# ========================
# MESURES ET DIAGNOSTICS
# ========================

class MesureOTDR(models.Model):
    """Mesures OTDR effectuées sur une liaison"""
    POSITION_CHOICES = [
        ('central', 'Au central'),
        ('client', 'Chez le client'),
        ('intermediaire', 'Point intermédiaire'),
    ]
    
    DIRECTION_CHOICES = [
        ('vers_central', 'Vers le central'),
        ('vers_client', 'Vers le client'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='mesures_otdr', on_delete=models.CASCADE)
    
    # Position et direction
    position_technicien = models.CharField(max_length=20, choices=POSITION_CHOICES)
    point_mesure = models.ForeignKey(PointDynamique, on_delete=models.SET_NULL, null=True, blank=True)
    direction_analyse = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    
    # Mesures
    distance_coupure = models.FloatField(help_text="Distance de la coupure en km")
    attenuation = models.FloatField(help_text="Atténuation en dB")
    type_evenement = models.CharField(max_length=50, choices=[
        ('coupure', 'Coupure'),
        ('attenuation', 'Atténuation excessive'),
        ('reflet', 'Réflexion'),
        ('epissure', 'Épissure défectueuse'),
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
        ('localisee', 'Localisée'),
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
    segment_touche = models.ForeignKey(Segment, on_delete=models.SET_NULL, null=True, blank=True)
    distance_sur_segment = models.FloatField(help_text="Distance depuis le début du segment en km", null=True)
    
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

# ========================
# INTERVENTIONS
# ========================

class Intervention(models.Model):
    """Interventions techniques"""
    TYPE_CHOICES = [
        ('creation', 'Création liaison'),
        ('modification', 'Modification'),
        ('depannage', 'Dépannage'),
        ('maintenance', 'Maintenance préventive'),
        ('ajout_point', 'Ajout point dynamique'),
    ]
    
    STATUS_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    liaison = models.ForeignKey(Liaison, related_name='interventions', on_delete=models.CASCADE, null=True, blank=True)
    coupure = models.ForeignKey(Coupure, on_delete=models.SET_NULL, null=True, blank=True)
    fat = models.ForeignKey(FAT, on_delete=models.SET_NULL, null=True, blank=True)
    
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
    
    # Rapport
    rapport_final = models.TextField(blank=True)
    photos_avant = models.ManyToManyField(PhotoPoint, related_name='interventions_avant', blank=True)
    photos_apres = models.ManyToManyField(PhotoPoint, related_name='interventions_apres', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.liaison:
            return f"{self.type_intervention} - {self.liaison.nom_liaison}"
        elif self.fat:
            return f"{self.type_intervention} - FAT {self.fat.numero_fat}"
        return f"{self.type_intervention} - {self.id}"

    class Meta:
        ordering = ['-date_planifiee']

class CommitIntervention(models.Model):
    """Historique des modifications (système de commits)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    intervention = models.ForeignKey(Intervention, related_name='commits', on_delete=models.CASCADE)
    
    # Commit info
    message_commit = models.CharField(max_length=255)
    description_detaillee = models.TextField(blank=True)
    hash_commit = models.CharField(max_length=40, unique=True)
    
    # Changements
    changements_json = models.JSONField()
    
    # Métadonnées
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_commit = models.DateTimeField(auto_now_add=True)
    
    # État avant/après
    etat_avant = models.JSONField(blank=True, null=True)
    etat_apres = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.hash_commit:
            timestamp = str(time.time())
            content = f"{self.message_commit}{timestamp}{self.auteur.id}"
            self.hash_commit = hashlib.sha1(content.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hash_commit[:8]} - {self.message_commit}"

    class Meta:
        ordering = ['-date_commit']

# ========================
# FICHES TECHNIQUES
# ========================

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

# ========================
# NOTIFICATIONS
# ========================

class Notification(models.Model):
    """Système de notifications"""
    TYPE_CHOICES = [
        ('coupure', 'Coupure détectée'),
        ('intervention', 'Intervention planifiée'),
        ('maintenance', 'Maintenance requise'),
        ('alerte', 'Alerte système'),
        ('rapport', 'Rapport disponible'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale')
    
    titre = models.CharField(max_length=255)
    message = models.TextField()
    
    # Liens vers les objets concernés
    liaison_concernee = models.ForeignKey(Liaison, on_delete=models.CASCADE, null=True, blank=True)
    coupure_concernee = models.ForeignKey(Coupure, on_delete=models.CASCADE, null=True, blank=True)
    intervention_concernee = models.ForeignKey(Intervention, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    lue = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_notification} - {self.destinataire.username}"

    class Meta:
        ordering = ['-created_at']

# ========================
# PARAMÈTRES APPLICATION
# ========================

class ParametreApplication(models.Model):
    """Paramètres globaux de l'application"""
    TYPE_PARAM_CHOICES = [
        ('otdr', 'Configuration OTDR'),
        ('carte', 'Configuration carte'),
        ('notification', 'Configuration notifications'),
        ('general', 'Configuration générale'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_parametre = models.CharField(max_length=20, choices=TYPE_PARAM_CHOICES)
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type_parametre} - {self.cle}"

    class Meta:
        ordering = ['type_parametre', 'cle']
        verbose_name = "Paramètre application"
        verbose_name_plural = "Paramètres application"