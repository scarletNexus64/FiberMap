from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Client, TypeLiaison, Liaison, PointDynamique, Segment, PhotoPoint,
    DetailONT, DetailPOPLS, DetailPOPFTTH, DetailChambre, DetailManchon, 
    FAT, DetailFDT, MesureOTDR, Coupure, Intervention, CommitIntervention, 
    FicheTechnique, Notification, ParametreApplication
)

# ===============================
# Configuration utilisateurs
# ===============================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour les utilisateurs"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations FiberMap', {
            'fields': ('role', 'phone', 'location')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations FiberMap', {
            'fields': ('role', 'phone', 'location')
        }),
    )

# ===============================
# Inline classes
# ===============================

class PointDynamiqueInline(admin.TabularInline):
    model = PointDynamique
    extra = 0
    fields = ('nom', 'type_point', 'ordre', 'latitude', 'longitude', 'distance_depuis_central')
    readonly_fields = ('created_at', 'updated_at')

class SegmentInline(admin.TabularInline):
    model = Segment
    extra = 0
    fields = ('point_depart', 'point_arrivee', 'distance_gps', 'distance_cable')
    readonly_fields = ('created_at', 'updated_at')

class PhotoPointInline(admin.TabularInline):
    model = PhotoPoint
    extra = 0
    fields = ('image', 'categorie', 'description', 'uploaded_by')
    readonly_fields = ('uploaded_at',)

class MesureOTDRInline(admin.TabularInline):
    model = MesureOTDR
    extra = 0
    fields = ('type_evenement', 'distance_coupure', 'attenuation', 'technicien', 'date_mesure')
    readonly_fields = ('date_mesure',)

class CoupureInline(admin.TabularInline):
    model = Coupure
    extra = 0
    fields = ('status', 'point_dynamique_proche', 'date_detection')
    readonly_fields = ('date_detection',)

class InterventionInline(admin.TabularInline):
    model = Intervention
    extra = 0
    fields = ('type_intervention', 'status', 'technicien_principal', 'date_planifiee')
    readonly_fields = ('created_at',)

# ===============================
# Admins pour les clients
# ===============================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'type_client', 'type_organisation', 'phone', 'email', 'created_at')
    list_filter = ('type_client', 'type_organisation', 'created_at')
    search_fields = ('name', 'raison_sociale', 'phone', 'email')
    ordering = ('name',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'raison_sociale', 'type_client', 'type_organisation')
        }),
        ('Contact', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Informations FTTH', {
            'fields': ('numero_ligne', 'nom_ligne'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TypeLiaison)
class TypeLiaisonAdmin(admin.ModelAdmin):
    list_display = ('type', 'description')
    search_fields = ('type', 'description')

# ===============================
# Admins pour les liaisons
# ===============================

@admin.register(Liaison)
class LiaisonAdmin(admin.ModelAdmin):
    list_display = ('nom_liaison', 'client', 'type_liaison', 'status', 'distance_totale', 'created_at')
    list_filter = ('status', 'type_liaison', 'created_at', 'client__type_client')
    search_fields = ('nom_liaison', 'client__name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom_liaison', 'client', 'type_liaison', 'status')
        }),
        ('Coordonnées géographiques', {
            'fields': (
                ('point_central_lat', 'point_central_lng'),
                ('point_client_lat', 'point_client_lng')
            )
        }),
        ('Informations techniques', {
            'fields': ('distance_totale', 'created_by')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PointDynamiqueInline, SegmentInline, MesureOTDRInline, CoupureInline, InterventionInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'type_liaison', 'created_by')

# ===============================
# Admins pour les points dynamiques
# ===============================

class DetailONTInline(admin.StackedInline):
    model = DetailONT
    extra = 0

class DetailPOPLSInline(admin.StackedInline):
    model = DetailPOPLS
    extra = 0

class DetailPOPFTTHInline(admin.StackedInline):
    model = DetailPOPFTTH
    extra = 0

class DetailChambreInline(admin.StackedInline):
    model = DetailChambre
    extra = 0

class DetailManchonInline(admin.StackedInline):
    model = DetailManchon
    extra = 0

class DetailFDTInline(admin.StackedInline):
    model = DetailFDT
    extra = 0

@admin.register(PointDynamique)
class PointDynamiqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_point', 'liaison', 'ordre', 'latitude', 'longitude', 'distance_depuis_central')
    list_filter = ('type_point', 'liaison__type_liaison', 'created_at')
    search_fields = ('nom', 'description', 'liaison__nom_liaison')
    ordering = ('liaison', 'ordre')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'type_point', 'liaison', 'ordre')
        }),
        ('Position', {
            'fields': (
                ('latitude', 'longitude'),
                'distance_depuis_central'
            )
        }),
        ('Descriptions', {
            'fields': ('description', 'commentaire_technicien')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PhotoPointInline, DetailONTInline, DetailPOPLSInline, DetailPOPFTTHInline, 
               DetailChambreInline, DetailManchonInline, DetailFDTInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('liaison')

@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('point_depart', 'point_arrivee', 'liaison', 'distance_gps', 'distance_cable')
    list_filter = ('liaison', 'created_at')
    search_fields = ('point_depart__nom', 'point_arrivee__nom', 'liaison__nom_liaison')
    ordering = ('liaison', 'point_depart__ordre')
    
    fieldsets = (
        ('Points', {
            'fields': ('liaison', 'point_depart', 'point_arrivee')
        }),
        ('Distances', {
            'fields': ('distance_gps', 'distance_cable')
        }),
        ('Tracé', {
            'fields': ('trace_coords',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FAT)
class FATAdmin(admin.ModelAdmin):
    list_display = ('numero_fat', 'numero_fdt', 'liaison', 'latitude', 'longitude', 'created_at')
    list_filter = ('numero_fdt', 'liaison', 'created_at')
    search_fields = ('numero_fat', 'numero_fdt', 'port_splitter')
    ordering = ('numero_fat',)
    
    fieldsets = (
        ('Identification', {
            'fields': ('numero_fat', 'numero_fdt', 'port_splitter')
        }),
        ('Position', {
            'fields': ('latitude', 'longitude')
        }),
        ('Informations techniques', {
            'fields': ('capacite_cable_entrant', 'couleur_toron', 'couleur_brin', 'moue_cable_poteau')
        }),
        ('Associations', {
            'fields': ('liaison', 'point_dynamique')
        }),
        ('Commentaires', {
            'fields': ('commentaire',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

# ===============================
# Admins pour les photos
# ===============================

@admin.register(PhotoPoint)
class PhotoPointAdmin(admin.ModelAdmin):
    list_display = ('point_dynamique', 'categorie', 'description', 'uploaded_by', 'uploaded_at')
    list_filter = ('categorie', 'uploaded_at', 'uploaded_by')
    search_fields = ('point_dynamique__nom', 'description')
    ordering = ('-uploaded_at',)
    
    readonly_fields = ('uploaded_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('point_dynamique', 'uploaded_by')

# ===============================
# Admins pour les diagnostics
# ===============================

@admin.register(MesureOTDR)
class MesureOTDRAdmin(admin.ModelAdmin):
    list_display = ('liaison', 'type_evenement', 'distance_coupure', 'attenuation', 'technicien', 'date_mesure')
    list_filter = ('type_evenement', 'position_technicien', 'direction_analyse', 'date_mesure')
    search_fields = ('liaison__nom_liaison', 'commentaires')
    ordering = ('-date_mesure',)
    
    fieldsets = (
        ('Mesure', {
            'fields': ('liaison', 'type_evenement', 'distance_coupure', 'attenuation')
        }),
        ('Position et direction', {
            'fields': ('position_technicien', 'point_mesure', 'direction_analyse')
        }),
        ('Métadonnées', {
            'fields': ('technicien', 'commentaires', 'fichier_otdr')
        }),
    )
    
    readonly_fields = ('date_mesure',)
    inlines = [CoupureInline]

@admin.register(Coupure)
class CoupureAdmin(admin.ModelAdmin):
    list_display = ('liaison', 'status', 'point_dynamique_proche', 'date_detection', 'date_resolution')
    list_filter = ('status', 'date_detection', 'superviseur_notifie', 'client_notifie')
    search_fields = ('liaison__nom_liaison', 'description_diagnostic')
    ordering = ('-date_detection',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('liaison', 'mesure_otdr', 'status')
        }),
        ('Localisation', {
            'fields': (
                ('point_estime_lat', 'point_estime_lng'),
                'point_dynamique_proche',
                'segment_touche',
                'distance_sur_segment'
            )
        }),
        ('Diagnostic', {
            'fields': ('description_diagnostic',)
        }),
        ('Dates', {
            'fields': ('date_detection', 'date_resolution')
        }),
        ('Notifications', {
            'fields': ('superviseur_notifie', 'client_notifie')
        }),
    )
    
    readonly_fields = ('date_detection',)

# ===============================
# Admins pour les interventions
# ===============================

class CommitInterventionInline(admin.TabularInline):
    model = CommitIntervention
    extra = 0
    fields = ('message_commit', 'auteur', 'date_commit')
    readonly_fields = ('hash_commit', 'date_commit')

@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('type_intervention', 'liaison', 'status', 'technicien_principal', 'date_planifiee')
    list_filter = ('type_intervention', 'status', 'date_planifiee')
    search_fields = ('description', 'liaison__nom_liaison', 'technicien_principal__username')
    ordering = ('-date_planifiee',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('type_intervention', 'status', 'liaison', 'coupure', 'fat')
        }),
        ('Personnel', {
            'fields': ('technicien_principal', 'techniciens_secondaires')
        }),
        ('Planification', {
            'fields': ('date_planifiee', 'duree_estimee', 'date_debut', 'date_fin')
        }),
        ('Description', {
            'fields': ('description', 'resume_changement', 'materiel_utilise')
        }),
        ('Rapport', {
            'fields': ('rapport_final', 'photos_avant', 'photos_apres')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CommitInterventionInline]
    filter_horizontal = ('techniciens_secondaires', 'photos_avant', 'photos_apres')

@admin.register(CommitIntervention)
class CommitInterventionAdmin(admin.ModelAdmin):
    list_display = ('intervention', 'message_commit', 'auteur', 'date_commit', 'hash_commit_short')
    list_filter = ('date_commit', 'auteur')
    search_fields = ('message_commit', 'description_detaillee', 'intervention__description')
    ordering = ('-date_commit',)
    
    readonly_fields = ('hash_commit', 'date_commit')
    
    def hash_commit_short(self, obj):
        return obj.hash_commit[:8] if obj.hash_commit else ''
    hash_commit_short.short_description = 'Hash (court)'

# ===============================
# Admins pour les fiches techniques
# ===============================

@admin.register(FicheTechnique)
class FicheTechniqueAdmin(admin.ModelAdmin):
    list_display = ('point_dynamique', 'modele_equipement', 'fabricant', 'numero_serie', 'date_installation')
    list_filter = ('fabricant', 'date_installation', 'created_at')
    search_fields = ('modele_equipement', 'numero_serie', 'fabricant', 'point_dynamique__nom')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Point dynamique', {
            'fields': ('point_dynamique',)
        }),
        ('Informations équipement', {
            'fields': ('modele_equipement', 'numero_serie', 'fabricant', 'date_installation')
        }),
        ('Spécifications', {
            'fields': ('specifications_json',),
            'classes': ('collapse',)
        }),
        ('Documentation', {
            'fields': ('manuel_url', 'notes_maintenance')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')

# ===============================
# Admins pour les notifications
# ===============================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_notification', 'priorite', 'destinataire', 'lue', 'created_at')
    list_filter = ('type_notification', 'priorite', 'lue', 'created_at')
    search_fields = ('titre', 'message', 'destinataire__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Notification', {
            'fields': ('type_notification', 'priorite', 'titre', 'message')
        }),
        ('Destinataire', {
            'fields': ('destinataire',)
        }),
        ('Objets concernés', {
            'fields': ('liaison_concernee', 'coupure_concernee', 'intervention_concernee'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('lue', 'date_lecture')
        }),
    )
    
    readonly_fields = ('created_at', 'date_lecture')

# ===============================
# Admins pour les paramètres
# ===============================

@admin.register(ParametreApplication)
class ParametreApplicationAdmin(admin.ModelAdmin):
    list_display = ('type_parametre', 'cle', 'valeur_courte', 'created_at')
    list_filter = ('type_parametre', 'created_at')
    search_fields = ('cle', 'valeur', 'description')
    ordering = ('type_parametre', 'cle')
    
    fieldsets = (
        ('Paramètre', {
            'fields': ('type_parametre', 'cle', 'valeur')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def valeur_courte(self, obj):
        return obj.valeur[:50] + '...' if len(obj.valeur) > 50 else obj.valeur
    valeur_courte.short_description = 'Valeur'

# ===============================
# Configuration du site admin
# ===============================

admin.site.site_header = "FiberMap Administration"
admin.site.site_title = "FiberMap Admin"
admin.site.index_title = "Gestion du réseau fibre optique"