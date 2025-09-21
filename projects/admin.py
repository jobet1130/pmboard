from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import Project, ProjectLabel


class ProjectLabelInline(admin.TabularInline):
    """Inline admin for project labels."""
    model = ProjectLabel
    extra = 1
    fields = ['name', 'color', 'created_at']
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin configuration for the Project model."""
    list_display = (
        'name', 
        'status', 
        'priority',
        'created_by_link',
        'formatted_start_date',
        'formatted_end_date',
        'member_count'
    )
    list_filter = ['status', 'priority', 'created_at', 'start_date', 'end_date']
    search_fields = ['name', 'description', 'created_by__username', 'created_by__email']
    list_select_related = ['created_by']
    list_per_page = 20
    date_hierarchy = 'created_at'
    inlines = [ProjectLabelInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'created_by')
        }),
        (_('Dates'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority')
        }),
        (_('Members'), {
            'classes': ('collapse',),
            'fields': ('members',)
        }),
        (_('Timestamps'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['members']
    
    def created_by_link(self, obj):
        """Create a link to the user's admin change page."""
        if obj.created_by:
            url = reverse('admin:accounts_customuser_change', args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.created_by)
        return "-"
    created_by_link.short_description = _('Created By')
    created_by_link.admin_order_field = 'created_by__username'
    
    def created_at_formatted(self, obj):
        """Format the created_at date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_formatted.short_description = _('Created At')
    created_at_formatted.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        """Optimize database queries."""
        return super().get_queryset(request).select_related('created_by').prefetch_related('members')
    
    def formatted_start_date(self, obj):
        """Format the start date for display in the admin list."""
        return obj.start_date.strftime('%Y-%m-%d') if obj.start_date else "-"
    formatted_start_date.short_description = 'Start Date'
    formatted_start_date.admin_order_field = 'start_date'
    
    def formatted_end_date(self, obj):
        """Format the end date for display in the admin list."""
        return obj.end_date.strftime('%Y-%m-%d') if obj.end_date else "-"
    formatted_end_date.short_description = 'End Date'
    formatted_end_date.admin_order_field = 'end_date'
    
    def member_count(self, obj):
        """Return the count of members in the project."""
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(ProjectLabel)
class ProjectLabelAdmin(admin.ModelAdmin):
    """Admin configuration for the ProjectLabel model."""
    list_display = ('name', 'project_link', 'color', 'color_preview')
    list_filter = ['project']
    search_fields = ['name', 'project__name']
    list_select_related = ['project']
    
    def color_preview(self, obj):
        """Display a preview of the color."""
        if obj.color:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.color
            )
        return ""
    color_preview.short_description = 'Color Preview'
    
    def project_link(self, obj):
        """Create a link to the project's admin change page."""
        if obj.project:
            url = reverse('admin:projects_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return "-"
    project_link.short_description = _('Project')
    project_link.admin_order_field = 'project__name'
    
    def created_at_formatted(self, obj):
        """Format the created_at date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_formatted.short_description = _('Created At')
    created_at_formatted.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        """Optimize database queries."""
        return super().get_queryset(request).select_related('project')
