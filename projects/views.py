from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Project, ProjectLabel, ProjectStatus
from .serializers import (
    ProjectSerializer, 
    ProjectCreateUpdateSerializer,
    ProjectLabelSerializer,
    ProjectLabelCreateSerializer,
    ProjectStatusUpdateSerializer,
    ProjectPriorityUpdateSerializer,
    ProjectMemberSerializer
)
from .permissions import IsProjectMemberOrCreator


class ProjectPagination(PageNumberPagination):
    """Custom pagination for project lists."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects.
    """
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = ProjectPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'priority', 'end_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectSerializer

    def get_queryset(self):
        """
        Return all projects for list view, with optional filtering.
        Actual permission checks are handled in get_permissions.
        """
        queryset = Project.objects.all()

        # Apply status filter
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Apply priority filter
        priority_param = self.request.query_params.get('priority')
        if priority_param:
            queryset = queryset.filter(priority=priority_param)

        # Apply member filter
        member_id = self.request.query_params.get('member')
        if member_id:
            queryset = queryset.filter(members__id=member_id)

        # For list view, only show projects where user is a member or creator
        if self.action == 'list':
            queryset = queryset.filter(
                Q(created_by=self.request.user) | 
                Q(members=self.request.user)
            ).distinct()

        return queryset

    def perform_create(self, serializer):
        """Set the creator of the project."""
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['list']:
            # For list view, only show projects where user is a member or creator
            return [IsAuthenticated()]
        elif self.action in ['retrieve']:
            # For retrieve action, allow any authenticated user to view
            return [IsAuthenticated()]
        else:
            # For other actions (update, partial_update, destroy, etc.), check project membership
            return [IsProjectMemberOrCreator()]
        
    def get_object(self):
        """
        Returns the object the view is displaying.
        For retrieve action, allow access to any authenticated user.
        For other actions, check permissions.
        """
        obj = get_object_or_404(Project, pk=self.kwargs['pk'])
        # For retrieve action, allow access to any authenticated user
        if self.action == 'retrieve':
            return obj
        # For other actions, check permissions
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add members to the project."""
        project = self.get_object()
        serializer = ProjectMemberSerializer(data=request.data)
        
        if serializer.is_valid():
            users = serializer.validated_data['user_ids']
            project.members.add(*users)
            return Response(
                {'detail': 'Members added successfully'}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove members from the project."""
        project = self.get_object()
        serializer = ProjectMemberSerializer(data=request.data)
        
        if serializer.is_valid():
            users = serializer.validated_data['user_ids']
            # Don't allow removing the creator
            users = [user for user in users if user != project.created_by]
            project.members.remove(*users)
            return Response(
                {'detail': 'Members removed successfully'}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def archive_project(self, request, pk=None):
        """Archive the project."""
        project = self.get_object()
        project.status = ProjectStatus.ARCHIVED
        project.save()
        return Response(
            {'detail': 'Project archived successfully'}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update project status."""
        project = self.get_object()
        serializer = ProjectStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            project.status = serializer.validated_data['status']
            project.save()
            return Response(
                {'detail': 'Status updated successfully'}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_priority(self, request, pk=None):
        """Update project priority."""
        project = self.get_object()
        serializer = ProjectPriorityUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            project.priority = serializer.validated_data['priority']
            project.save()
            return Response(
                {'detail': 'Priority updated successfully'}, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectLabelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing project labels.
    """
    serializer_class = ProjectLabelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return labels for the specified project."""
        project_id = self.kwargs.get('project_pk')
        return ProjectLabel.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectLabelCreateSerializer
        return ProjectLabelSerializer

    def perform_create(self, serializer):
        """Set the project for the label."""
        project = get_object_or_404(
            Project.objects.filter(
                Q(created_by=self.request.user) | 
                Q(members=self.request.user)
            ),
            pk=self.kwargs['project_pk']
        )
        serializer.save(project=project)

    def get_permissions(self):
        """Only allow project members to view labels and creators/admins to modify them."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrSelf()]
        return super().get_permissions()
