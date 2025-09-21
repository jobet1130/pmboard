from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Project, ProjectLabel, ProjectStatus, ProjectPriority

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details in project responses."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ProjectLabelSerializer(serializers.ModelSerializer):
    """Serializer for project labels."""
    class Meta:
        model = ProjectLabel
        fields = ['id', 'name', 'color', 'project', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'project': {'write_only': True}
        }


class ProjectLabelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating project labels."""
    class Meta:
        model = ProjectLabel
        fields = ['id', 'name', 'color', 'project']
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for project details."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    created_by = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=User.objects.all(),
        source='members'
    )
    labels = ProjectLabelSerializer(many=True, read_only=True)
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'start_date', 'end_date',
            'created_by', 'members', 'member_ids', 'labels', 'created_at',
            'updated_at', 'is_creator'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'is_creator']
        extra_kwargs = {
            'status': {'write_only': True},
            'priority': {'write_only': True}
        }
    
    def get_is_creator(self, obj):
        """Check if the current user is the creator of the project."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.created_by == request.user
        return False
    
    def validate(self, data):
        """Validate project data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
            
        return data
    
    def create(self, validated_data):
        """Create a new project and add the creator as a member."""
        members = validated_data.pop('members', [])
        project = Project.objects.create(**validated_data)
        
        # Add members to the project (including the creator)
        project.members.set(members)
        if project.created_by not in project.members.all():
            project.members.add(project.created_by)
            
        return project


class ProjectCreateUpdateSerializer(ProjectSerializer):
    """Serializer for creating and updating projects."""
    class Meta(ProjectSerializer.Meta):
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},
            'status': {'required': True},
            'priority': {'required': True}
        }


class ProjectStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating project status."""
    status = serializers.ChoiceField(choices=ProjectStatus.choices)
    
    def validate_status(self, value):
        """Validate the status value."""
        if value not in dict(ProjectStatus.choices):
            raise serializers.ValidationError("Invalid status value.")
        return value


class ProjectPriorityUpdateSerializer(serializers.Serializer):
    """Serializer for updating project priority."""
    priority = serializers.ChoiceField(choices=ProjectPriority.choices)
    
    def validate_priority(self, value):
        """Validate the priority value."""
        if value not in dict(ProjectPriority.choices):
            raise serializers.ValidationError("Invalid priority value.")
        return value


class ProjectMemberSerializer(serializers.Serializer):
    """Serializer for adding/removing project members."""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    
    def validate_user_ids(self, value):
        """Validate that the users exist."""
        users = User.objects.filter(id__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("One or more users not found.")
        return users