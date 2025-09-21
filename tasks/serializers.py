from rest_framework import serializers
from django.utils import timezone
from .models import Task, TaskStatus, TaskPriority
from projects.models import Project
from projects.serializers import ProjectSerializer
from accounts.serializers import UserSerializer


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task listings."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    status_choices = serializers.SerializerMethodField()
    priority_choices = serializers.SerializerMethodField()
    
    def get_is_overdue(self, obj):
        return obj.due_date < timezone.now().date() if obj.due_date else False
        
    def get_status_choices(self, obj):
        return [{'value': status[0], 'label': status[1]} for status in TaskStatus.choices]
        
    def get_priority_choices(self, obj):
        return [{'value': priority[0], 'label': priority[1]} for priority in TaskPriority.choices]
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'status_display', 'status_choices',
            'priority', 'priority_display', 'priority_choices', 
            'due_date', 'is_overdue'
        ]
        read_only_fields = ['id']


class TaskDependencySerializer(serializers.ModelSerializer):
    """Serializer for task dependencies (nested)."""
    class Meta:
        model = Task
        fields = ['id', 'title', 'status']
        read_only_fields = fields


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for task CRUD operations."""
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        write_only=True
    )
    project_details = ProjectSerializer(source='project', read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(many=True, read_only=True)
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Task._meta.get_field('assigned_to').remote_field.model.objects.all(),
        source='assigned_to',
        required=False,
        default=[]
    )
    parent_task = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        required=False,
        allow_null=True
    )
    parent_task_details = TaskListSerializer(source='parent_task', read_only=True)
    subtasks = TaskListSerializer(many=True, read_only=True)
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Task.objects.all(),
        required=False
    )
    dependency_details = TaskDependencySerializer(
        source='dependencies',
        many=True,
        read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'start_date', 'due_date',
            'project', 'project_details', 'created_by', 'assigned_to', 'assigned_to_ids',
            'parent_task', 'parent_task_details', 'subtasks',
            'dependencies', 'dependency_details', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'subtasks', 'dependency_details', 'parent_task_details'
        ]

    def validate(self, data):
        """
        Validate the task data.
        - Ensure due_date is not before start_date
        - Ensure dependencies belong to the same project
        """
        instance = self.instance
        project = data.get('project', instance.project if instance else None)
        start_date = data.get('start_date', instance.start_date if instance else None)
        due_date = data.get('due_date', instance.due_date if instance else None)
        dependencies = data.get('dependencies', [])
        
        # Check if due_date is before start_date
        if start_date and due_date and due_date < start_date:
            raise serializers.ValidationError({
                'due_date': 'Due date cannot be before start date.'
            })
        
        # Check if dependencies belong to the same project
        if project and dependencies:
            invalid_deps = [str(dep.id) for dep in dependencies if dep.project_id != project.id]
            if invalid_deps:
                raise serializers.ValidationError({
                    'dependencies': f'The following tasks do not belong to this project: {", ".join(invalid_deps)}'
                })
        
        return data
    
    def create(self, validated_data):
        """Create a new task with the validated data."""
        # Extract many-to-many and foreign key data
        assigned_to = validated_data.pop('assigned_to', [])
        dependencies = validated_data.pop('dependencies', [])
        
        # Set created_by to the current user if not provided
        if 'created_by' not in validated_data:
            validated_data['created_by'] = self.context['request'].user
        
        # Create the task
        task = Task.objects.create(**validated_data)
        
        # Set many-to-many relationships
        task.assigned_to.set(assigned_to)
        task.dependencies.set(dependencies)
        
        return task
    
    def update(self, instance, validated_data):
        """Update an existing task with the validated data."""
        # Extract many-to-many and foreign key data
        assigned_to = validated_data.pop('assigned_to', None)
        dependencies = validated_data.pop('dependencies', None)
        
        # Update the task fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance to ensure we have an ID for many-to-many relationships
        instance.save()
        
        # Update many-to-many relationships if provided
        if assigned_to is not None:
            instance.assigned_to.set(assigned_to)
        
        if dependencies is not None:
            instance.dependencies.set(dependencies)
        
        return instance


# Alias for backward compatibility
TaskSerializer = TaskDetailSerializer
