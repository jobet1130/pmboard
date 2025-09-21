from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from .models import Task, TaskStatus


class SubtaskInline(admin.TabularInline):
    """Inline for viewing and editing subtasks."""
    model = Task
    fk_name = 'parent_task'
    fields = ('title', 'status', 'priority', 'due_date', 'created_by')
    readonly_fields = ('created_by',)
    extra = 0
    show_change_link = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for managing tasks."""
    list_display = (
        'title', 
        'project_link', 
        'status_badge', 
        'priority_display', 
        'due_date', 
        'created_by_link',
        'subtasks_count',
    )
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
    list_select_related = ('project', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by_link')
    date_hierarchy = 'due_date'
    inlines = [SubtaskInline]
    
    fieldsets = (
        ('Task Details', {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        ('Dates', {
            'fields': ('start_date', 'due_date')
        }),
        ('Relationships', {
            'fields': ('project', 'parent_task', 'dependencies', 'assigned_to')
        }),
        ('Metadata', {
            'fields': ('created_by_link', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('assigned_to', 'dependencies')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            subtasks_count=Count('subtasks')
        )
    
    def project_link(self, obj):
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return "-"
    project_link.short_description = 'Project'
    project_link.admin_order_field = 'project__name'
    
    def created_by_link(self, obj):
        if obj.created_by:
            url = reverse('admin:accounts_user_change', args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by.get_full_name() or obj.created_by.username)
        return "-"
    created_by_link.short_description = 'Created By'
    created_by_link.admin_order_field = 'created_by__username'
    
    def status_badge(self, obj):
        status_colors = {
            TaskStatus.TODO: 'gray',
            TaskStatus.IN_PROGRESS: 'blue',
            TaskStatus.IN_REVIEW: 'orange',
            TaskStatus.BLOCKED: 'red',
            TaskStatus.COMPLETED: 'green',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span class="status-badge" style="'
            'display: inline-block; '
            'padding: 2px 8px; '
            'border-radius: 10px; '
            'background-color: {}; '
            'color: white; '
            'font-size: 12px; '
            'font-weight: 500;"'
            '>{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_display(self, obj):
        priority_colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'critical': 'red',
        }
        color = priority_colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.get_priority_display().title()
        )
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def subtasks_count(self, obj):
        return obj.subtasks_count
    subtasks_count.short_description = 'Subtasks'
    subtasks_count.admin_order_field = 'subtasks_count'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by during the first save
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('css/admin/task_admin.css',)
        }
        js = ('js/admin/task_admin.js',)
