from rest_framework import permissions


class IsProjectMemberOrCreator(permissions.BasePermission):
    """
    Custom permission to only allow members or the creator of a project to edit or delete it.
    Read-only access is granted to any authenticated user.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
            
        # Write permissions are only allowed to the project creator or members
        if hasattr(obj, 'created_by'):
            is_creator = obj.created_by == request.user
        else:
            is_creator = False
            
        is_member = request.user in obj.members.all()
        
        return is_creator or is_member
