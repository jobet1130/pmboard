# Standard library
from datetime import datetime, timedelta

# Django
from django.db.models import Q, Case, When, Value, BooleanField
from django.utils import timezone

# Django REST Framework
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

# Django
from django.contrib.auth import get_user_model

# Local imports
from .models import Task, TaskStatus
from .serializers import TaskSerializer, TaskListSerializer
from .permissions import IsProjectMember

# Get the User model
User = get_user_model()


class TaskFilter(filters.BaseFilterBackend):
    """Custom filter for TaskViewSet."""
    
    def filter_queryset(self, request, queryset, view):
        # Filter by status
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        # Filter by priority
        priority_param = request.query_params.get('priority')
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
            
        # Filter by due_date (before or on the specified date)
        due_date_param = request.query_params.get('due_date')
        if due_date_param:
            try:
                due_date = datetime.strptime(due_date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(due_date__lte=due_date)
            except ValueError:
                pass
                
        # Filter by assigned_to (user ID)
        assigned_to_param = request.query_params.get('assigned_to')
        if assigned_to_param:
            queryset = queryset.filter(assigned_to__id=assigned_to_param)
            
        return queryset


class TaskPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks with advanced filtering and search capabilities.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter, TaskFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['priority', 'due_date', 'created_at']
    ordering = ['-priority', 'due_date']
    pagination_class = TaskPagination
    
    def get_queryset(self):
        """
        Return tasks where the user is a member of the project or is assigned to the task.
        Adds annotations for task status and priority ordering.
        """
        user = self.request.user
        
        # Annotate with status and priority ordering
        status_order = Case(
            When(status=TaskStatus.TODO, then=Value(1)),
            When(status=TaskStatus.IN_PROGRESS, then=Value(2)),
            When(status=TaskStatus.IN_REVIEW, then=Value(3)),
            When(status=TaskStatus.BLOCKED, then=Value(4)),
            When(status=TaskStatus.COMPLETED, then=Value(5)),
            default=Value(6),
            output_field=BooleanField(),
        )
        
        priority_order = Case(
            When(priority='critical', then=Value(1)),
            When(priority='high', then=Value(2)),
            When(priority='medium', then=Value(3)),
            When(priority='low', then=Value(4)),
            default=Value(5),
            output_field=BooleanField(),
        )
        
        # Add due_date_soon flag (due in next 3 days)
        soon = timezone.now().date() + timedelta(days=3)
        
        queryset = Task.objects.annotate(
            status_order=status_order,
            priority_order=priority_order,
            due_soon=Case(
                When(due_date__isnull=False, due_date__lte=soon, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related(
            'project', 'created_by', 'parent_task'
        ).prefetch_related(
            'assigned_to', 'dependencies', 'subtasks'
        ).distinct()
        
        # For list view, only show tasks from projects where user is a member
        if self.action == 'list':
            queryset = queryset.filter(
                Q(project__members=user) | 
                Q(assigned_to=user) |
                Q(created_by=user)
            )
            
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views."""
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """Set the created_by user when creating a task."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_user(self, request, pk=None):
        """Assign a user to this task."""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(pk=user_id)
            if user not in task.assigned_to.all():
                task.assigned_to.add(user)
                return Response({'status': 'user assigned'})
            return Response(
                {'status': 'user already assigned'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def unassign_user(self, request, pk=None):
        """Remove a user from this task."""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(pk=user_id)
            if user in task.assigned_to.all():
                task.assigned_to.remove(user)
                return Response({'status': 'user unassigned'})
            return Response(
                {'status': 'user was not assigned'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Update the status of a task.
        Validates status transitions and updates timestamps accordingly.
        """
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if new_status not in dict(TaskStatus.choices):
            return Response(
                {'error': 'invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status and relevant timestamps
        task.status = new_status
        now = timezone.now()
        
        # Update started_at if transitioning to IN_PROGRESS
        if new_status == TaskStatus.IN_PROGRESS and not task.start_date:
            task.start_date = now.date()
        
        # Update completed_at if transitioning to COMPLETED
        if new_status == TaskStatus.COMPLETED:
            task.completed_at = now
            
        task.save(update_fields=['status', 'start_date', 'completed_at', 'updated_at'])
        
        # Use the serializer to include all task data in the response
        serializer = self.get_serializer(task)
        return Response({
            'status': 'status updated',
            'new_status': task.get_status_display(),
            'task': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        """Add a task as a dependency."""
        task = self.get_object()
        dependency_id = request.data.get('task_id')
        
        if not dependency_id:
            return Response(
                {'error': 'task_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            dependency = Task.objects.get(pk=dependency_id)
            
            # Prevent circular dependencies
            if dependency == task:
                return Response(
                    {'error': 'A task cannot depend on itself'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if dependency is in the same project
            if dependency.project != task.project:
                return Response(
                    {'error': 'Dependency must be in the same project'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            task.dependencies.add(dependency)
            return Response({'status': 'dependency added'})
            
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        """Remove a task dependency."""
        task = self.get_object()
        dependency_id = request.data.get('task_id')
        
        if not dependency_id:
            return Response(
                {'error': 'task_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            dependency = Task.objects.get(pk=dependency_id)
            if dependency in task.dependencies.all():
                task.dependencies.remove(dependency)
                return Response({'status': 'dependency removed'})
            return Response(
                {'status': 'dependency did not exist'},
                status=status.HTTP_200_OK
            )
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Public read access for listing and retrieving tasks.
        Write access requires authentication and project membership.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]  # Or [IsAuthenticated] if auth is required
        else:
            permission_classes = [IsAuthenticated, IsProjectMember]
        return [permission() for permission in permission_classes]


# Additional API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tasks_overview(request):
    """
    Get an overview of the current user's tasks.
    """
    user = request.user
    now = timezone.now()
    
    # Get counts for different task statuses
    tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user)
    ).values('status').annotate(count=models.Count('id'))
    
    # Get overdue tasks
    overdue = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user),
        due_date__lt=now.date(),
        status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
    ).count()
    
    # Get due soon tasks (next 3 days)
    due_soon = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user),
        due_date__range=[now.date(), now.date() + timedelta(days=3)],
        status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS]
    ).count()
    
    return Response({
        'status_counts': {t['status']: t['count'] for t in tasks},
        'overdue_tasks': overdue,
        'due_soon': due_soon,
    })
