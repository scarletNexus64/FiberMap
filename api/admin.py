from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Client, TypeLiaison, Liaison, PointDynamique, PhotoPoint,
    MesureOTDR, Coupure, Intervention, CommitIntervention, FicheTechnique,
    Notification, ParametreApplication
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
    fields = ('nom', 'type_point', 'latitude', 'longitude', 'distance_depuis_central', 'presence_splitter')
    readonly_fields = ('created_at', 'updated_at')


class PhotoPointInline(admin.TabularInline):
    model = PhotoPoint
    extra = 0
    fields = ('image', 'description', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class InterventionInline(admin.TabularInline):
    model = Intervention
    extra = 0
    fields = ('type_intervention', 'status', 'technicien_principal', 'date_planifiee')
    readonly_fields = ('created_at',)


class CommitInterventionInline(admin.TabularInline):
    model = CommitIntervention
    extra = 0
    fields = ('message_commit', 'auteur', 'date_commit', 'hash_commit')
    readonly_fields = ('hash_commit', 'date_commit')


# ===============================
# Admin classes principales
# ===============================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin pour les clients"""
    list_display = ('name', 'type', 'phone', 'email', 'liaisons_count', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'phone', 'email', 'address')
    ordering = ('name',)
    
    def liaisons_count(self, obj):
        count = obj.liaisons.count()
        if count > 0:
            url = reverse('admin:api_liaison_changelist') + f'?client__id__exact={obj.id}'
            return format_html('<a href="{}">{} liaisons</a>', url, count)
        return '0 liaison'
    liaisons_count.short_description = 'Liaisons'


@admin.register(TypeLiaison)
class TypeLiaisonAdmin(admin.ModelAdmin):
    """Admin pour les types de liaisons"""
    list_display = ('type', 'description')
    list_filter = ('type',)
    search_fields = ('type', 'description')


@admin.register(Liaison)
class LiaisonAdmin(admin.ModelAdmin):
    """Admin pour les liaisons"""
    list_display = ('nom_liaison', 'client', 'type_liaison', 'status', 'distance_totale', 'created_by', 'created_at')
    list_filter = ('status', 'type_liaison', 'created_at', 'created_by')
    search_fields = ('nom_liaison', 'client__name')
    ordering = ('-created_at',)
    inlines = [PointDynamiqueInline, InterventionInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom_liaison', 'client', 'type_liaison', 'status', 'distance_totale', 'created_by')
        }),
        ('Coordonnées géographiques', {
            'fields': (
                ('point_central_lat', 'point_central_lng'),
                ('point_client_lat', 'point_client_lng')
            )
        }),
        ('Spécifications techniques LS', {
            'fields': ('convertisseur_central', 'convertisseur_client', 'type_connectique'),
            'classes': ('collapse',)
        }),
        ('Spécifications techniques GPON', {
            'fields': ('olt_source', 'port_olt'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'type_liaison', 'created_by')


@admin.register(PointDynamique)
class PointDynamiqueAdmin(admin.ModelAdmin):
    """Admin pour les points dynamiques"""
    list_display = ('nom', 'type_point', 'liaison', 'distance_depuis_central', 'presence_splitter', 'photos_count')
    list_filter = ('type_point', 'presence_splitter', 'liaison__type_liaison', 'created_at')
    search_fields = ('nom', 'description', 'liaison__nom_liaison')
    ordering = ('liaison', 'distance_depuis_central')
    inlines = [PhotoPointInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('liaison', 'nom', 'type_point', 'description')
        }),
        ('Position', {
            'fields': (
                ('latitude', 'longitude'),
                'distance_depuis_central'
            )
        }),
        ('Informations techniques', {
            'fields': (
                'type_armoire',
                ('presence_splitter', 'ratio_splitter'),
                ('port_utilise', 'type_distribution')
            )
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def photos_count(self, obj):
        count = obj.photos.count()
        if count > 0:
            url = reverse('admin:api_photopoint_changelist') + f'?point_dynamique__id__exact={obj.id}'
            return format_html('<a href="{}">{} photos</a>', url, count)
        return '0 photo'
    photos_count.short_description = 'Photos'


@admin.register(PhotoPoint)
class PhotoPointAdmin(admin.ModelAdmin):
    """Admin pour les photos des points"""
    list_display = ('point_dynamique', 'description', 'uploaded_by', 'uploaded_at', 'image_preview')
    list_filter = ('uploaded_at', 'point_dynamique__type_point')
    search_fields = ('description', 'point_dynamique__nom')
    ordering = ('-uploaded_at',)
    
    readonly_fields = ('uploaded_at', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />', obj.image.url)
        return 'Pas d\'image'
    image_preview.short_description = 'Aperçu'


@admin.register(MesureOTDR)
class MesureOTDRAdmin(admin.ModelAdmin):
    """Admin pour les mesures OTDR"""
    list_display = ('liaison', 'type_evenement', 'distance_coupure', 'attenuation', 'technicien', 'date_mesure')
    list_filter = ('type_evenement', 'date_mesure', 'technicien')
    search_fields = ('liaison__nom_liaison', 'commentaires')
    ordering = ('-date_mesure',)
    
    fieldsets = (
        ('Liaison', {
            'fields': ('liaison', 'technicien')
        }),
        ('Mesures', {
            'fields': (
                'type_evenement',
                ('distance_coupure', 'attenuation'),
                'commentaires'
            )
        }),
        ('Fichier', {
            'fields': ('fichier_otdr',)
        }),
    )
    
    readonly_fields = ('date_mesure',)


@admin.register(Coupure)
class CoupureAdmin(admin.ModelAdmin):
    """Admin pour les coupures"""
    list_display = ('liaison', 'status', 'date_detection', 'date_resolution', 'superviseur_notifie', 'client_notifie', 'voir_carte')
    list_filter = ('status', 'date_detection', 'superviseur_notifie', 'client_notifie')
    search_fields = ('liaison__nom_liaison', 'description_diagnostic')
    ordering = ('-date_detection',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('liaison', 'mesure_otdr', 'status', 'description_diagnostic')
        }),
        ('Localisation', {
            'fields': (
                ('point_estime_lat', 'point_estime_lng'),
                'point_dynamique_proche'
            )
        }),
        ('Dates', {
            'fields': ('date_detection', 'date_resolution')
        }),
        ('Notifications', {
            'fields': ('superviseur_notifie', 'client_notifie')
        }),
    )
    
    readonly_fields = ('date_detection',)
    
    def voir_carte(self, obj):
        if obj.point_estime_lat and obj.point_estime_lng:
            url = f"https://www.google.com/maps/@{obj.point_estime_lat},{obj.point_estime_lng},15z"
            return format_html('<a href="{}" target="_blank">🗺️ Voir sur carte</a>', url)
        return 'Position non calculée'
    voir_carte.short_description = 'Carte'


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    """Admin pour les interventions"""
    list_display = ('liaison', 'type_intervention', 'status', 'technicien_principal', 'date_planifiee', 'date_debut', 'date_fin')
    list_filter = ('type_intervention', 'status', 'date_planifiee', 'technicien_principal')
    search_fields = ('liaison__nom_liaison', 'description', 'resume_changement')
    ordering = ('-date_planifiee',)
    inlines = [CommitInterventionInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('liaison', 'coupure', 'type_intervention', 'status')
        }),
        ('Personnel', {
            'fields': ('technicien_principal', 'techniciens_secondaires')
        }),
        ('Planification', {
            'fields': (
                'date_planifiee',
                ('date_debut', 'date_fin'),
                'duree_estimee'
            )
        }),
        ('Description', {
            'fields': ('description', 'resume_changement', 'materiel_utilise')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('techniciens_secondaires',)


@admin.register(CommitIntervention)
class CommitInterventionAdmin(admin.ModelAdmin):
    """Admin pour les commits d'intervention"""
    list_display = ('intervention', 'message_commit', 'auteur', 'date_commit', 'hash_commit_short')
    list_filter = ('date_commit', 'auteur')
    search_fields = ('message_commit', 'description_detaillee', 'intervention__liaison__nom_liaison')
    ordering = ('-date_commit',)
    
    readonly_fields = ('hash_commit', 'date_commit')
    
    def hash_commit_short(self, obj):
        return obj.hash_commit[:8] if obj.hash_commit else ''
    hash_commit_short.short_description = 'Hash (court)'


@admin.register(FicheTechnique)
class FicheTechniqueAdmin(admin.ModelAdmin):
    """Admin pour les fiches techniques"""
    list_display = ('point_dynamique', 'modele_equipement', 'fabricant', 'numero_serie', 'date_installation')
    list_filter = ('fabricant', 'date_installation', 'created_at')
    search_fields = ('modele_equipement', 'numero_serie', 'fabricant', 'point_dynamique__nom')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Point associé', {
            'fields': ('point_dynamique',)
        }),
        ('Informations équipement', {
            'fields': (
                ('modele_equipement', 'fabricant'),
                ('numero_serie', 'date_installation')
            )
        }),
        ('Spécifications', {
            'fields': ('specifications_json',)
        }),
        ('Documentation', {
            'fields': ('manuel_url', 'notes_maintenance')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin pour les notifications"""
    list_display = ('destinataire', 'type_notification', 'titre', 'lue', 'date_creation', 'date_lecture')
    list_filter = ('type_notification', 'lue', 'date_creation')
    search_fields = ('titre', 'message', 'destinataire__username')
    ordering = ('-date_creation',)
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('destinataire', 'type_notification')
        }),
        ('Contenu', {
            'fields': ('titre', 'message')
        }),
        ('Objets liés', {
            'fields': ('liaison', 'coupure', 'intervention')
        }),
        ('État', {
            'fields': ('lue', 'date_creation', 'date_lecture')
        }),
    )
    
    readonly_fields = ('date_creation',)


@admin.register(ParametreApplication)
class ParametreApplicationAdmin(admin.ModelAdmin):
    """Admin pour les paramètres d'application"""
    list_display = ('cle', 'valeur_preview', 'type_donnee', 'description_short', 'updated_at')
    list_filter = ('type_donnee', 'created_at', 'updated_at')
    search_fields = ('cle', 'valeur', 'description')
    ordering = ('cle',)
    
    fieldsets = (
        ('Paramètre', {
            'fields': ('cle', 'type_donnee')
        }),
        ('Valeur', {
            'fields': ('valeur',)
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def valeur_preview(self, obj):
        if len(obj.valeur) > 50:
            return obj.valeur[:50] + '...'
        return obj.valeur
    valeur_preview.short_description = 'Valeur'
    
    def description_short(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        return obj.description
    description_short.short_description = 'Description'


# ===============================
# Configuration du site admin
# ===============================

admin.site.site_header = "FiberMap Administration"
admin.site.site_title = "FiberMap Admin"
admin.site.index_title = "Gestion du réseau fibre optique"