from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects, but allow anyone to view.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return bool(request.user and request.user.is_staff)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the object has a user attribute and if it matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For models that directly have a ForeignKey to User
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        # For User model itself
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
            
        return False


class RoleBasedPermission(permissions.BasePermission):
    """
    Permission class that checks if the user has a specific role.
    The role_name can be passed as a parameter when initializing the permission.
    """
    def __init__(self, role_name=None):
        self.role_name = role_name

    def has_permission(self, request, view):
        # If no role_name is provided, deny access
        if not self.role_name:
            return False

        # Allow safe methods if configured to do so
        if request.method in permissions.SAFE_METHODS and getattr(view, 'allow_read_only', False):
            return True

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has the required role
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role'):
            return request.user.profile.role.name.lower() == self.role_name.lower()
        
        return False

    def has_object_permission(self, request, view, obj):
        # If no role_name is provided, deny access
        if not self.role_name:
            return False

        # Allow safe methods if configured to do so
        if request.method in permissions.SAFE_METHODS and getattr(view, 'allow_read_only', False):
            return True

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has the required role
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role'):
            return request.user.profile.role.name.lower() == self.role_name.lower()
        
        return False


class IsAdminOrSelf(permissions.BasePermission):
    """
    Allow access to admin users or the user themselves.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users can do anything
        if request.user and request.user.is_staff:
            return True

        # Users can access their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
            
        return False