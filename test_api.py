#!/usr/bin/env python3
"""
Script de test pour l'API FiberMap
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_api():
    print("🧪 Test de l'API FiberMap")
    print("=" * 50)
    
    # 1. Test de l'endpoint hello (sans auth)
    print("1️⃣ Test endpoint hello...")
    response = requests.get(f"{BASE_URL}/hello/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ {response.json()['message']}")
    else:
        print(f"   ❌ Erreur: {response.text}")
    
    # 2. Test de connexion
    print("\n2️⃣ Test de connexion...")
    login_data = {
        "username": "jean.technicien",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data['token']
        user = data['user']
        print(f"   ✅ Connexion réussie pour {user['first_name']} {user['last_name']} ({user['role']})")
        headers = {"Authorization": f"Token {token}"}
    else:
        print(f"   ❌ Erreur de connexion: {response.text}")
        return
    
    # 3. Test des endpoints protégés
    endpoints_tests = [
        ("liaisons", "Liaisons fibre"),
        ("clients", "Clients"),
        ("types-liaisons", "Types de liaisons"),
        ("points-dynamiques", "Points dynamiques"),
        ("interventions", "Interventions"),
        ("coupures", "Coupures"),
        ("notifications", "Notifications"),
        ("map/liaisons", "Carte des liaisons"),
        ("map/points-dynamiques", "Carte des points"),
    ]
    
    print("\n3️⃣ Test des endpoints protégés...")
    for endpoint, description in endpoints_tests:
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}/", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'count' in data:
                    count = data['count']
                    print(f"   ✅ {description}: {count} éléments")
                elif isinstance(data, list):
                    print(f"   ✅ {description}: {len(data)} éléments")
                else:
                    print(f"   ✅ {description}: OK")
            else:
                print(f"   ❌ {description}: Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ {description}: Erreur {e}")
    
    # 4. Test d'un endpoint spécialisé
    print("\n4️⃣ Test d'endpoints spécialisés...")
    
    # Test du tracé d'une liaison
    response = requests.get(f"{BASE_URL}/liaisons/", headers=headers)
    if response.status_code == 200 and response.json()['count'] > 0:
        liaison_id = response.json()['results'][0]['id']
        
        trace_response = requests.get(f"{BASE_URL}/map/trace/{liaison_id}/", headers=headers)
        if trace_response.status_code == 200:
            trace_data = trace_response.json()
            print(f"   ✅ Tracé liaison: {len(trace_data['trace'])} points")
        else:
            print(f"   ❌ Tracé liaison: Status {trace_response.status_code}")
    
    # Test des coupures actives
    response = requests.get(f"{BASE_URL}/coupures/actives/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Coupures actives: {len(data)} coupures")
    else:
        print(f"   ❌ Coupures actives: Status {response.status_code}")
    
    print("\n🎉 Tests terminés !")
    print("\n📋 Endpoints disponibles:")
    print("   • GET  /api/hello/ - Test de l'API")
    print("   • POST /api/auth/login/ - Connexion")
    print("   • GET  /api/liaisons/ - Liste des liaisons")
    print("   • GET  /api/map/liaisons/ - Liaisons pour carte")
    print("   • GET  /api/coupures/ - Liste des coupures")
    print("   • GET  /api/interventions/ - Liste des interventions")
    print("   • GET  /api/notifications/ - Notifications utilisateur")
    print("\n📖 Documentation complète:")
    print("   • Swagger UI: http://127.0.0.1:8000/api/schema/swagger-ui/")
    print("   • ReDoc: http://127.0.0.1:8000/api/schema/redoc/")
    print("   • Admin Django: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    test_api()