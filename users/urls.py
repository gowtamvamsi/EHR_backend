from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RoleViewSet,PermissionViewSet

# Create separate routers for users and roles
user_router = DefaultRouter()
user_router.register(r'', UserViewSet, basename='user')  # No prefix for user routes

role_router = DefaultRouter()
role_router.register(r'', RoleViewSet, basename='role')  # No prefix for role routes

permission_router = DefaultRouter()  # Add PermissionViewSet
permission_router.register(r'', PermissionViewSet, basename='permission')

urlpatterns = [
    path('users/', include(user_router.urls)),  # Map UserViewSet routes directly to /api/users/
    path('roles/', include(role_router.urls)),
    path('permissions/',include(permission_router.urls))  # Map RoleViewSet routes directly to /api/roles/
]