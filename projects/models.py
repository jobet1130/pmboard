import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ProjectStatus(models.TextChoices):
    PLANNED = 'PL', _('Planned')
    IN_PROGRESS = 'IP', _('In Progress')
    ON_HOLD = 'OH', _('On Hold')
    COMPLETED = 'CO', _('Completed')
    ARCHIVED = 'AR', _('Archived')


class ProjectPriority(models.TextChoices):
    LOW = 'LOW', _('Low')
    MEDIUM = 'MED', _('Medium')
    HIGH = 'HI', _('High')
    CRITICAL = 'CRIT', _('Critical')


class Project(models.Model):
    """
    Project model representing a project in the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text=_('Name of the project')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Detailed description of the project')
    )
    status = models.CharField(
        max_length=2,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNED,
        help_text=_('Current status of the project')
    )
    priority = models.CharField(
        max_length=4,
        choices=ProjectPriority.choices,
        default=ProjectPriority.MEDIUM,
        help_text=_('Priority level of the project')
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Planned or actual start date of the project')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Planned or actual end date of the project')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_projects',
        help_text=_('User who created the project')
    )
    members = models.ManyToManyField(
        User,
        related_name='projects',
        blank=True,
        help_text=_('Team members working on this project')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'created_by'],
                name='unique_project_name_per_creator',
                violation_error_message=_('You already have a project with this name.')
            ),
            models.CheckConstraint(
                check=models.Q(
                    end_date__isnull=True,
                    start_date__isnull=True
                ) | models.Q(
                    end_date__gte=models.F('start_date')
                ),
                name='end_date_after_start_date',
                violation_error_message=_('End date must be after start date.')
            )
        ]
        indexes = [
            models.Index(fields=['status'], name='project_status_idx'),
            models.Index(fields=['priority'], name='project_priority_idx'),
            models.Index(fields=['created_by'], name='project_created_by_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Ensure the creator is always a member of the project
        super().save(*args, **kwargs)
        if self.created_by not in self.members.all():
            self.members.add(self.created_by)


class ProjectLabel(models.Model):
    """
    Label model for categorizing projects.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(2)],
        help_text=_('Name of the label')
    )
    color = models.CharField(
        max_length=7,
        default='#808080',  # Default to gray
        help_text=_('Hex color code for the label (e.g., #FF0000 for red)')
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='labels',
        help_text=_('Project this label belongs to')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Project Label')
        verbose_name_plural = _('Project Labels')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'project'],
                name='unique_label_name_per_project',
                violation_error_message=_('A label with this name already exists in this project.')
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.project.name})"
