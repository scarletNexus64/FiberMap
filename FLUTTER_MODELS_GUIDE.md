# Guide des Modèles Flutter - FiberMap

## 🎯 Modèles Basés sur les Exigences wa.md

Cette documentation détaille tous les modèles Flutter nécessaires pour implémenter les exigences spécifiées dans le fichier wa.md.

## 📋 Structure des Types de Points Dynamiques

### 1. Énumérations et Constantes
```dart
// lib/core/constants/fiber_constants.dart

enum TypePointDynamique {
  ont('ONT', 'ONT (Optical Network Terminal)'),
  popLs('POP_LS', 'POP LS (Point of Presence LS)'),
  popFtth('POP_FTTH', 'POP FTTH (Point of Presence FTTH)'),
  chambre('chambre', 'Chambre de tirage'),
  manchon('manchon', 'Manchon'),
  manchonAerien('manchon_aerien', 'Manchon aérien/distribution'),
  fat('FAT', 'FAT (Fiber Access Terminal)'),
  fdt('FDT', 'FDT (Fiber Distribution Terminal)');

  const TypePointDynamique(this.value, this.label);
  final String value;
  final String label;
}

enum CouleurFibre {
  blue('blue', 'Bleu'),
  orange('orange', 'Orange'),
  vert('vert', 'Vert'),
  marron('maron', 'Marron'),
  gris('gris', 'Gris'),
  blanc('blanc', 'Blanc'),
  rouge('rouge', 'Rouge'),
  noir('noir', 'Noir'),
  jaune('jaune', 'Jaune'),
  violet('violet', 'Violet'),
  rose('rose', 'Rose'),
  turquoise('turquoise', 'Turquoise');

  const CouleurFibre(this.value, this.label);
  final String value;
  final String label;
}

enum CapaciteCable {
  cap2(2),
  cap6(6),
  cap12(12),
  cap18(18),
  cap24(24),
  cap48(48),
  cap96(96);

  const CapaciteCable(this.value);
  final int value;
}

enum TypeConnecteur {
  fc('FC'),
  lc('LC'),
  sc('SC');

  const TypeConnecteur(this.value);
  final String value;
}

enum TypeClient {
  ls('LS', 'Client LS (Liaison Spécialisée)'),
  ftth('FTTH', 'Client FTTH');

  const TypeClient(this.value, this.label);
  final String value;
  final String label;
}

enum TypeOrganisation {
  entreprise('entreprise', 'Entreprise'),
  banque('banque', 'Banque'),
  particulier('particulier', 'Particulier');

  const TypeOrganisation(this.value, this.label);
  final String value;
  final String label;
}
```

## 🏗️ Modèles de Détails Spécialisés

### 1. Détail ONT (Selon wa.md - Ligne 145-152)
```dart
// lib/data/models/details/detail_ont.dart
import 'package:json_annotation/json_annotation.dart';

part 'detail_ont.g.dart';

@JsonSerializable()
class DetailONT {
  /// Numéro de série de l'ONT (alphanumérique)
  @JsonKey(name: 'numero_serie')
  final String? numeroSerie;

  /// Numéro de la ligne
  @JsonKey(name: 'numero_ligne')
  final String? numeroLigne;

  /// Nom de la ligne
  @JsonKey(name: 'nom_ligne')
  final String? nomLigne;

  /// Couleur du brin allant au FAT (1|2)
  @JsonKey(name: 'couleur_brin_fat')
  final String? couleurBrinFat;

  /// Quantité de moue de câble laissé en mètre
  @JsonKey(name: 'moue_cable_metres')
  final double? moueCableMetres;

  DetailONT({
    this.numeroSerie,
    this.numeroLigne,
    this.nomLigne,
    this.couleurBrinFat,
    this.moueCableMetres,
  });

  factory DetailONT.fromJson(Map<String, dynamic> json) =>
      _$DetailONTFromJson(json);

  Map<String, dynamic> toJson() => _$DetailONTToJson(this);

  DetailONT copyWith({
    String? numeroSerie,
    String? numeroLigne,
    String? nomLigne,
    String? couleurBrinFat,
    double? moueCableMetres,
  }) {
    return DetailONT(
      numeroSerie: numeroSerie ?? this.numeroSerie,
      numeroLigne: numeroLigne ?? this.numeroLigne,
      nomLigne: nomLigne ?? this.nomLigne,
      couleurBrinFat: couleurBrinFat ?? this.couleurBrinFat,
      moueCableMetres: moueCableMetres ?? this.moueCableMetres,
    );
  }
}
```

### 2. Détail POP LS (Selon wa.md - Ligne 154-169)
```dart
// lib/data/models/details/detail_pop_ls.dart
@JsonSerializable()
class DetailPOPLS {
  /// Détails du convertisseur
  final ConvertisseurPOPLS convertisseur;

  /// Détails du tiroir optique
  @JsonKey(name: 'tiroir_optique')
  final TiroirOptiquePOPLS tiroirOptique;

  /// Quantité de moue de câble laissé en mètre
  @JsonKey(name: 'moue_cable_metres')
  final double? moueCableMetres;

  DetailPOPLS({
    required this.convertisseur,
    required this.tiroirOptique,
    this.moueCableMetres,
  });

  factory DetailPOPLS.fromJson(Map<String, dynamic> json) =>
      _$DetailPOPLSFromJson(json);

  Map<String, dynamic> toJson() => _$DetailPOPLSToJson(this);
}

@JsonSerializable()
class ConvertisseurPOPLS {
  /// Nombre de brins utilisés par le convertisseur (1|2)
  @JsonKey(name: 'nb_brins_utilises')
  final int nbBrinsUtilises;

  /// Type de connecteur(s) de la jarretière(s) branchée sur le convertisseur
  @JsonKey(name: 'type_connecteur')
  final String typeConnecteur; // FC|LC|SC

  ConvertisseurPOPLS({
    required this.nbBrinsUtilises,
    required this.typeConnecteur,
  });

  factory ConvertisseurPOPLS.fromJson(Map<String, dynamic> json) =>
      _$ConvertisseurPOPLSFromJson(json);

  Map<String, dynamic> toJson() => _$ConvertisseurPOPLSToJson(this);
}

@JsonSerializable()
class TiroirOptiquePOPLS {
  /// Nombre de brins utilisés (1|2)
  @JsonKey(name: 'nb_brins_utilises')
  final int nbBrinsUtilises;

  /// Capacité de câble (96|48|24|18|12|6|2)
  @JsonKey(name: 'capacite_cable')
  final int capaciteCable;

  /// Couleur du toron dans le câble
  @JsonKey(name: 'couleur_toron')
  final String couleurToron;

  /// Couleur du brin fusionné sur le pigtail du tiroir
  @JsonKey(name: 'couleur_brin')
  final String couleurBrin;

  /// Numéro de port utilisé sur le tiroir (1-12)
  @JsonKey(name: 'numero_port')
  final int numeroPort;

  /// Type du connecteur de la jarretière branchée sur le tiroir
  @JsonKey(name: 'type_connecteur')
  final String typeConnecteur;

  TiroirOptiquePOPLS({
    required this.nbBrinsUtilises,
    required this.capaciteCable,
    required this.couleurToron,
    required this.couleurBrin,
    required this.numeroPort,
    required this.typeConnecteur,
  });

  factory TiroirOptiquePOPLS.fromJson(Map<String, dynamic> json) =>
      _$TiroirOptiquePOPLSFromJson(json);

  Map<String, dynamic> toJson() => _$TiroirOptiquePOPLSToJson(this);
}
```

### 3. Détail POP FTTH (Selon wa.md - Ligne 171-185)
```dart
// lib/data/models/details/detail_pop_ftth.dart
@JsonSerializable()
class DetailPOPFTTH {
  /// Détails OLT
  final OLTPOPFTTH olt;

  /// Détails ODF
  final ODFPOPFTTH odf;

  DetailPOPFTTH({
    required this.olt,
    required this.odf,
  });

  factory DetailPOPFTTH.fromJson(Map<String, dynamic> json) =>
      _$DetailPOPFTTHFromJson(json);

  Map<String, dynamic> toJson() => _$DetailPOPFTTHToJson(this);
}

@JsonSerializable()
class OLTPOPFTTH {
  /// Référence OLT
  @JsonKey(name: 'reference_olt')
  final String referenceOlt;

  /// Port OLT
  @JsonKey(name: 'port_olt')
  final String portOlt;

  OLTPOPFTTH({
    required this.referenceOlt,
    required this.portOlt,
  });

  factory OLTPOPFTTH.fromJson(Map<String, dynamic> json) =>
      _$OLTPOPFTTHFromJson(json);

  Map<String, dynamic> toJson() => _$OLTPOPFTTHToJson(this);
}

@JsonSerializable()
class ODFPOPFTTH {
  /// Référence ODF
  @JsonKey(name: 'reference_odf')
  final String referenceOdf;

  /// Numéro FDT
  @JsonKey(name: 'numero_fdt')
  final String numeroFdt;

  /// Quantième cassette en partant du haut (1-30)
  @JsonKey(name: 'cassette_position')
  final int cassettePosition;

  /// Numéro du port sur la cassette (1-12)
  @JsonKey(name: 'numero_port')
  final int numeroPort;

  /// Capacité du câble sortant du central
  @JsonKey(name: 'capacite_cable')
  final int capaciteCable;

  /// Couleur du toron
  @JsonKey(name: 'couleur_toron')
  final String couleurToron;

  /// Couleur du brin
  @JsonKey(name: 'couleur_brin')
  final String couleurBrin;

  ODFPOPFTTH({
    required this.referenceOdf,
    required this.numeroFdt,
    required this.cassettePosition,
    required this.numeroPort,
    required this.capaciteCable,
    required this.couleurToron,
    required this.couleurBrin,
  });

  factory ODFPOPFTTH.fromJson(Map<String, dynamic> json) =>
      _$ODFPOPFTTHFromJson(json);

  Map<String, dynamic> toJson() => _$ODFPOPFTTHToJson(this);
}
```

### 4. Détail Chambre (Selon wa.md - Ligne 195-213)
```dart
// lib/data/models/details/detail_chambre.dart
@JsonSerializable()
class DetailChambre {
  /// Informations côté central
  @JsonKey(name: 'cote_central')
  final CoteChambre coteCentral;

  /// Informations côté client
  @JsonKey(name: 'cote_client')
  final CoteChambre coteClient;

  DetailChambre({
    required this.coteCentral,
    required this.coteClient,
  });

  factory DetailChambre.fromJson(Map<String, dynamic> json) =>
      _$DetailChambreFromJson(json);

  Map<String, dynamic> toJson() => _$DetailChambreToJson(this);
}

@JsonSerializable()
class CoteChambre {
  /// Capacité du câble
  @JsonKey(name: 'capacite_cable')
  final int capaciteCable;

  /// Couleur du toron dans le câble
  @JsonKey(name: 'couleur_toron')
  final String couleurToron;

  /// Couleur du brin dans le toron
  @JsonKey(name: 'couleur_brin')
  final String couleurBrin;

  /// Quantité de moue de câble laissé en mètre
  @JsonKey(name: 'moue_cable_metres')
  final double moueCableMetres;

  CoteChambre({
    required this.capaciteCable,
    required this.couleurToron,
    required this.couleurBrin,
    required this.moueCableMetres,
  });

  factory CoteChambre.fromJson(Map<String, dynamic> json) =>
      _$CoteChambreFromJson(json);

  Map<String, dynamic> toJson() => _$CoteChambreToJson(this);
}
```

### 5. Détail FAT (Selon wa.md - Ligne 226-235)
```dart
// lib/data/models/details/detail_fat.dart
@JsonSerializable()
class DetailFAT {
  /// Numéro du FAT
  @JsonKey(name: 'numero_fat')
  final String numeroFat;

  /// Numéro de FDT associé
  @JsonKey(name: 'numero_fdt')
  final String numeroFdt;

  /// Port utilisé sur le splitter
  @JsonKey(name: 'port_splitter')
  final int portSplitter;

  /// Capacité du câble entrant le FAT
  @JsonKey(name: 'capacite_cable_entrant')
  final int capaciteCableEntrant;

  /// Couleur du brin
  @JsonKey(name: 'couleur_brin')
  final String couleurBrin;

  /// Couleur du toron
  @JsonKey(name: 'couleur_toron')
  final String couleurToron;

  /// Quantité de moue de câble laissé en mètre sur le poteau du FAT
  @JsonKey(name: 'moue_cable_metres')
  final double moueCableMetres;

  DetailFAT({
    required this.numeroFat,
    required this.numeroFdt,
    required this.portSplitter,
    required this.capaciteCableEntrant,
    required this.couleurBrin,
    required this.couleurToron,
    required this.moueCableMetres,
  });

  factory DetailFAT.fromJson(Map<String, dynamic> json) =>
      _$DetailFATFromJson(json);

  Map<String, dynamic> toJson() => _$DetailFATToJson(this);
}
```

### 6. Détail FDT (Selon wa.md - Ligne 237-252)
```dart
// lib/data/models/details/detail_fdt.dart
@JsonSerializable()
class DetailFDT {
  /// Informations côté transport (venant du central)
  @JsonKey(name: 'cote_transport')
  final CoteFDT coteTransport;

  /// Informations côté distribution (allant au FAT)
  @JsonKey(name: 'cote_distribution')
  final CoteFDT coteDistribution;

  DetailFDT({
    required this.coteTransport,
    required this.coteDistribution,
  });

  factory DetailFDT.fromJson(Map<String, dynamic> json) =>
      _$DetailFDTFromJson(json);

  Map<String, dynamic> toJson() => _$DetailFDTToJson(this);
}

@JsonSerializable()
class CoteFDT {
  /// Capacité du câble
  @JsonKey(name: 'capacite_cable')
  final int capaciteCable;

  /// Couleur du brin
  @JsonKey(name: 'couleur_brin')
  final String couleurBrin;

  /// Couleur du toron
  @JsonKey(name: 'couleur_toron')
  final String couleurToron;

  /// Quantième cassette en partant du haut (1-30)
  @JsonKey(name: 'cassette_position')
  final int cassettePosition;

  /// Numéro de port sur la cassette (1-12)
  @JsonKey(name: 'numero_port')
  final int numeroPort;

  CoteFDT({
    required this.capaciteCable,
    required this.couleurBrin,
    required this.couleurToron,
    required this.cassettePosition,
    required this.numeroPort,
  });

  factory CoteFDT.fromJson(Map<String, dynamic> json) =>
      _$CoteFDTFromJson(json);

  Map<String, dynamic> toJson() => _$CoteFDTToJson(this);
}
```

### 7. Détail Manchon (Selon wa.md - Ligne 215-224)
```dart
// lib/data/models/details/detail_manchon.dart
@JsonSerializable()
class DetailManchon {
  /// Capacité du câble entrant le manchon
  @JsonKey(name: 'capacite_cable_entrant')
  final int capaciteCableEntrant;

  /// Couleur du brin entrant
  @JsonKey(name: 'couleur_brin_entrant')
  final String couleurBrinEntrant;

  /// Couleur du toron entrant
  @JsonKey(name: 'couleur_toron_entrant')
  final String couleurToronEntrant;

  /// Capacité du câble sortant du manchon allant au client
  @JsonKey(name: 'capacite_cable_sortant')
  final int capaciteCableSortant;

  /// Couleur du brin sortant
  @JsonKey(name: 'couleur_brin_sortant')
  final String couleurBrinSortant;

  /// Couleur du toron sortant
  @JsonKey(name: 'couleur_toron_sortant')
  final String couleurToronSortant;

  /// Quantité de moue de câble laissé en mètre
  @JsonKey(name: 'moue_cable_metres')
  final double moueCableMetres;

  /// Indique si c'est un manchon aérien
  @JsonKey(name: 'is_aerien')
  final bool isAerien;

  DetailManchon({
    required this.capaciteCableEntrant,
    required this.couleurBrinEntrant,
    required this.couleurToronEntrant,
    required this.capaciteCableSortant,
    required this.couleurBrinSortant,
    required this.couleurToronSortant,
    required this.moueCableMetres,
    required this.isAerien,
  });

  factory DetailManchon.fromJson(Map<String, dynamic> json) =>
      _$DetailManchonFromJson(json);

  Map<String, dynamic> toJson() => _$DetailManchonToJson(this);
}
```

## 🔗 Modèle Principal Point Dynamique

```dart
// lib/data/models/point_dynamique.dart
@JsonSerializable()
class PointDynamique {
  final String id;
  final String liaison;
  final String nom;
  @JsonKey(name: 'type_point')
  final String typePoint;
  final double latitude;
  final double longitude;
  @JsonKey(name: 'distance_depuis_central')
  final double? distanceDepuisCentral;
  final int? ordre;
  final String? description;

  /// Commentaire du technicien (optionnel)
  @JsonKey(name: 'commentaire_technicien')
  final String? commentaireTechnicien;

  /// Photos associées au point dynamique
  final List<PhotoPoint>? photos;

  // Détails spécialisés selon le type de point
  @JsonKey(name: 'detail_ont')
  final DetailONT? detailOnt;

  @JsonKey(name: 'detail_pop_ls')
  final DetailPOPLS? detailPopLs;

  @JsonKey(name: 'detail_pop_ftth')
  final DetailPOPFTTH? detailPopFtth;

  @JsonKey(name: 'detail_chambre')
  final DetailChambre? detailChambre;

  @JsonKey(name: 'detail_fat')
  final DetailFAT? detailFat;

  @JsonKey(name: 'detail_fdt')
  final DetailFDT? detailFdt;

  @JsonKey(name: 'detail_manchon')
  final DetailManchon? detailManchon;

  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  PointDynamique({
    required this.id,
    required this.liaison,
    required this.nom,
    required this.typePoint,
    required this.latitude,
    required this.longitude,
    this.distanceDepuisCentral,
    this.ordre,
    this.description,
    this.commentaireTechnicien,
    this.photos,
    this.detailOnt,
    this.detailPopLs,
    this.detailPopFtth,
    this.detailChambre,
    this.detailFat,
    this.detailFdt,
    this.detailManchon,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PointDynamique.fromJson(Map<String, dynamic> json) =>
      _$PointDynamiqueFromJson(json);

  Map<String, dynamic> toJson() => _$PointDynamiqueToJson(this);

  /// Retourne le détail approprié selon le type de point
  dynamic get detailSpecifique {
    switch (typePoint) {
      case 'ONT':
        return detailOnt;
      case 'POP_LS':
        return detailPopLs;
      case 'POP_FTTH':
        return detailPopFtth;
      case 'chambre':
        return detailChambre;
      case 'FAT':
        return detailFat;
      case 'FDT':
        return detailFdt;
      case 'manchon':
      case 'manchon_aerien':
        return detailManchon;
      default:
        return null;
    }
  }

  /// Vérifie si le point a tous les détails requis
  bool get isComplete {
    switch (typePoint) {
      case 'ONT':
        return detailOnt != null && 
               detailOnt!.numeroSerie != null &&
               detailOnt!.numeroLigne != null;
      case 'FAT':
        return detailFat != null && 
               detailFat!.numeroFat.isNotEmpty &&
               detailFat!.numeroFdt.isNotEmpty;
      case 'chambre':
        return detailChambre != null &&
               detailChambre!.coteCentral != null &&
               detailChambre!.coteClient != null;
      default:
        return true;
    }
  }

  /// Calcule le total de moue de câble pour ce point
  double get totalMoueCable {
    switch (typePoint) {
      case 'ONT':
        return detailOnt?.moueCableMetres ?? 0;
      case 'POP_LS':
        return detailPopLs?.moueCableMetres ?? 0;
      case 'FAT':
        return detailFat?.moueCableMetres ?? 0;
      case 'manchon':
      case 'manchon_aerien':
        return detailManchon?.moueCableMetres ?? 0;
      case 'chambre':
        return (detailChambre?.coteCentral.moueCableMetres ?? 0) +
               (detailChambre?.coteClient.moueCableMetres ?? 0);
      default:
        return 0;
    }
  }
}
```

## 📊 Modèles pour la Gestion des Segments

```dart
// lib/data/models/segment.dart
@JsonSerializable()
class Segment {
  final String id;
  final String liaison;
  @JsonKey(name: 'point_depart')
  final String pointDepart;
  @JsonKey(name: 'point_arrivee')
  final String pointArrivee;
  
  /// Distance GPS directe
  @JsonKey(name: 'distance_gps')
  final double distanceGps;
  
  /// Distance réelle du câble posé (incluant moue)
  @JsonKey(name: 'distance_cable')
  final double distanceCable;
  
  /// Coordonnées du tracé précis
  @JsonKey(name: 'trace_coords')
  final List<List<double>> traceCoords;
  
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  
  @JsonKey(name: 'updated_at')
  final DateTime updatedAt;

  Segment({
    required this.id,
    required this.liaison,
    required this.pointDepart,
    required this.pointArrivee,
    required this.distanceGps,
    required this.distanceCable,
    required this.traceCoords,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Segment.fromJson(Map<String, dynamic> json) =>
      _$SegmentFromJson(json);

  Map<String, dynamic> toJson() => _$SegmentToJson(this);

  /// Convertit les coordonnées en LatLng pour Google Maps
  List<LatLng> get traceLatLng {
    return traceCoords.map((coord) => LatLng(coord[0], coord[1])).toList();
  }

  /// Calcule le moue de câble (différence entre distance câble et GPS)
  double get moueCable => distanceCable - distanceGps;

  /// Pourcentage de moue par rapport à la distance GPS
  double get pourcentageMoue => (moueCable / distanceGps) * 100;
}
```

## 🔧 Modèles pour les Requêtes

### 1. Création de Point Dynamique
```dart
// lib/data/models/requests/create_point_request.dart
@JsonSerializable()
class CreatePointRequest {
  final String liaison;
  final String nom;
  @JsonKey(name: 'type_point')
  final String typePoint;
  final double latitude;
  final double longitude;
  @JsonKey(name: 'distance_depuis_central')
  final double? distanceDepuisCentral;
  final int? ordre;
  final String? description;
  @JsonKey(name: 'commentaire_technicien')
  final String? commentaireTechnicien;

  // Détails spécialisés
  @JsonKey(name: 'detail_ont')
  final Map<String, dynamic>? detailOnt;
  @JsonKey(name: 'detail_pop_ls')
  final Map<String, dynamic>? detailPopLs;
  @JsonKey(name: 'detail_pop_ftth')
  final Map<String, dynamic>? detailPopFtth;
  @JsonKey(name: 'detail_chambre')
  final Map<String, dynamic>? detailChambre;
  @JsonKey(name: 'detail_fat')
  final Map<String, dynamic>? detailFat;
  @JsonKey(name: 'detail_fdt')
  final Map<String, dynamic>? detailFdt;
  @JsonKey(name: 'detail_manchon')
  final Map<String, dynamic>? detailManchon;

  CreatePointRequest({
    required this.liaison,
    required this.nom,
    required this.typePoint,
    required this.latitude,
    required this.longitude,
    this.distanceDepuisCentral,
    this.ordre,
    this.description,
    this.commentaireTechnicien,
    this.detailOnt,
    this.detailPopLs,
    this.detailPopFtth,
    this.detailChambre,
    this.detailFat,
    this.detailFdt,
    this.detailManchon,
  });

  factory CreatePointRequest.fromJson(Map<String, dynamic> json) =>
      _$CreatePointRequestFromJson(json);

  Map<String, dynamic> toJson() => _$CreatePointRequestToJson(this);
}
```

## 🚨 Modèles de Diagnostic OTDR

```dart
// lib/data/models/diagnostic/coupure_detection.dart
@JsonSerializable()
class CoupureDetection {
  final String message;
  @JsonKey(name: 'mesure_otdr')
  final MesureOTDR mesureOtdr;
  final Coupure coupure;
  final AnalyseCoupure analyse;

  CoupureDetection({
    required this.message,
    required this.mesureOtdr,
    required this.coupure,
    required this.analyse,
  });

  factory CoupureDetection.fromJson(Map<String, dynamic> json) =>
      _$CoupureDetectionFromJson(json);

  Map<String, dynamic> toJson() => _$CoupureDetectionToJson(this);
}

@JsonSerializable()
class AnalyseCoupure {
  @JsonKey(name: 'distance_absolue_km')
  final double distanceAbsolueKm;
  @JsonKey(name: 'precision_estimation')
  final String precisionEstimation;
  @JsonKey(name: 'point_proche')
  final PointProche? pointProche;
  @JsonKey(name: 'segment_info')
  final SegmentInfo? segmentInfo;
  @JsonKey(name: 'coordonnees_estimees')
  final Map<String, double>? coordonneesEstimees;

  AnalyseCoupure({
    required this.distanceAbsolueKm,
    required this.precisionEstimation,
    this.pointProche,
    this.segmentInfo,
    this.coordonneesEstimees,
  });

  factory AnalyseCoupure.fromJson(Map<String, dynamic> json) =>
      _$AnalyseCoupureFromJson(json);

  Map<String, dynamic> toJson() => _$AnalyseCoupureToJson(this);
}

@JsonSerializable()
class PointProche {
  final String nom;
  @JsonKey(name: 'distance_km')
  final double distanceKm;

  PointProche({
    required this.nom,
    required this.distanceKm,
  });

  factory PointProche.fromJson(Map<String, dynamic> json) =>
      _$PointProcheFromJson(json);

  Map<String, dynamic> toJson() => _$PointProcheToJson(this);
}
```

## 🎨 Helpers et Extensions

```dart
// lib/core/extensions/point_dynamique_extensions.dart
extension PointDynamiqueExtensions on PointDynamique {
  /// Icône à afficher sur la carte selon le type
  BitmapDescriptor get mapIcon {
    switch (typePoint) {
      case 'ONT':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen);
      case 'FAT':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange);
      case 'FDT':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow);
      case 'chambre':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue);
      case 'POP_LS':
      case 'POP_FTTH':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueMagenta);
      case 'manchon':
      case 'manchon_aerien':
        return BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueCyan);
      default:
        return BitmapDescriptor.defaultMarker;
    }
  }

  /// Couleur du marqueur selon le statut
  Color get statusColor {
    if (!isComplete) return Colors.red;
    if (photos?.isEmpty ?? true) return Colors.orange;
    return Colors.green;
  }

  /// Description courte pour affichage
  String get shortDescription {
    switch (typePoint) {
      case 'ONT':
        return 'ONT ${detailOnt?.numeroSerie ?? ""}';
      case 'FAT':
        return 'FAT ${detailFat?.numeroFat ?? ""}';
      case 'FDT':
        return 'FDT';
      case 'chambre':
        return 'Chambre';
      case 'POP_LS':
        return 'POP LS';
      case 'POP_FTTH':
        return 'POP FTTH';
      default:
        return typePoint;
    }
  }
}
```

Ce guide fournit tous les modèles nécessaires pour implémenter les exigences détaillées du fichier wa.md dans l'application Flutter, avec une structure complète et typée pour tous les types de points dynamiques et leurs spécifications techniques.