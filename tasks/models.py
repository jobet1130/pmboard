import uuid
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class TaskStatus(models.TextChoices):
    """Status choices for tasks."""
    TODO = 'todo', 'To Do'
    IN_PROGRESS = 'in_progress', 'In Progress'
    IN_REVIEW = 'in_review', 'In Review'
    BLOCKED = 'blocked', 'Blocked'
    COMPLETED = 'completed', 'Completed'


class TaskPriority(models.TextChoices):
    """Priority levels for tasks."""
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'


class Task(models.Model):
    """Model representing a task in the project management system."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    assigned_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True
    )
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_tasks'
    )
    
    # Task details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completion_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[validators.MinValueValidator(0), validators.MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """Validate model fields."""
        super().clean()
        
        # Ensure due_date is not before start_date if both are set
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValidationError({
                'due_date': 'Due date cannot be before start date.'
            })
        
        # Ensure parent task belongs to the same project
        if self.parent_task and self.parent_task.project_id != self.project_id:
            raise ValidationError({
                'parent_task': 'Parent task must belong to the same project.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to include full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if not self.due_date:
            return False
        return self.due_date < timezone.now().date() and self.status != TaskStatus.COMPLETED

    def add_dependency(self, task):
        """Add a task as a dependency."""
        if task == self:
            raise ValidationError('A task cannot depend on itself.')
        if task in self.dependencies.all():
            return
        self.dependencies.add(task)
    
    def remove_dependency(self, task):
        """Remove a task dependency."""
        self.dependencies.remove(task)

    def get_all_dependencies(self, include_self=False):
        """Get all dependencies recursively."""
        dependencies = set()
        
        def _get_deps(task):
            for dep in task.dependencies.all():
                if dep not in dependencies:
                    dependencies.add(dep)
                    _get_deps(dep)
        
        if include_self:
            dependencies.add(self)
        
        _get_deps(self)
        return dependencies
        
    def calculate_completion_percentage(self):
        """
        Calculate the completion percentage of the task.
        If the task has subtasks, the completion percentage is the average of all subtasks.
        Otherwise, it returns the task's own completion_percentage.
        """
        subtasks = self.subtasks.all()
        if not subtasks:
            return self.completion_percentage
            
        total_percentage = 0
        valid_subtasks = 0
        
        for subtask in subtasks:
            # Recursively calculate for subtasks
            subtask_percentage = subtask.calculate_completion_percentage()
            if subtask_percentage is not None:
                total_percentage += subtask_percentage
                valid_subtasks += 1
                
        if valid_subtasks == 0:
            return 0
            
        average_percentage = total_percentage // valid_subtasks
        return min(100, max(0, average_percentage))  # Ensure between 0-100
