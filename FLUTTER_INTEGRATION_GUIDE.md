# Guide d'Intégration Flutter - FiberMap

## 🎯 Architecture Flutter Recommandée

### Structure des Dossiers
```
lib/
├── main.dart
├── app/
│   ├── app.dart
│   ├── routes/
│   └── theme/
├── data/
│   ├── api/
│   ├── models/
│   ├── repositories/
│   └── services/
├── domain/
│   ├── entities/
│   ├── repositories/
│   └── usecases/
├── presentation/
│   ├── pages/
│   ├── widgets/
│   ├── providers/
│   └── utils/
└── core/
    ├── constants/
    ├── errors/
    └── utils/
```

## 📦 Dépendances Requises

### pubspec.yaml
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # État et injection de dépendances
  flutter_riverpod: ^2.4.0
  riverpod_annotation: ^2.2.0
  
  # Réseau
  dio: ^5.3.0
  retrofit: ^4.0.0
  json_annotation: ^4.8.0
  
  # Carte
  google_maps_flutter: ^2.5.0
  geolocator: ^10.1.0
  geocoding: ^2.1.0
  
  # Base de données locale
  drift: ^2.13.0
  sqlite3_flutter_libs: ^0.5.15
  
  # Images et médias
  image_picker: ^1.0.4
  cached_network_image: ^3.3.0
  
  # Navigation
  go_router: ^12.1.0
  
  # Utilitaires
  uuid: ^4.1.0
  intl: ^0.18.1
  logger: ^2.0.1

dev_dependencies:
  # Génération de code
  build_runner: ^2.4.7
  riverpod_generator: ^2.3.0
  retrofit_generator: ^7.0.0
  json_serializable: ^6.7.1
  drift_dev: ^2.13.0
```

## 🔌 Configuration de l'API Client

### 1. Client API de Base
```dart
// lib/data/api/api_client.dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

part 'api_client.g.dart';

@RestApi(baseUrl: "http://localhost:8000/api/")
abstract class ApiClient {
  factory ApiClient(Dio dio, {String baseUrl}) = _ApiClient;

  // Auth
  @POST("/auth/login/")
  Future<LoginResponse> login(@Body() LoginRequest request);

  @POST("/auth/logout/")
  Future<void> logout();

  @GET("/auth/profile/")
  Future<UserProfile> getProfile();

  // Cartographie
  @GET("/map/liaisons/")
  Future<List<LiaisonCarte>> getLiaisonsForMap({
    @Query("client_id") String? clientId,
    @Query("type_liaison") String? typeLiaison,
    @Query("status") String? status,
  });

  @GET("/map/liaisons/bounds/")
  Future<MapBounds> getLiaisonsBounds();

  @GET("/map/trace/{liaison_id}/")
  Future<LiaisonTrace> getLiaisonTrace(@Path("liaison_id") String liaisonId);

  // Points Dynamiques
  @GET("/points-dynamiques/")
  Future<List<PointDynamique>> getPointsDynamiques({
    @Query("liaison") String? liaison,
    @Query("type_point") String? typePoint,
  });

  @POST("/points-dynamiques/")
  Future<PointDynamique> createPointDynamique(@Body() CreatePointRequest request);

  @POST("/points-dynamiques/{point_id}/photos/")
  @MultiPart()
  Future<PhotoPoint> uploadPhoto(
    @Path("point_id") String pointId,
    @Part() String categorie,
    @Part() MultipartFile image,
  );

  // Segments
  @POST("/segments/")
  Future<Segment> createSegment(@Body() CreateSegmentRequest request);

  @PUT("/segments/{segment_id}/mettre-a-jour-trace/")
  Future<Segment> updateSegmentTrace(
    @Path("segment_id") String segmentId,
    @Body() UpdateTraceRequest request,
  );

  // Diagnostic OTDR
  @POST("/diagnostic/detecter-coupure/")
  Future<CoupureDetection> detecterCoupure(@Body() DetectCoupureRequest request);

  @POST("/diagnostic/simuler-analyse/")
  Future<AnalyseSimulation> simulerAnalyse(@Body() SimulateAnalyseRequest request);

  // Navigation
  @POST("/navigation/point/")
  Future<NavigationResponse> navigateToPoint(@Body() NavigationRequest request);

  @POST("/navigation/position/")
  Future<PositionUpdateResponse> updatePosition(@Body() PositionUpdateRequest request);

  @POST("/navigation/itineraire-multiple/")
  Future<MultipleRouteResponse> calculateMultipleRoute(@Body() MultipleRouteRequest request);

  // Coupures
  @PUT("/coupures/{coupure_id}/status/")
  Future<Coupure> updateCoupureStatus(
    @Path("coupure_id") String coupureId,
    @Body() StatusUpdateRequest request,
  );

  // Clients
  @GET("/clients/")
  Future<List<Client>> getClients();

  @POST("/clients/")
  Future<Client> createClient(@Body() CreateClientRequest request);

  // Liaisons
  @POST("/liaisons/")
  Future<Liaison> createLiaison(@Body() CreateLiaisonRequest request);

  // Statistiques
  @GET("/map/statistiques/")
  Future<MapStatistics> getMapStatistics();

  @GET("/map/recherche-geographique/")
  Future<GeographicSearchResult> searchGeographic({
    @Query("lat_min") required double latMin,
    @Query("lat_max") required double latMax,
    @Query("lng_min") required double lngMin,
    @Query("lng_max") required double lngMax,
  });
}
```

### 2. Configuration Dio avec Interceptors
```dart
// lib/data/api/dio_config.dart
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthInterceptor extends Interceptor {
  final String? token;

  AuthInterceptor(this.token);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (token != null) {
      options.headers['Authorization'] = 'Token $token';
    }
    options.headers['Content-Type'] = 'application/json';
    super.onRequest(options, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      // Token expired, redirect to login
      // Implement logout logic here
    }
    super.onError(err, handler);
  }
}

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio();
  final token = ref.watch(authTokenProvider);
  
  dio.interceptors.add(AuthInterceptor(token));
  dio.interceptors.add(LogInterceptor(responseBody: true, requestBody: true));
  
  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return ApiClient(dio);
});
```

## 🗺️ Modèles de Données

### 1. Modèles Principaux
```dart
// lib/data/models/liaison.dart
import 'package:json_annotation/json_annotation.dart';

part 'liaison.g.dart';

@JsonSerializable()
class LiaisonCarte {
  final String id;
  @JsonKey(name: 'nom_liaison')
  final String nomLiaison;
  final Client client;
  @JsonKey(name: 'type_liaison')
  final TypeLiaison typeLiaison;
  @JsonKey(name: 'point_central')
  final MapPoint pointCentral;
  @JsonKey(name: 'point_client')
  final MapPoint pointClient;
  final String status;
  @JsonKey(name: 'distance_totale')
  final double? distanceTotale;
  @JsonKey(name: 'points_dynamiques_count')
  final int pointsDynamiquesCount;

  LiaisonCarte({
    required this.id,
    required this.nomLiaison,
    required this.client,
    required this.typeLiaison,
    required this.pointCentral,
    required this.pointClient,
    required this.status,
    this.distanceTotale,
    required this.pointsDynamiquesCount,
  });

  factory LiaisonCarte.fromJson(Map<String, dynamic> json) =>
      _$LiaisonCarteFromJson(json);

  Map<String, dynamic> toJson() => _$LiaisonCarteToJson(this);
}

@JsonSerializable()
class MapPoint {
  final double lat;
  final double lng;

  MapPoint({required this.lat, required this.lng});

  factory MapPoint.fromJson(Map<String, dynamic> json) =>
      _$MapPointFromJson(json);

  Map<String, dynamic> toJson() => _$MapPointToJson(this);
}

@JsonSerializable()
class LiaisonTrace {
  final LiaisonCarte liaison;
  final List<TracePoint> trace;
  final TraceStatistics statistiques;

  LiaisonTrace({
    required this.liaison,
    required this.trace,
    required this.statistiques,
  });

  factory LiaisonTrace.fromJson(Map<String, dynamic> json) =>
      _$LiaisonTraceFromJson(json);

  Map<String, dynamic> toJson() => _$LiaisonTraceToJson(this);
}

@JsonSerializable()
class TracePoint {
  final double lat;
  final double lng;
  final String type;
  final String nom;
  final String? id;
  final int? ordre;
  @JsonKey(name: 'distance_depuis_central')
  final double? distanceDepuisCentral;
  final Map<String, dynamic>? info;

  TracePoint({
    required this.lat,
    required this.lng,
    required this.type,
    required this.nom,
    this.id,
    this.ordre,
    this.distanceDepuisCentral,
    this.info,
  });

  factory TracePoint.fromJson(Map<String, dynamic> json) =>
      _$TracePointFromJson(json);

  Map<String, dynamic> toJson() => _$TracePointToJson(this);
}
```

### 2. Point Dynamique avec Détails Spécialisés
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
  @JsonKey(name: 'commentaire_technicien')
  final String? commentaireTechnicien;
  
  // Détails spécialisés selon le type
  @JsonKey(name: 'detail_ont')
  final DetailONT? detailOnt;
  @JsonKey(name: 'detail_fat')
  final DetailFAT? detailFat;
  @JsonKey(name: 'detail_chambre')
  final DetailChambre? detailChambre;
  @JsonKey(name: 'detail_pop_ls')
  final DetailPOPLS? detailPopLs;
  @JsonKey(name: 'detail_pop_ftth')
  final DetailPOPFTTH? detailPopFtth;

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
    this.detailOnt,
    this.detailFat,
    this.detailChambre,
    this.detailPopLs,
    this.detailPopFtth,
  });

  factory PointDynamique.fromJson(Map<String, dynamic> json) =>
      _$PointDynamiqueFromJson(json);

  Map<String, dynamic> toJson() => _$PointDynamiqueToJson(this);
}

@JsonSerializable()
class DetailONT {
  @JsonKey(name: 'numero_serie')
  final String? numeroSerie;
  @JsonKey(name: 'numero_ligne')
  final String? numeroLigne;
  @JsonKey(name: 'nom_ligne')
  final String? nomLigne;
  @JsonKey(name: 'couleur_brin_fat')
  final String? couleurBrinFat;
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
}
```

## 🗺️ Intégration Carte Google Maps

### 1. Service de Carte
```dart
// lib/data/services/map_service.dart
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MapService {
  final ApiClient _apiClient;

  MapService(this._apiClient);

  Future<List<LiaisonCarte>> getLiaisonsForMap({
    String? clientId,
    String? typeLiaison,
    String? status,
  }) async {
    return await _apiClient.getLiaisonsForMap(
      clientId: clientId,
      typeLiaison: typeLiaison,
      status: status,
    );
  }

  Future<CameraPosition> getInitialCameraPosition() async {
    try {
      final bounds = await _apiClient.getLiaisonsBounds();
      return CameraPosition(
        target: LatLng(bounds.center.lat, bounds.center.lng),
        zoom: 12.0,
      );
    } catch (e) {
      // Position par défaut (Paris)
      return const CameraPosition(
        target: LatLng(48.8566, 2.3522),
        zoom: 10.0,
      );
    }
  }

  Set<Marker> createLiaisonMarkers(List<LiaisonCarte> liaisons) {
    final markers = <Marker>{};
    
    for (final liaison in liaisons) {
      // Marqueur central
      markers.add(Marker(
        markerId: MarkerId('central_${liaison.id}'),
        position: LatLng(liaison.pointCentral.lat, liaison.pointCentral.lng),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: InfoWindow(
          title: 'Central',
          snippet: liaison.nomLiaison,
        ),
      ));

      // Marqueur client
      markers.add(Marker(
        markerId: MarkerId('client_${liaison.id}'),
        position: LatLng(liaison.pointClient.lat, liaison.pointClient.lng),
        icon: BitmapDescriptor.defaultMarkerWithHue(
          liaison.typeLiaison.type == 'LS' 
            ? BitmapDescriptor.hueOrange 
            : BitmapDescriptor.hueGreen
        ),
        infoWindow: InfoWindow(
          title: liaison.client.name,
          snippet: '${liaison.typeLiaison.type} - ${liaison.status}',
        ),
      ));
    }

    return markers;
  }

  Set<Polyline> createLiaisonPolylines(List<LiaisonCarte> liaisons) {
    final polylines = <Polyline>{};

    for (final liaison in liaisons) {
      polylines.add(Polyline(
        polylineId: PolylineId('liaison_${liaison.id}'),
        points: [
          LatLng(liaison.pointCentral.lat, liaison.pointCentral.lng),
          LatLng(liaison.pointClient.lat, liaison.pointClient.lng),
        ],
        color: liaison.status == 'active' ? Colors.blue : Colors.grey,
        width: 3,
        patterns: liaison.status == 'active' ? [] : [PatternItem.dash(10)],
      ));
    }

    return polylines;
  }
}

final mapServiceProvider = Provider<MapService>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MapService(apiClient);
});
```

### 2. Provider d'État de la Carte
```dart
// lib/presentation/providers/map_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

@riverpod
class MapController extends _$MapController {
  @override
  FutureOr<MapState> build() async {
    final mapService = ref.read(mapServiceProvider);
    
    final liaisons = await mapService.getLiaisonsForMap();
    final initialPosition = await mapService.getInitialCameraPosition();
    
    return MapState(
      liaisons: liaisons,
      markers: mapService.createLiaisonMarkers(liaisons),
      polylines: mapService.createLiaisonPolylines(liaisons),
      initialCameraPosition: initialPosition,
      selectedLiaison: null,
      isCreatingLiaison: false,
      coupureOverlay: null,
    );
  }

  void selectLiaison(String liaisonId) async {
    final currentState = await future;
    final liaison = currentState.liaisons.firstWhere((l) => l.id == liaisonId);
    
    state = AsyncValue.data(currentState.copyWith(selectedLiaison: liaison));
  }

  void startCreatingLiaison() async {
    final currentState = await future;
    state = AsyncValue.data(currentState.copyWith(isCreatingLiaison: true));
  }

  void addCoupureOverlay(String liaisonId, double distanceCoupure) async {
    final currentState = await future;
    final apiClient = ref.read(apiClientProvider);
    
    try {
      final trace = await apiClient.getLiaisonTrace(liaisonId);
      final coupureOverlay = _calculateCoupureOverlay(trace, distanceCoupure);
      
      state = AsyncValue.data(
        currentState.copyWith(coupureOverlay: coupureOverlay)
      );
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
    }
  }

  CoupureOverlay _calculateCoupureOverlay(LiaisonTrace trace, double distance) {
    // Logique pour calculer l'overlay de coupure
    final points = <LatLng>[];
    double currentDistance = 0;
    
    for (int i = 0; i < trace.trace.length - 1; i++) {
      final point1 = trace.trace[i];
      final point2 = trace.trace[i + 1];
      
      final segmentDistance = point2.distanceDepuisCentral! - point1.distanceDepuisCentral!;
      
      if (currentDistance + segmentDistance >= distance) {
        // Point de coupure trouvé
        final ratio = (distance - currentDistance) / segmentDistance;
        final lat = point1.lat + (point2.lat - point1.lat) * ratio;
        final lng = point1.lng + (point2.lng - point1.lng) * ratio;
        
        points.add(LatLng(lat, lng));
        break;
      }
      
      points.add(LatLng(point1.lat, point1.lng));
      currentDistance += segmentDistance;
    }

    return CoupureOverlay(
      polyline: Polyline(
        polylineId: const PolylineId('coupure'),
        points: points,
        color: Colors.red,
        width: 5,
      ),
      marker: Marker(
        markerId: const MarkerId('point_coupure'),
        position: points.last,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
        infoWindow: const InfoWindow(
          title: 'Point de coupure estimé',
          snippet: 'Distance OTDR',
        ),
      ),
    );
  }
}

class MapState {
  final List<LiaisonCarte> liaisons;
  final Set<Marker> markers;
  final Set<Polyline> polylines;
  final CameraPosition initialCameraPosition;
  final LiaisonCarte? selectedLiaison;
  final bool isCreatingLiaison;
  final CoupureOverlay? coupureOverlay;

  MapState({
    required this.liaisons,
    required this.markers,
    required this.polylines,
    required this.initialCameraPosition,
    this.selectedLiaison,
    required this.isCreatingLiaison,
    this.coupureOverlay,
  });

  MapState copyWith({
    List<LiaisonCarte>? liaisons,
    Set<Marker>? markers,
    Set<Polyline>? polylines,
    CameraPosition? initialCameraPosition,
    LiaisonCarte? selectedLiaison,
    bool? isCreatingLiaison,
    CoupureOverlay? coupureOverlay,
  }) {
    return MapState(
      liaisons: liaisons ?? this.liaisons,
      markers: markers ?? this.markers,
      polylines: polylines ?? this.polylines,
      initialCameraPosition: initialCameraPosition ?? this.initialCameraPosition,
      selectedLiaison: selectedLiaison ?? this.selectedLiaison,
      isCreatingLiaison: isCreatingLiaison ?? this.isCreatingLiaison,
      coupureOverlay: coupureOverlay ?? this.coupureOverlay,
    );
  }
}

class CoupureOverlay {
  final Polyline polyline;
  final Marker marker;

  CoupureOverlay({required this.polyline, required this.marker});
}
```

## 🏗️ Pages Principales

### 1. Page de Carte Principale
```dart
// lib/presentation/pages/map_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

class MapPage extends ConsumerStatefulWidget {
  const MapPage({super.key});

  @override
  ConsumerState<MapPage> createState() => _MapPageState();
}

class _MapPageState extends ConsumerState<MapPage> {
  GoogleMapController? _mapController;

  @override
  Widget build(BuildContext context) {
    final mapState = ref.watch(mapControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('FiberMap'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => ref.read(mapControllerProvider.notifier).startCreatingLiaison(),
          ),
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showSearchDialog(),
          ),
        ],
      ),
      body: mapState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Erreur: $error')),
        data: (state) => Column(
          children: [
            if (state.selectedLiaison != null)
              _buildLiaisonInfoCard(state.selectedLiaison!),
            Expanded(
              child: GoogleMap(
                initialCameraPosition: state.initialCameraPosition,
                markers: state.markers,
                polylines: state.polylines,
                onMapCreated: (GoogleMapController controller) {
                  _mapController = controller;
                },
                onTap: state.isCreatingLiaison ? _onMapTap : null,
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: _buildFloatingActionButtons(),
    );
  }

  Widget _buildLiaisonInfoCard(LiaisonCarte liaison) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.blue.shade50,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  liaison.nomLiaison,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text('Client: ${liaison.client.name}'),
                Text('Type: ${liaison.typeLiaison.type}'),
                Text('Distance: ${liaison.distanceTotale?.toStringAsFixed(2) ?? "N/A"} km'),
              ],
            ),
          ),
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.visibility),
                onPressed: () => _viewLiaisonDetails(liaison),
              ),
              IconButton(
                icon: const Icon(Icons.warning),
                onPressed: () => _reportFault(liaison),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFloatingActionButtons() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        FloatingActionButton(
          heroTag: "location",
          mini: true,
          onPressed: _goToCurrentLocation,
          child: const Icon(Icons.my_location),
        ),
        const SizedBox(height: 8),
        FloatingActionButton(
          heroTag: "center",
          mini: true,
          onPressed: _centerOnAllLiaisons,
          child: const Icon(Icons.center_focus_strong),
        ),
      ],
    );
  }

  void _onMapTap(LatLng position) {
    // Logique pour création de liaison
    showDialog(
      context: context,
      builder: (context) => CreatePointDialog(
        position: position,
        onPointCreated: (point) {
          // Ajouter le point à la liaison en cours de création
        },
      ),
    );
  }

  void _viewLiaisonDetails(LiaisonCarte liaison) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => LiaisonDetailsPage(liaisionId: liaison.id),
      ),
    );
  }

  void _reportFault(LiaisonCarte liaison) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => ReportFaultPage(liaison: liaison),
      ),
    );
  }

  void _showSearchDialog() {
    showDialog(
      context: context,
      builder: (context) => const SearchLiaisonDialog(),
    );
  }

  void _goToCurrentLocation() async {
    // Implémenter géolocalisation
  }

  void _centerOnAllLiaisons() async {
    if (_mapController != null) {
      final bounds = await ref.read(mapServiceProvider).getLiaisonsForMap();
      // Calculer et animer vers les bounds
    }
  }
}
```

### 2. Page de Diagnostic OTDR
```dart
// lib/presentation/pages/diagnostic_page.dart
class DiagnosticPage extends ConsumerStatefulWidget {
  final LiaisonCarte liaison;

  const DiagnosticPage({super.key, required this.liaison});

  @override
  ConsumerState<DiagnosticPage> createState() => _DiagnosticPageState();
}

class _DiagnosticPageState extends ConsumerState<DiagnosticPage> {
  final _formKey = GlobalKey<FormState>();
  final _distanceController = TextEditingController();
  final _attenuationController = TextEditingController();
  final _commentsController = TextEditingController();
  
  String _positionTechnicien = 'central';
  String _directionAnalyse = 'vers_client';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Diagnostic OTDR - ${widget.liaison.nomLiaison}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildLiaisonInfo(),
              const SizedBox(height: 24),
              _buildMeasurementForm(),
              const SizedBox(height: 24),
              _buildActionButtons(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLiaisonInfo() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Informations Liaison',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text('Nom: ${widget.liaison.nomLiaison}'),
            Text('Client: ${widget.liaison.client.name}'),
            Text('Type: ${widget.liaison.typeLiaison.type}'),
            Text('Distance totale: ${widget.liaison.distanceTotale?.toStringAsFixed(2) ?? "N/A"} km'),
            Text('Status: ${widget.liaison.status}'),
          ],
        ),
      ),
    );
  }

  Widget _buildMeasurementForm() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Mesure OTDR',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _distanceController,
              decoration: const InputDecoration(
                labelText: 'Distance de coupure (km)',
                hintText: 'Ex: 3.245',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value?.isEmpty ?? true) {
                  return 'Distance requise';
                }
                if (double.tryParse(value!) == null) {
                  return 'Distance invalide';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _attenuationController,
              decoration: const InputDecoration(
                labelText: 'Atténuation (dB)',
                hintText: 'Ex: 15.5',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _positionTechnicien,
              decoration: const InputDecoration(
                labelText: 'Position du technicien',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'central', child: Text('Central')),
                DropdownMenuItem(value: 'client', child: Text('Client')),
                DropdownMenuItem(value: 'point_intermediaire', child: Text('Point intermédiaire')),
              ],
              onChanged: (value) => setState(() => _positionTechnicien = value!),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _directionAnalyse,
              decoration: const InputDecoration(
                labelText: 'Direction d\'analyse',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'vers_client', child: Text('Vers le client')),
                DropdownMenuItem(value: 'vers_central', child: Text('Vers le central')),
              ],
              onChanged: (value) => setState(() => _directionAnalyse = value!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _commentsController,
              decoration: const InputDecoration(
                labelText: 'Commentaires',
                hintText: 'Observations terrain...',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElevatedButton(
          onPressed: _simulateAnalysis,
          child: const Text('Simuler l\'analyse'),
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: _detectFault,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red,
            foregroundColor: Colors.white,
          ),
          child: const Text('Détecter la coupure'),
        ),
      ],
    );
  }

  void _simulateAnalysis() async {
    if (!_formKey.currentState!.validate()) return;

    final request = SimulateAnalyseRequest(
      liaisonId: widget.liaison.id,
      distanceTest: double.parse(_distanceController.text),
      positionTest: _positionTechnicien,
      directionTest: _directionAnalyse,
    );

    try {
      final apiClient = ref.read(apiClientProvider);
      final result = await apiClient.simulerAnalyse(request);

      if (mounted) {
        showDialog(
          context: context,
          builder: (context) => SimulationResultDialog(result: result),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    }
  }

  void _detectFault() async {
    if (!_formKey.currentState!.validate()) return;

    final request = DetectCoupureRequest(
      liaisonId: widget.liaison.id,
      distanceCoupure: double.parse(_distanceController.text),
      positionTechnicien: _positionTechnicien,
      directionAnalyse: _directionAnalyse,
      attenuation: double.tryParse(_attenuationController.text),
      commentaires: _commentsController.text,
    );

    try {
      final apiClient = ref.read(apiClientProvider);
      final result = await apiClient.detecterCoupure(request);

      // Ajouter l'overlay de coupure sur la carte
      ref.read(mapControllerProvider.notifier).addCoupureOverlay(
        widget.liaison.id,
        double.parse(_distanceController.text),
      );

      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => FaultResultPage(
              detection: result,
              liaison: widget.liaison,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e')),
        );
      }
    }
  }
}
```

## 🔧 Fonctionnalités Avancées

### 1. Création de Liaison Interactive
```dart
// lib/presentation/pages/create_liaison_page.dart
class CreateLiaisonPage extends ConsumerStatefulWidget {
  const CreateLiaisonPage({super.key});

  @override
  ConsumerState<CreateLiaisonPage> createState() => _CreateLiaisonPageState();
}

class _CreateLiaisonPageState extends ConsumerState<CreateLiaisonPage> {
  final List<LatLng> _points = [];
  final List<PointDynamique> _dynamicPoints = [];
  final Map<int, double> _segmentDistances = {};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Créer une liaison'),
        actions: [
          TextButton(
            onPressed: _canSave() ? _saveLiaison : null,
            child: const Text('Sauvegarder'),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildProgressIndicator(),
          Expanded(
            child: GoogleMap(
              initialCameraPosition: _getInitialPosition(),
              markers: _buildMarkers(),
              polylines: _buildPolylines(),
              onTap: _onMapTap,
              onMapCreated: (controller) => _mapController = controller,
            ),
          ),
          _buildBottomPanel(),
        ],
      ),
    );
  }

  Set<Marker> _buildMarkers() {
    final markers = <Marker>{};
    
    for (int i = 0; i < _points.length; i++) {
      markers.add(Marker(
        markerId: MarkerId('point_$i'),
        position: _points[i],
        icon: _getMarkerIcon(i),
        onTap: () => _editPoint(i),
      ));
    }
    
    return markers;
  }

  Set<Polyline> _buildPolylines() {
    final polylines = <Polyline>{};
    
    if (_points.length >= 2) {
      for (int i = 0; i < _points.length - 1; i++) {
        final color = _segmentDistances.containsKey(i) 
          ? Colors.blue 
          : Colors.grey;
        
        polylines.add(Polyline(
          polylineId: PolylineId('segment_$i'),
          points: [_points[i], _points[i + 1]],
          color: color,
          width: 4,
          onTap: () => _editSegment(i),
        ));
      }
    }
    
    return polylines;
  }

  void _onMapTap(LatLng position) {
    setState(() {
      _points.add(position);
    });
    _showPointCreationDialog(position, _points.length - 1);
  }

  void _showPointCreationDialog(LatLng position, int index) {
    showDialog(
      context: context,
      builder: (context) => CreatePointDialog(
        position: position,
        pointIndex: index,
        onPointCreated: (pointData) {
          setState(() {
            if (index < _dynamicPoints.length) {
              _dynamicPoints[index] = pointData;
            } else {
              _dynamicPoints.add(pointData);
            }
          });
        },
      ),
    );
  }

  void _editSegment(int segmentIndex) {
    showDialog(
      context: context,
      builder: (context) => SegmentEditDialog(
        segmentIndex: segmentIndex,
        currentDistance: _segmentDistances[segmentIndex],
        onDistanceSet: (distance) {
          setState(() {
            _segmentDistances[segmentIndex] = distance;
          });
        },
      ),
    );
  }
}
```

### 2. Navigation GPS
```dart
// lib/data/services/navigation_service.dart
class NavigationService {
  final ApiClient _apiClient;

  NavigationService(this._apiClient);

  Stream<Position> get positionStream => Geolocator.getPositionStream(
    locationSettings: const LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10,
    ),
  );

  Future<NavigationResponse> navigateToPoint({
    required String pointId,
    required LatLng currentPosition,
  }) async {
    return await _apiClient.navigateToPoint(
      NavigationRequest(
        pointId: pointId,
        positionActuelle: MapPoint(
          lat: currentPosition.latitude,
          lng: currentPosition.longitude,
        ),
      ),
    );
  }

  Future<void> updateTechnicianPosition(LatLng position) async {
    await _apiClient.updatePosition(
      PositionUpdateRequest(
        position: MapPoint(
          lat: position.latitude,
          lng: position.longitude,
        ),
        calculerPointsProches: true,
        rayonKm: 1.0,
      ),
    );
  }
}
```

## 🚀 Workflow d'Utilisation

### 1. Démarrage de l'Application
```dart
void main() {
  runApp(
    ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'FiberMap',
      routerConfig: ref.watch(routerProvider),
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
    );
  }
}
```

### 2. Gestion d'État avec Riverpod
```dart
// lib/presentation/providers/auth_provider.dart
@riverpod
class AuthController extends _$AuthController {
  @override
  FutureOr<User?> build() async {
    // Vérifier si l'utilisateur est connecté
    final token = await _getStoredToken();
    if (token != null) {
      try {
        final apiClient = ref.read(apiClientProvider);
        return await apiClient.getProfile();
      } catch (e) {
        await _clearStoredToken();
        return null;
      }
    }
    return null;
  }

  Future<bool> login(String username, String password) async {
    state = const AsyncValue.loading();
    
    try {
      final apiClient = ref.read(apiClientProvider);
      final response = await apiClient.login(
        LoginRequest(username: username, password: password),
      );
      
      await _storeToken(response.token);
      state = AsyncValue.data(response.user);
      return true;
    } catch (e) {
      state = AsyncValue.error(e, StackTrace.current);
      return false;
    }
  }

  Future<void> logout() async {
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.logout();
    } finally {
      await _clearStoredToken();
      state = const AsyncValue.data(null);
    }
  }
}
```

Ce guide fournit une base solide pour intégrer le backend FiberMap avec une application Flutter moderne, en utilisant les meilleures pratiques et une architecture robuste.