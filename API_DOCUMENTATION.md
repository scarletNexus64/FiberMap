# Documentation API FiberMap

## 📋 Vue d'ensemble

FiberMap Backend fournit une API REST complète pour la gestion des réseaux fibre optique avec support LS (Liaisons Spécialisées) et FTTH. Cette documentation détaille tous les endpoints disponibles pour l'intégration Flutter.

## 🔗 URL de Base
```
http://localhost:8000/api/
```

## 🔐 Authentification

### 1. Login
**POST** `/auth/login/`
```json
{
  "username": "technicien1",
  "password": "motdepasse123"
}
```

**Response:**
```json
{
  "token": "abcd1234...",
  "user": {
    "id": "uuid",
    "username": "technicien1",
    "role": "technicien",
    "first_name": "Jean",
    "last_name": "Dupont"
  }
}
```

### 2. Logout
**POST** `/auth/logout/`

### 3. Profile
**GET** `/auth/profile/`

---

## 🗺️ API Cartographie

### 1. Récupérer les liaisons pour la carte
**GET** `/map/liaisons/`

**Query Parameters:**
- `client_id` (optional): Filtrer par client
- `type_liaison` (optional): LS ou FTTH
- `status` (optional): active, inactive, maintenance

**Response:**
```json
[
  {
    "id": "uuid",
    "nom_liaison": "LIA001",
    "client": {
      "id": "uuid",
      "name": "Client Test",
      "type_client": "FTTH"
    },
    "type_liaison": {
      "type": "FTTH",
      "description": "Fiber To The Home"
    },
    "point_central": {
      "lat": 48.8566,
      "lng": 2.3522
    },
    "point_client": {
      "lat": 48.8606,
      "lng": 2.3376
    },
    "status": "active",
    "distance_totale": 5.2,
    "points_dynamiques_count": 3
  }
]
```

### 2. Calculer les limites géographiques
**GET** `/map/liaisons/bounds/`

**Response:**
```json
{
  "bounds": {
    "southwest": {"lat": 48.85, "lng": 2.35},
    "northeast": {"lat": 48.87, "lng": 2.37}
  },
  "center": {"lat": 48.86, "lng": 2.36}
}
```

### 3. Récupérer le tracé détaillé d'une liaison
**GET** `/map/trace/{liaison_id}/`

**Response:**
```json
{
  "liaison": {
    "id": "uuid",
    "nom_liaison": "LIA001",
    "client": {...}
  },
  "trace": [
    {
      "lat": 48.8566,
      "lng": 2.3522,
      "type": "central",
      "nom": "Central",
      "info": {
        "liaison": "LIA001",
        "client": "Client Test"
      }
    },
    {
      "lat": 48.8576,
      "lng": 2.3400,
      "type": "chambre",
      "nom": "Chambre 1",
      "id": "uuid",
      "ordre": 1,
      "distance_depuis_central": 1.5
    }
  ],
  "statistiques": {
    "nb_points": 3,
    "nb_segments": 2,
    "distance_totale_km": 5.2
  }
}
```

---

## 📍 API Points Dynamiques

### 1. Lister les points dynamiques
**GET** `/points-dynamiques/`

**Query Parameters:**
- `liaison` (optional): Filtrer par liaison
- `type_point` (optional): ONT, FAT, FDT, chambre, manchon, etc.

### 2. Créer un point dynamique
**POST** `/points-dynamiques/`

**Payload:**
```json
{
  "liaison": "uuid",
  "nom": "Point Dynamique 1",
  "type_point": "ONT",
  "latitude": "48.8576",
  "longitude": "2.3400",
  "distance_depuis_central": 1.5,
  "ordre": 1,
  "description": "Description du point",
  "commentaire_technicien": "Commentaire optionnel"
}
```

### 3. Points dynamiques pour la carte
**GET** `/map/points-dynamiques/`

**Query Parameters:**
- `type_point` (optional)
- `liaison_id` (optional)

### 4. Ajouter des photos à un point
**POST** `/points-dynamiques/{point_id}/photos/`

**Form Data:**
- `categorie`: avant_intervention, apres_intervention, technique
- `image`: fichier image

---

## 🔗 API Segments

### 1. Créer un segment
**POST** `/segments/`

**Payload:**
```json
{
  "liaison": "uuid",
  "point_depart": "uuid",
  "point_arrivee": "uuid",
  "distance_gps": 2.0,
  "distance_cable": 2.5,
  "trace_coords": [[48.8566, 2.3522], [48.8576, 2.3400]]
}
```

### 2. Mettre à jour le tracé d'un segment
**PUT** `/segments/{segment_id}/mettre-a-jour-trace/`

**Payload:**
```json
{
  "trace_coords": [[48.8566, 2.3522], [48.8570, 2.3450], [48.8576, 2.3400]],
  "distance_cable": 2.8
}
```

---

## 🚨 API Diagnostic OTDR

### 1. Détecter une coupure
**POST** `/diagnostic/detecter-coupure/`

**Payload:**
```json
{
  "liaison_id": "uuid",
  "distance_coupure": 3.2,
  "position_technicien": "central",
  "direction_analyse": "vers_client",
  "point_mesure_id": "uuid",
  "attenuation": 15.5,
  "commentaires": "Coupure détectée lors du test"
}
```

**Response:**
```json
{
  "message": "Coupure détectée et analysée",
  "mesure_otdr": {...},
  "coupure": {
    "id": "uuid",
    "liaison": "uuid",
    "status": "detectee",
    "point_estime_lat": 48.8580,
    "point_estime_lng": 2.3420,
    "distance_absolue": 3.2,
    "precision_estimation": "haute"
  },
  "analyse": {
    "distance_absolue_km": 3.2,
    "precision_estimation": "haute",
    "point_proche": {
      "nom": "Chambre 2",
      "distance_km": 0.3
    },
    "segment_info": {
      "depart": "Chambre 1",
      "arrivee": "Chambre 2",
      "distance_sur_segment_km": 1.2
    }
  }
}
```

### 2. Simuler une analyse OTDR
**POST** `/diagnostic/simuler-analyse/`

**Payload:**
```json
{
  "liaison_id": "uuid",
  "distance_test": 2.5,
  "position_test": "central",
  "direction_test": "vers_client"
}
```

### 3. Changer le statut d'une coupure
**PUT** `/coupures/{coupure_id}/status/`

**Payload:**
```json
{
  "status": "en_cours"
}
```

---

## 🗺️ API Navigation

### 1. Navigation vers un point
**POST** `/navigation/point/`

**Payload:**
```json
{
  "point_id": "uuid",
  "position_actuelle": {
    "latitude": 48.8566,
    "longitude": 2.3522
  }
}
```

**Response:**
```json
{
  "point_cible": {
    "id": "uuid",
    "nom": "Point Dynamique 1",
    "type": "chambre",
    "latitude": 48.8576,
    "longitude": 2.3400
  },
  "distance_directe_km": 1.2,
  "azimut": 45.5,
  "direction": "Nord-Est",
  "instructions": [
    "Dirigez-vous vers le Nord-Est sur 1.2km"
  ]
}
```

### 2. Mettre à jour la position du technicien
**POST** `/navigation/position/`

**Payload:**
```json
{
  "position": {
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  "calculer_points_proches": true,
  "rayon_km": 1.0
}
```

### 3. Calculer un itinéraire multiple
**POST** `/navigation/itineraire-multiple/`

**Payload:**
```json
{
  "points_ids": ["uuid1", "uuid2", "uuid3"],
  "position_depart": {
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  "optimiser_ordre": true
}
```

---

## 👥 API Clients

### 1. Lister les clients
**GET** `/clients/`

### 2. Créer un client
**POST** `/clients/`

**Payload pour client FTTH:**
```json
{
  "name": "Jean Dupont",
  "type_client": "FTTH",
  "type_organisation": "particulier",
  "address": "123 Rue de la Paix, 75001 Paris",
  "phone": "+33123456789",
  "email": "jean.dupont@email.com",
  "numero_ligne": "0123456789",
  "nom_ligne": "DUPONT_Jean"
}
```

**Payload pour client LS:**
```json
{
  "name": "Entreprise ABC",
  "type_client": "LS",
  "type_organisation": "entreprise",
  "raison_sociale": "ABC Corp",
  "address": "456 Boulevard de l'Entreprise, 75002 Paris",
  "phone": "+33987654321",
  "email": "contact@abc-corp.com"
}
```

### 3. Liaisons d'un client
**GET** `/clients/{client_id}/liaisons/`

---

## 🔧 API Liaisons

### 1. Créer une liaison
**POST** `/liaisons/`

**Payload:**
```json
{
  "nom_liaison": "LIA001",
  "client": "uuid",
  "type_liaison": "uuid",
  "point_central_lat": "48.8566",
  "point_central_lng": "2.3522",
  "point_client_lat": "48.8606",
  "point_client_lng": "2.3376",
  "status": "active",
  "description": "Description de la liaison"
}
```

### 2. Recalculer les distances d'une liaison
**POST** `/liaisons/{liaison_id}/recalculer-distance/`

---

## 📊 API Statistiques

### 1. Statistiques globales pour la carte
**GET** `/map/statistiques/`

**Response:**
```json
{
  "clients": {
    "total": 150,
    "LS": 45,
    "FTTH": 105
  },
  "liaisons": {
    "total": 150,
    "actives": 140,
    "inactives": 10,
    "distance_totale_km": 1250.5
  },
  "points_dynamiques": {
    "total": 450,
    "par_type": {
      "ONT": 105,
      "FAT": 85,
      "chambre": 120
    }
  },
  "coupures": {
    "actives": 5,
    "total_mois": 12
  },
  "carte": {
    "nb_liaisons_avec_coupures": 5,
    "nb_points_sans_photos": 25,
    "couverture_geographique": {
      "nb_zones_actives": 140,
      "distance_totale_reseau_km": 1250.5
    }
  }
}
```

### 2. Recherche géographique
**GET** `/map/recherche-geographique/`

**Query Parameters:**
- `lat_min`: Latitude minimum
- `lat_max`: Latitude maximum  
- `lng_min`: Longitude minimum
- `lng_max`: Longitude maximum

---

## 🔔 API Notifications

### 1. Lister les notifications
**GET** `/notifications/`

### 2. Marquer une notification comme lue
**PUT** `/notifications/{notification_id}/lue/`

---

## 🔧 Types de Points Dynamiques et leurs Détails

### ONT (Optical Network Terminal)
```json
{
  "type_point": "ONT",
  "detail_ont": {
    "numero_serie": "ONT123456",
    "numero_ligne": "0123456789",
    "nom_ligne": "DUPONT_Jean",
    "couleur_brin_fat": "blue",
    "moue_cable_metres": 5.0
  }
}
```

### FAT (Fiber Access Terminal)
```json
{
  "type_point": "FAT",
  "detail_fat": {
    "numero_fat": "FAT001",
    "numero_fdt": "FDT001",
    "port_splitter": 1,
    "capacite_cable_entrant": 24,
    "couleur_brin": "blue",
    "couleur_toron": "orange",
    "moue_cable_metres": 15.0
  }
}
```

### Chambre
```json
{
  "type_point": "chambre",
  "detail_chambre": {
    "cote_central": {
      "capacite_cable": 48,
      "couleur_toron": "blue",
      "couleur_brin": "orange",
      "moue_cable_metres": 10.0
    },
    "cote_client": {
      "capacite_cable": 24,
      "couleur_toron": "vert",
      "couleur_brin": "blue",
      "moue_cable_metres": 8.0
    }
  }
}
```

### POP LS
```json
{
  "type_point": "POP_LS",
  "detail_pop_ls": {
    "convertisseur": {
      "nb_brins_utilises": 2,
      "type_connecteur": "LC"
    },
    "tiroir_optique": {
      "nb_brins_utilises": 2,
      "capacite_cable": 48,
      "couleur_toron": "blue",
      "couleur_brin": "orange",
      "numero_port": 5,
      "type_connecteur": "FC"
    },
    "moue_cable_metres": 12.0
  }
}
```

---

## 📱 Codes de Statut HTTP

- **200**: Succès
- **201**: Créé avec succès
- **400**: Erreur de validation
- **401**: Non authentifié
- **403**: Non autorisé
- **404**: Non trouvé
- **500**: Erreur serveur

---

## 🚀 Workflow Typique

### 1. Création d'une liaison complète
1. **POST** `/clients/` - Créer le client
2. **POST** `/liaisons/` - Créer la liaison de base
3. **POST** `/points-dynamiques/` - Créer les points dynamiques
4. **POST** `/segments/` - Créer les segments entre points
5. **PUT** `/segments/{id}/mettre-a-jour-trace/` - Ajuster les tracés

### 2. Diagnostic de coupure
1. **POST** `/diagnostic/detecter-coupure/` - Détecter la coupure
2. **GET** `/map/trace/{liaison_id}/` - Récupérer le tracé avec coupure
3. **POST** `/navigation/point/` - Navigation vers le point estimé
4. **PUT** `/coupures/{id}/status/` - Mettre à jour le statut

### 3. Intervention terrain
1. **POST** `/navigation/position/` - Mettre à jour position
2. **POST** `/points-dynamiques/{id}/photos/` - Ajouter photos
3. **POST** `/interventions/` - Créer l'intervention
4. **PUT** `/interventions/{id}/status/` - Finaliser intervention

Cette documentation fournit tous les éléments nécessaires pour intégrer le backend FiberMap avec l'application Flutter.