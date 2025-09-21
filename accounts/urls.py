from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    RoleViewSet,
    AuditLogView,
    ChangePasswordView,
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'audit-logs', AuditLogView, basename='audit-log')

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User profile
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Change password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Include router URLs
    path('', include(router.urls)),
]