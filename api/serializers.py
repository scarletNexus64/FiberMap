from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Client, TypeLiaison, Liaison, PointDynamique, PhotoPoint,
    MesureOTDR, Coupure, Intervention, CommitIntervention, FicheTechnique,
    Notification, ParametreApplication
)


# ===============================
# Serializers d'authentification
# ===============================

class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs"""
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'phone', 'location', 'created_at', 'updated_at', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    username = serializers.CharField()
    password = serializers.CharField()


# ===============================
# Serializers métier
# ===============================

class ClientSerializer(serializers.ModelSerializer):
    """Serializer pour les clients"""
    liaisons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'type', 'address', 'phone', 'email', 
                 'created_at', 'liaisons_count']
        read_only_fields = ['created_at']
    
    def get_liaisons_count(self, obj):
        return obj.liaisons.count()


class TypeLiaisonSerializer(serializers.ModelSerializer):
    """Serializer pour les types de liaisons"""
    
    class Meta:
        model = TypeLiaison
        fields = ['id', 'type', 'description']


class PointDynamiqueSerializer(serializers.ModelSerializer):
    """Serializer pour les points dynamiques"""
    photos_count = serializers.SerializerMethodField()
    has_fiche_technique = serializers.SerializerMethodField()
    
    class Meta:
        model = PointDynamique
        fields = ['id', 'liaison', 'type_point', 'nom', 'latitude', 'longitude',
                 'distance_depuis_central', 'description', 'type_armoire',
                 'presence_splitter', 'ratio_splitter', 'port_utilise',
                 'type_distribution', 'created_at', 'updated_at',
                 'photos_count', 'has_fiche_technique']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_photos_count(self, obj):
        return obj.photos.count()
    
    def get_has_fiche_technique(self, obj):
        return hasattr(obj, 'fichetechnique')


class PhotoPointSerializer(serializers.ModelSerializer):
    """Serializer pour les photos des points"""
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PhotoPoint
        fields = ['id', 'point_dynamique', 'image', 'description',
                 'uploaded_by', 'uploaded_at', 'uploaded_by_name']
        read_only_fields = ['uploaded_at']
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class LiaisonSerializer(serializers.ModelSerializer):
    """Serializer de base pour les liaisons"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    type_liaison_display = serializers.CharField(source='type_liaison.get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    points_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Liaison
        fields = ['id', 'client', 'client_name', 'type_liaison', 'type_liaison_display',
                 'nom_liaison', 'point_central_lat', 'point_central_lng',
                 'point_client_lat', 'point_client_lng', 'status', 'status_display',
                 'distance_totale', 'convertisseur_central', 'convertisseur_client',
                 'type_connectique', 'olt_source', 'port_olt', 'created_at',
                 'updated_at', 'created_by', 'created_by_name', 'points_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
    
    def get_points_count(self, obj):
        return obj.points_dynamiques.count()


class LiaisonDetailSerializer(LiaisonSerializer):
    """Serializer détaillé pour les liaisons avec points dynamiques"""
    points_dynamiques = PointDynamiqueSerializer(many=True, read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    type_liaison_details = TypeLiaisonSerializer(source='type_liaison', read_only=True)
    interventions_count = serializers.SerializerMethodField()
    coupures_actives_count = serializers.SerializerMethodField()
    
    class Meta(LiaisonSerializer.Meta):
        fields = LiaisonSerializer.Meta.fields + [
            'points_dynamiques', 'client_details', 'type_liaison_details',
            'interventions_count', 'coupures_actives_count'
        ]
    
    def get_interventions_count(self, obj):
        return obj.interventions.count()
    
    def get_coupures_actives_count(self, obj):
        return obj.coupures.filter(status__in=['detectee', 'en_cours']).count()


class LiaisonMapSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour l'affichage sur carte"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    type_display = serializers.CharField(source='type_liaison.type', read_only=True)
    
    class Meta:
        model = Liaison
        fields = ['id', 'nom_liaison', 'client_name', 'type_display', 'status',
                 'point_central_lat', 'point_central_lng', 'point_client_lat',
                 'point_client_lng', 'distance_totale']


# ===============================
# Serializers diagnostic
# ===============================

class MesureOTDRSerializer(serializers.ModelSerializer):
    """Serializer pour les mesures OTDR"""
    technicien_name = serializers.SerializerMethodField()
    liaison_name = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    
    class Meta:
        model = MesureOTDR
        fields = ['id', 'liaison', 'liaison_name', 'distance_coupure', 'attenuation',
                 'type_evenement', 'technicien', 'technicien_name', 'date_mesure',
                 'commentaires', 'fichier_otdr']
        read_only_fields = ['date_mesure']
    
    def get_technicien_name(self, obj):
        return obj.technicien.get_full_name() if obj.technicien else None


class CoupureSerializer(serializers.ModelSerializer):
    """Serializer pour les coupures"""
    liaison_name = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    client_name = serializers.CharField(source='liaison.client.name', read_only=True)
    mesure_otdr_details = MesureOTDRSerializer(source='mesure_otdr', read_only=True)
    point_dynamique_proche_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Coupure
        fields = ['id', 'liaison', 'liaison_name', 'client_name', 'mesure_otdr',
                 'mesure_otdr_details', 'point_estime_lat', 'point_estime_lng',
                 'point_dynamique_proche', 'point_dynamique_proche_name',
                 'status', 'status_display', 'description_diagnostic',
                 'date_detection', 'date_resolution', 'superviseur_notifie',
                 'client_notifie']
        read_only_fields = ['date_detection']
    
    def get_point_dynamique_proche_name(self, obj):
        return obj.point_dynamique_proche.nom if obj.point_dynamique_proche else None


# ===============================
# Serializers interventions
# ===============================

class CommitInterventionSerializer(serializers.ModelSerializer):
    """Serializer pour les commits d'intervention"""
    auteur_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CommitIntervention
        fields = ['id', 'intervention', 'message_commit', 'description_detaillee',
                 'hash_commit', 'changements_json', 'auteur', 'auteur_name',
                 'date_commit', 'etat_avant', 'etat_apres']
        read_only_fields = ['hash_commit', 'date_commit']
    
    def get_auteur_name(self, obj):
        return obj.auteur.get_full_name() if obj.auteur else None


class InterventionSerializer(serializers.ModelSerializer):
    """Serializer pour les interventions"""
    liaison_name = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    client_name = serializers.CharField(source='liaison.client.name', read_only=True)
    technicien_principal_name = serializers.SerializerMethodField()
    techniciens_secondaires_names = serializers.SerializerMethodField()
    coupure_details = CoupureSerializer(source='coupure', read_only=True)
    commits_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_intervention_display', read_only=True)
    
    class Meta:
        model = Intervention
        fields = ['id', 'liaison', 'liaison_name', 'client_name', 'coupure',
                 'coupure_details', 'type_intervention', 'type_display', 'status',
                 'status_display', 'technicien_principal', 'technicien_principal_name',
                 'techniciens_secondaires', 'techniciens_secondaires_names',
                 'date_planifiee', 'date_debut', 'date_fin', 'duree_estimee',
                 'description', 'resume_changement', 'materiel_utilise',
                 'created_at', 'updated_at', 'commits_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_technicien_principal_name(self, obj):
        return obj.technicien_principal.get_full_name()
    
    def get_techniciens_secondaires_names(self, obj):
        return [tech.get_full_name() for tech in obj.techniciens_secondaires.all()]
    
    def get_commits_count(self, obj):
        return obj.commits.count()


class InterventionPlanningSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour le planning des techniciens"""
    liaison_name = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    client_name = serializers.CharField(source='liaison.client.name', read_only=True)
    
    class Meta:
        model = Intervention
        fields = ['id', 'liaison_name', 'client_name', 'type_intervention',
                 'status', 'date_planifiee', 'date_debut', 'date_fin',
                 'duree_estimee', 'description']


# ===============================
# Serializers techniques
# ===============================

class FicheTechniqueSerializer(serializers.ModelSerializer):
    """Serializer pour les fiches techniques"""
    point_dynamique_name = serializers.CharField(source='point_dynamique.nom', read_only=True)
    
    class Meta:
        model = FicheTechnique
        fields = ['id', 'point_dynamique', 'point_dynamique_name', 'modele_equipement',
                 'numero_serie', 'fabricant', 'date_installation', 'specifications_json',
                 'manuel_url', 'notes_maintenance', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# ===============================
# Serializers notifications
# ===============================

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    destinataire_name = serializers.SerializerMethodField()
    liaison_name = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    type_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'destinataire', 'destinataire_name', 'type_notification',
                 'type_display', 'titre', 'message', 'liaison', 'liaison_name',
                 'coupure', 'intervention', 'lue', 'date_creation', 'date_lecture']
        read_only_fields = ['date_creation']
    
    def get_destinataire_name(self, obj):
        return obj.destinataire.get_full_name()


class ParametreApplicationSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres d'application"""
    
    class Meta:
        model = ParametreApplication
        fields = ['id', 'cle', 'valeur', 'description', 'type_donnee',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_cle(self, value):
        """Valider que la clé est unique lors de la création"""
        if self.instance is None:  # Création
            if ParametreApplication.objects.filter(cle=value).exists():
                raise serializers.ValidationError("Cette clé existe déjà")
        else:  # Modification
            if ParametreApplication.objects.filter(cle=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Cette clé existe déjà")
        return value
    
    def validate_valeur(self, value):
        """Valider la valeur selon le type de données"""
        type_donnee = self.initial_data.get('type_donnee')
        
        if type_donnee == 'integer':
            try:
                int(value)
            except ValueError:
                raise serializers.ValidationError("La valeur doit être un entier")
        elif type_donnee == 'float':
            try:
                float(value)
            except ValueError:
                raise serializers.ValidationError("La valeur doit être un nombre décimal")
        elif type_donnee == 'boolean':
            if value.lower() not in ['true', 'false', '1', '0']:
                raise serializers.ValidationError("La valeur doit être true/false ou 1/0")
        elif type_donnee == 'json':
            import json
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("La valeur doit être un JSON valide")
        
        return value