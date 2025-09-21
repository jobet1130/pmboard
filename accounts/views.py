from rest_framework import status, permissions, viewsets, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import Profile, Role, AuditLog
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    UserSerializer, 
    ProfileSerializer, 
    RoleSerializer, 
    AuditLogSerializer,
    ChangePasswordSerializer
)

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create user profile
            Profile.objects.create(user=user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Log the registration
            AuditLog.objects.create(
                user=user,
                action='user_register',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            print("\n=== Login Request ===")
            print(f"Data: {request.data}")
            
            serializer = LoginSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            
            print("\n=== Validated Data ===")
            print(f"Data: {data}")
            
            # Get the user from validated data
            user = data.get('user')
            if not user:
                raise ValidationError('User not found in validated data')
            
            print(f"\n=== User: {user} ===")
            
            # Log the login
            try:
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                audit_log = AuditLog.objects.create(
                    user=user,
                    action='user_login',
                    ip_address=self.get_client_ip(request),
                    user_agent=user_agent,
                    metadata={'user_agent': user_agent}
                )
                print(f"\n=== Audit Log Created: {audit_log} ===")
            except Exception as e:
                print(f"\n=== Audit Log Error: {str(e)} ===")
                raise
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Prepare response data
            response_data = {
                'access': data.get('access'),
                'refresh': data.get('refresh'),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'is_active': user.is_active
                }
            }
            
            print("\n=== Response Data ===")
            print(f"Data: {response_data}")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            print(f"\n=== Validation Error ===")
            print(f"Error: {str(e)}")
            print(f"Detail: {e.detail if hasattr(e, 'detail') else 'No detail'}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            import traceback
            print("\n=== Exception ===")
            print(f"Type: {type(e).__name__}")
            print(f"Error: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            
            return Response(
                {'detail': f'An error occurred during login: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        print("\n" + "="*80)
        print("=== SIMPLIFIED LOGOUT VIEW ===")
        print(f"User: {request.user}")
        print(f"Request data: {request.data}")
        
        try:
            # Get the refresh token from request data
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"Refresh token received (first 20 chars): {str(refresh_token)[:20]}...")
            
            try:
                # Convert to string and clean up
                refresh_token = str(refresh_token).strip()
                
                # For djangorestframework-simplejwt >= 5.0.0
                try:
                    from rest_framework_simplejwt.tokens import RefreshToken as RT
                    token = RT(refresh_token)
                    
                    # Check if we have the token_blacklist app installed
                    from django.apps import apps
                    if apps.is_installed('rest_framework_simplejwt.token_blacklist'):
                        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
                        
                        # Get or create the outstanding token
                        outstanding_token = OutstandingToken.objects.filter(
                            token=refresh_token
                        ).first()
                        
                        if not outstanding_token:
                            # Create the outstanding token
                            outstanding_token = OutstandingToken.objects.create(
                                user=request.user,
                                token=refresh_token,
                                created_at=timezone.now(),
                                expires_at=token['exp']
                            )
                        
                        # Blacklist the token
                        BlacklistedToken.objects.get_or_create(token=outstanding_token)
                        print("Token blacklisted successfully using token_blacklist app")
                    else:
                        # If token_blacklist is not installed, we can't blacklist the token
                        print("Warning: rest_framework_simplejwt.token_blacklist is not installed")
                    
                    # Log the successful logout
                    try:
                        AuditLog.objects.create(
                            user=request.user,
                            action='user_logout',
                            ip_address=self.get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        print("Audit log created successfully")
                    except Exception as e:
                        print(f"Warning: Could not create audit log: {str(e)}")
                    
                    return Response(status=status.HTTP_205_RESET_CONTENT)
                    
                except Exception as e:
                    print(f"Error during token processing: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise
                
            except TokenError as e:
                print(f"Token error: {str(e)}")
                return Response(
                    {'detail': 'Invalid or expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print("\n" + "="*80)
            print("!!! UNEXPECTED ERROR IN LOGOUT VIEW !!!")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("\nTraceback:")
            print(error_traceback)
            print("="*80 + "\n")
            
            return Response(
                {
                    'detail': 'An error occurred during logout.',
                    'error': str(e),
                    'type': type(e).__name__
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # Log the profile update
            AuditLog.objects.create(
                user=request.user,
                action='profile_update',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # Log the password change
            AuditLog.objects.create(
                user=request.user,
                action='password_change',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'status': 'password changed'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Role.objects.all().order_by('name')
    
    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action('role_create', instance)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('role_update', instance)
    
    def perform_destroy(self, instance):
        self.log_action('role_delete', instance)
        instance.delete()
    
    def log_action(self, action, instance):
        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            metadata={
                'role_id': str(instance.id),
                'role_name': instance.name
            },
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AuditLogView(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user')
        
        # Filter by user if provided
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by action if provided
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
            
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
            
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def actions(self, request):
        """Get list of available audit log actions"""
        return Response(dict(AuditLog.ActionChoices.choices))