from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Profile, Role, AuditLog

# Get the custom user model
User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('role', 'phone_number', 'timezone', 'department', 'position', 'location', 'profile_picture_preview')
    readonly_fields = ('profile_picture_preview',)

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;" />', obj.profile_picture.url)
        return "No image"
    profile_picture_preview.short_description = 'Profile Picture Preview'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'get_role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = (ProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    def get_role(self, obj):
        if hasattr(obj, 'profile') and obj.profile.role:
            return obj.profile.role.name
        return "No role"
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role__name'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'department', 'position')
    list_filter = ('role', 'department', 'position')
    search_fields = ('user__username', 'user__email', 'phone_number', 'department', 'position')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_permissions_count', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions Count'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user_display', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__email', 'user__username', 'ip_address', 'action')
    readonly_fields = ('user', 'action', 'ip_address', 'user_agent', 'timestamp', 'metadata_preview')
    date_hierarchy = 'timestamp'
    
    def user_display(self, obj):
        if obj.user:
            url = reverse("admin:accounts_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return "System"
    user_display.short_description = 'User'
    
    def metadata_preview(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', str(obj.metadata))
        return "No metadata"
    metadata_preview.short_description = 'Metadata'