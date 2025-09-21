from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsProjectMember(BasePermission):
    """
    Permission to check if the user is a member of the project that the task belongs to.
    Also provides object-level permission checking.
    """
    
    def has_permission(self, request, view):
        # Allow list/create actions to be handled by the view's get_queryset
        if view.action in ['list', 'create']:
            return True
            
        # For other actions, we'll check object-level permissions
        return True
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For write operations, check if user has appropriate permissions
        user = request.user
        if not user.is_authenticated:
            return False
            
        # Project members can modify tasks
        if user in obj.project.members.all():
            return True
            
        # Task creator can modify their own tasks
        if hasattr(obj, 'created_by') and obj.created_by == user:
            return True
            
        # Assigned users can update task status and add comments
        if request.method in ['PATCH', 'PUT'] and user in obj.assigned_to.all():
            # Only allow status updates and comments from assigned users
            allowed_fields = {'status', 'comments'}
            if all(field in allowed_fields for field in request.data.keys()):
                return True
                
        return False


class IsProjectAdmin(BasePermission):
    """
    Permission to check if the user is an admin of the project.
    """
    def has_permission(self, request, view):
        # Check if this is a project-specific action
        project_id = view.kwargs.get('project_pk') or request.data.get('project')
        if not project_id:
            return False
            
        from projects.models import ProjectMembership
        return ProjectMembership.objects.filter(
            project_id=project_id,
            user=request.user,
            role=ProjectMembership.Role.ADMIN
        ).exists()


class IsTaskAssigneeOrCreator(BasePermission):
    """
    Permission to check if the user is assigned to the task or is the creator.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            user == obj.created_by or
            user in obj.assigned_to.all()
        )


class IsTaskProjectMemberOrCreator(BasePermission):
    """
    Permission that allows read access to all users but only allows write access to:
    - Project members (for creating tasks in the project)
    - Task creator (for updating their own tasks)
    - Project members (for updating tasks in their projects)
    """
    
    def has_permission(self, request, view):
        # Allow read-only for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For write operations, user must be authenticated
        if not request.user.is_authenticated:
            return False
            
        # For task creation, check if user is a member of the project
        if view.action == 'create':
            project_id = None
            if hasattr(request, 'data') and 'project' in request.data:
                project_id = request.data.get('project')
            elif hasattr(request, 'POST') and 'project' in request.POST:
                project_id = request.POST.get('project')
                
            if not project_id:
                return False
                
            try:
                from projects.models import Project
                project = Project.objects.get(id=project_id)
                return request.user in project.members.all()
            except (Project.DoesNotExist, ValueError):
                return False
                
        return True  # Object-level permission will handle other cases
    
    def has_object_permission(self, request, view, obj):
        # Allow read-only for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # For write operations, user must be authenticated
        if not request.user.is_authenticated:
            return False
            
        # Allow if user is the task creator
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
            
        # Allow if user is a member of the project
        if hasattr(obj, 'project') and request.user in obj.project.members.all():
            return True
            
        return False


def has_project_permission(user, project, required_permission):
    """
    Helper function to check project permissions.
    """
    if not user.is_authenticated:
        return False
        
    # Superusers have all permissions
    if user.is_superuser:
        return True
        
    # Check project membership and role
    membership = project.memberships.filter(user=user).first()
    if not membership:
        return False
        
    # Map permission levels to role requirements
    permission_levels = {
        'view': True,  # All members can view
        'edit': membership.role in ['ADMIN', 'MEMBER'],
        'delete': membership.role == 'ADMIN',
    }
    
    return permission_levels.get(required_permission, False)
