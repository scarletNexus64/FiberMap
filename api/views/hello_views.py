from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def hello(request):
    """Vue de test - Bienvenue sur FiberMap API"""
    return Response({
        "message": "Bienvenue sur FiberMap API",
        "version": "1.0.0",
        "description": "API pour la gestion des liaisons fibre optique",
        "endpoints": {
            "auth": "/api/auth/",
            "liaisons": "/api/liaisons/",
            "clients": "/api/clients/",
            "interventions": "/api/interventions/",
            "map": "/api/map/",
            "diagnostic": "/api/diagnostic/",
            "notifications": "/api/notifications/"
        }
    })