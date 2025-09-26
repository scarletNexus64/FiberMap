#!/bin/bash

echo "🚀 Démarrage du serveur FiberMap..."

# Vérifier les dépendances
echo "📦 Vérification des dépendances..."
pip3 install -r requirements.txt

# Vérifier la configuration Django
echo "🔧 Vérification de la configuration..."
python3 manage.py check

# Appliquer les migrations
echo "💾 Application des migrations..."
python3 manage.py migrate

# Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@fibermap.com',
        password='admin123',
        role='admin'
    )
    print('✅ Superutilisateur créé: admin/admin123')
else:
    print('✅ Superutilisateur admin existe déjà')
"

echo ""
echo "🎯 Backend FiberMap prêt!"
echo "📍 Endpoints principaux:"
echo "  • API Admin: http://localhost:8000/admin/"
echo "  • API Hello: http://localhost:8000/api/hello/"
echo "  • API Docs: http://localhost:8000/api/schema/swagger-ui/"
echo "  • Liaisons: http://localhost:8000/api/map/liaisons/"
echo ""
echo "👤 Connexion admin: admin/admin123"
echo ""

# Démarrer le serveur
echo "🌟 Démarrage du serveur sur http://localhost:8000..."
python3 manage.py runserver 0.0.0.0:8000