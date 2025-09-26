from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Client, Liaison, TypeLiaison, PointDynamique, Segment,
    DetailONT, DetailPOPLS, DetailPOPFTTH, DetailChambre, DetailManchon, 
    FAT, DetailFDT, PhotoPoint, MesureOTDR, Coupure, Intervention, 
    CommitIntervention, FicheTechnique, Notification, ParametreApplication,
    COULEUR_CHOICES, CAPACITE_CABLE_CHOICES, CONNECTEUR_CHOICES
)

# ========================
# SERIALIZERS UTILISATEUR
# ========================

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'phone', 'location', 'password', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserPublicSerializer(serializers.ModelSerializer):
    """Version publique sans informations sensibles"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'role']

# ========================
# SERIALIZERS CLIENT
# ========================

class ClientSerializer(serializers.ModelSerializer):
    liaisons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = '__all__'

    def get_liaisons_count(self, obj):
        return obj.liaisons.count()

class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de clients avec validation du type"""
    class Meta:
        model = Client
        fields = '__all__'

    def validate(self, data):
        if data['type_client'] == 'FTTH':
            if not data.get('numero_ligne') or not data.get('nom_ligne'):
                raise serializers.ValidationError(
                    "Les champs numero_ligne et nom_ligne sont obligatoires pour les clients FTTH"
                )
        return data

# ========================
# SERIALIZERS LIAISON
# ========================

class TypeLiaisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeLiaison
        fields = '__all__'

class SegmentSerializer(serializers.ModelSerializer):
    point_depart_nom = serializers.CharField(source='point_depart.nom', read_only=True)
    point_arrivee_nom = serializers.CharField(source='point_arrivee.nom', read_only=True)
    
    class Meta:
        model = Segment
        fields = '__all__'

class LiaisonListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    type_liaison_display = serializers.CharField(source='type_liaison.get_type_display', read_only=True)
    points_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Liaison
        fields = ['id', 'nom_liaison', 'client_name', 'type_liaison_display', 
                 'status', 'distance_totale', 'points_count', 'created_at']

    def get_points_count(self, obj):
        return obj.points_dynamiques.count()

class LiaisonDetailSerializer(serializers.ModelSerializer):
    """Serializer complet avec toutes les relations"""
    client = ClientSerializer(read_only=True)
    type_liaison = TypeLiaisonSerializer(read_only=True)
    created_by = UserPublicSerializer(read_only=True)
    segments = SegmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Liaison
        fields = '__all__'

class LiaisonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liaison
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

# ========================
# SERIALIZERS POINTS DYNAMIQUES
# ========================

class DetailONTSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailONT
        fields = '__all__'

class DetailPOPLSSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailPOPLS
        fields = '__all__'

class DetailPOPFTTHSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailPOPFTTH
        fields = '__all__'

class DetailChambreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailChambre
        fields = '__all__'

class DetailManchonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailManchon
        fields = '__all__'

class DetailFDTSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailFDT
        fields = '__all__'

class PhotoPointSerializer(serializers.ModelSerializer):
    uploaded_by = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = PhotoPoint
        fields = '__all__'

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)

class PointDynamiqueListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes"""
    type_point_display = serializers.CharField(source='get_type_point_display', read_only=True)
    photos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PointDynamique
        fields = ['id', 'nom', 'type_point', 'type_point_display', 'ordre',
                 'latitude', 'longitude', 'distance_depuis_central', 'photos_count']

    def get_photos_count(self, obj):
        return obj.photos.count()

class PointDynamiqueDetailSerializer(serializers.ModelSerializer):
    """Serializer complet avec détails spécifiques selon le type"""
    liaison_nom = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    type_point_display = serializers.CharField(source='get_type_point_display', read_only=True)
    photos = PhotoPointSerializer(many=True, read_only=True)
    
    # Détails spécifiques (optionnels selon le type)
    detail_ont = DetailONTSerializer(read_only=True)
    detail_pop_ls = DetailPOPLSSerializer(read_only=True)
    detail_pop_ftth = DetailPOPFTTHSerializer(read_only=True)
    detail_chambre = DetailChambreSerializer(read_only=True)
    detail_manchon = DetailManchonSerializer(read_only=True)
    detail_fdt = DetailFDTSerializer(read_only=True)
    detail_fat = serializers.SerializerMethodField()
    
    class Meta:
        model = PointDynamique
        fields = '__all__'

    def get_detail_fat(self, obj):
        try:
            if hasattr(obj, 'detail_fat') and obj.detail_fat:
                return FATSerializer(obj.detail_fat).data
        except:
            pass
        return None

class PointDynamiqueCreateSerializer(serializers.ModelSerializer):
    # Détails spécifiques selon le type (optionnels lors de la création)
    detail_ont = DetailONTSerializer(required=False)
    detail_pop_ls = DetailPOPLSSerializer(required=False)
    detail_pop_ftth = DetailPOPFTTHSerializer(required=False)
    detail_chambre = DetailChambreSerializer(required=False)
    detail_manchon = DetailManchonSerializer(required=False)
    detail_fdt = DetailFDTSerializer(required=False)
    
    class Meta:
        model = PointDynamique
        fields = '__all__'

    def create(self, validated_data):
        # Extraire les détails spécifiques
        detail_ont_data = validated_data.pop('detail_ont', None)
        detail_pop_ls_data = validated_data.pop('detail_pop_ls', None)
        detail_pop_ftth_data = validated_data.pop('detail_pop_ftth', None)
        detail_chambre_data = validated_data.pop('detail_chambre', None)
        detail_manchon_data = validated_data.pop('detail_manchon', None)
        detail_fdt_data = validated_data.pop('detail_fdt', None)
        
        # Créer le point dynamique
        point = PointDynamique.objects.create(**validated_data)
        
        # Créer les détails selon le type
        if detail_ont_data and point.type_point == 'ONT':
            DetailONT.objects.create(point_dynamique=point, **detail_ont_data)
        elif detail_pop_ls_data and point.type_point == 'POP_LS':
            DetailPOPLS.objects.create(point_dynamique=point, **detail_pop_ls_data)
        elif detail_pop_ftth_data and point.type_point == 'POP_FTTH':
            DetailPOPFTTH.objects.create(point_dynamique=point, **detail_pop_ftth_data)
        elif detail_chambre_data and point.type_point == 'chambre':
            DetailChambre.objects.create(point_dynamique=point, **detail_chambre_data)
        elif detail_manchon_data and point.type_point in ['manchon', 'manchon_aerien']:
            DetailManchon.objects.create(point_dynamique=point, **detail_manchon_data)
        elif detail_fdt_data and point.type_point == 'FDT':
            DetailFDT.objects.create(point_dynamique=point, **detail_fdt_data)
        
        return point

# ========================
# SERIALIZERS FAT
# ========================

class FATSerializer(serializers.ModelSerializer):
    liaison_nom = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    point_dynamique_nom = serializers.CharField(source='point_dynamique.nom', read_only=True)
    
    class Meta:
        model = FAT
        fields = '__all__'

class FATCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAT
        fields = '__all__'

# ========================
# SERIALIZERS MESURES ET DIAGNOSTICS
# ========================

class MesureOTDRSerializer(serializers.ModelSerializer):
    liaison_nom = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    technicien_nom = serializers.CharField(source='technicien.get_full_name', read_only=True)
    point_mesure_nom = serializers.CharField(source='point_mesure.nom', read_only=True)
    
    class Meta:
        model = MesureOTDR
        fields = '__all__'

class MesureOTDRCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MesureOTDR
        fields = '__all__'

    def create(self, validated_data):
        validated_data['technicien'] = self.context['request'].user
        return super().create(validated_data)

class CoupureSerializer(serializers.ModelSerializer):
    liaison_nom = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    mesure_otdr = MesureOTDRSerializer(read_only=True)
    point_dynamique_proche_nom = serializers.CharField(source='point_dynamique_proche.nom', read_only=True)
    segment_touche_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Coupure
        fields = '__all__'

    def get_segment_touche_info(self, obj):
        if obj.segment_touche:
            return {
                'id': obj.segment_touche.id,
                'depart': obj.segment_touche.point_depart.nom,
                'arrivee': obj.segment_touche.point_arrivee.nom,
                'distance_cable': obj.segment_touche.distance_cable
            }
        return None

# ========================
# SERIALIZERS INTERVENTIONS
# ========================

class CommitInterventionSerializer(serializers.ModelSerializer):
    auteur = UserPublicSerializer(read_only=True)
    
    class Meta:
        model = CommitIntervention
        fields = '__all__'

class InterventionListSerializer(serializers.ModelSerializer):
    """Serializer allégé pour les listes"""
    technicien_principal_nom = serializers.CharField(source='technicien_principal.get_full_name', read_only=True)
    liaison_nom = serializers.CharField(source='liaison.nom_liaison', read_only=True)
    fat_numero = serializers.CharField(source='fat.numero_fat', read_only=True)
    commits_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Intervention
        fields = ['id', 'type_intervention', 'status', 'technicien_principal_nom',
                 'liaison_nom', 'fat_numero', 'date_planifiee', 'commits_count']

    def get_commits_count(self, obj):
        return obj.commits.count()

class InterventionDetailSerializer(serializers.ModelSerializer):
    """Serializer complet"""
    technicien_principal = UserPublicSerializer(read_only=True)
    techniciens_secondaires = UserPublicSerializer(many=True, read_only=True)
    liaison = LiaisonListSerializer(read_only=True)
    fat = FATSerializer(read_only=True)
    coupure = CoupureSerializer(read_only=True)
    commits = CommitInterventionSerializer(many=True, read_only=True)
    photos_avant = PhotoPointSerializer(many=True, read_only=True)
    photos_apres = PhotoPointSerializer(many=True, read_only=True)
    
    class Meta:
        model = Intervention
        fields = '__all__'

class InterventionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intervention
        fields = '__all__'

# ========================
# SERIALIZERS FICHES TECHNIQUES
# ========================

class FicheTechniqueSerializer(serializers.ModelSerializer):
    point_dynamique = PointDynamiqueListSerializer(read_only=True)
    
    class Meta:
        model = FicheTechnique
        fields = '__all__'

# ========================
# SERIALIZERS NOTIFICATIONS
# ========================

class NotificationSerializer(serializers.ModelSerializer):
    destinataire = UserPublicSerializer(read_only=True)
    liaison_concernee = LiaisonListSerializer(read_only=True)
    coupure_concernee = CoupureSerializer(read_only=True)
    intervention_concernee = InterventionListSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

# ========================
# SERIALIZERS PARAMÈTRES
# ========================

class ParametreApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParametreApplication
        fields = '__all__'

# ========================
# SERIALIZERS CARTE ET NAVIGATION
# ========================

class LiaisonCarteSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour l'affichage carte"""
    client_name = serializers.CharField(source='client.name')
    type_liaison_code = serializers.CharField(source='type_liaison.type')
    points_dynamiques = PointDynamiqueListSerializer(many=True, read_only=True)
    segments = SegmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Liaison
        fields = ['id', 'nom_liaison', 'client_name', 'type_liaison_code', 'status',
                 'point_central_lat', 'point_central_lng', 'point_client_lat', 
                 'point_client_lng', 'distance_totale', 'points_dynamiques', 'segments']

class CoupureCarteSerializer(serializers.ModelSerializer):
    """Serializer optimisé pour l'affichage des coupures sur carte"""
    liaison_nom = serializers.CharField(source='liaison.nom_liaison')
    client_name = serializers.CharField(source='liaison.client.name')
    
    class Meta:
        model = Coupure
        fields = ['id', 'liaison_nom', 'client_name', 'status', 'point_estime_lat', 
                 'point_estime_lng', 'date_detection', 'description_diagnostic']

# ========================
# SERIALIZERS AUTHENTIFICATION
# ========================

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                              username=username, password=password)
            if not user:
                raise serializers.ValidationError('Identifiants invalides.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Username et password requis.')

# ========================
# SERIALIZERS CHOIX
# ========================

class ChoixSerializer(serializers.Serializer):
    """Serializer pour les choix de l'application"""
    couleurs = serializers.SerializerMethodField()
    capacites_cable = serializers.SerializerMethodField()
    connecteurs = serializers.SerializerMethodField()
    types_points = serializers.SerializerMethodField()
    
    def get_couleurs(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in COULEUR_CHOICES]
    
    def get_capacites_cable(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in CAPACITE_CABLE_CHOICES]
    
    def get_connecteurs(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in CONNECTEUR_CHOICES]
    
    def get_types_points(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in PointDynamique.TYPE_CHOICES]

# ========================
# SERIALIZERS STATISTIQUES
# ========================

class StatistiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques générales"""
    total_liaisons = serializers.IntegerField()
    liaisons_actives = serializers.IntegerField()
    liaisons_en_panne = serializers.IntegerField()
    total_points_dynamiques = serializers.IntegerField()
    total_interventions = serializers.IntegerField()
    interventions_en_cours = serializers.IntegerField()
    coupures_detectees = serializers.IntegerField()
    coupures_reparees = serializers.IntegerField()

# ========================
# SERIALIZERS RECHERCHE
# ========================

class RechercheGlobaleSerializer(serializers.Serializer):
    """Serializer pour les résultats de recherche globale"""
    query = serializers.CharField()
    liaisons = LiaisonListSerializer(many=True, read_only=True)
    clients = ClientSerializer(many=True, read_only=True)
    points_dynamiques = PointDynamiqueListSerializer(many=True, read_only=True)
    fats = FATSerializer(many=True, read_only=True)
    interventions = InterventionListSerializer(many=True, read_only=True)