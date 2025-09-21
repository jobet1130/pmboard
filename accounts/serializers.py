from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from .models import Profile, Role, AuditLog

User = get_user_model()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['codename', 'name']
        read_only_fields = ['codename', 'name']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login', 'role']
        read_only_fields = ['id', 'is_active', 'date_joined', 'last_login']
    
    def get_role(self, obj):
        if hasattr(obj, 'profile') and obj.profile.role:
            return RoleSerializer(obj.profile.role).data
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import authenticate
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')
        
        if not username_or_email or not password:
            raise serializers.ValidationError(
                'Must include "username_or_email" and "password".',
                code='authorization'
            )
        
        # Try to authenticate with username or email
        user = None
        
        # First try with username
        user = authenticate(
            request=self.context.get('request'),
            username=username_or_email,
            password=password
        )
        
        # If that doesn't work, try with email
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(
                    request=self.context.get('request'),
                    username=user_obj.username,
                    password=password
                )
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
        
        if not user:
            raise serializers.ValidationError(
                'Unable to log in with provided credentials.',
                code='authorization'
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                'User account is disabled.',
                code='authorization'
            )
        
        # Generate tokens
        try:
            refresh = RefreshToken.for_user(user)
            
            return {
                'user': user,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        except Exception as e:
            raise serializers.ValidationError(
                f'Error generating tokens: {str(e)}',
                code='token_error'
            )

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    role_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Profile
        fields = [
            'user', 'bio', 'profile_picture', 'phone_number', 'timezone',
            'role', 'role_id', 'department', 'position', 'location',
            'date_of_birth', 'preferred_language', 'two_factor_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        if role_id is not None:
            try:
                role = Role.objects.get(id=role_id)
                instance.role = role
            except Role.DoesNotExist:
                raise serializers.ValidationError({"role_id": "Invalid role ID"})
        return super().update(instance, validated_data)

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'ip_address', 'user_agent', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp', 'metadata']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords don't match"})
        return attrs