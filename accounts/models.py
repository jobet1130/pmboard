import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()


class Role(models.Model):
    class RoleName(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        MANAGER = 'manager', _('Manager')
        DEVELOPER = 'developer', _('Developer')
        CLIENT = 'client', _('Client')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        _('role name'),
        max_length=50,
        choices=RoleName.choices,
        unique=True
    )
    description = models.TextField(_('description'), blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
        related_name='role_permissions'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class Profile(models.Model):
    class TimezoneChoices(models.TextChoices):
        UTC = 'UTC', 'UTC (Coordinated Universal Time)'
        GMT = 'GMT', 'GMT (Greenwich Mean Time)'
        EST = 'EST', 'EST (Eastern Standard Time)'
        EDT = 'EDT', 'EDT (Eastern Daylight Time)'
        CT = 'CT', 'CT (Central Time)'
        MT = 'MT', 'MT (Mountain Time)'
        PT = 'PT', 'PT (Pacific Time)'
        AEST = 'AEST', 'AEST (Australian Eastern Standard Time)'
        AEDT = 'AEDT', 'AEDT (Australian Eastern Daylight Time)'
        BST = 'BST', 'BST (British Summer Time)'
        CET = 'CET', 'CET (Central European Time)'
        CEST = 'CEST', 'CEST (Central European Summer Time)'
        EET = 'EET', 'EET (Eastern European Time)'
        EEST = 'EEST', 'EEST (Eastern European Summer Time)'
        IST = 'IST', 'IST (Indian Standard Time)'
        JST = 'JST', 'JST (Japan Standard Time)'
        KST = 'KST', 'KST (Korea Standard Time)'
        CST_CN = 'CST_CN', 'CST (China Standard Time)'
        HKT = 'HKT', 'HKT (Hong Kong Time)'
        SGT = 'SGT', 'SGT (Singapore Time)'
        WET = 'WET', 'WET (Western European Time)'
        WEST = 'WEST', 'WEST (Western European Summer Time)'
        MSK = 'MSK', 'MSK (Moscow Standard Time)'
        SAST = 'SAST', 'SAST (South Africa Standard Time)'
        NST = 'NST', 'NST (Newfoundland Standard Time)'
        HST = 'HST', 'HST (Hawaii Standard Time)'
        AKST = 'AKST', 'AKST (Alaska Standard Time)'
        CHST = 'CHST', 'CHST (Chamorro Standard Time)'
        SST = 'SST', 'SST (Samoa Standard Time)'
        NZST = 'NZST', 'NZST (New Zealand Standard Time)'
        NZDT = 'NZDT', 'NZDT (New Zealand Daylight Time)'
        
    class LanguageChoices(models.TextChoices):
        EN = 'en', _('English')
        ES = 'es', _('Spanish')
        FR = 'fr', _('French')
        DE = 'de', _('German')
        IT = 'it', _('Italian')
        PT = 'pt', _('Portuguese')
        RU = 'ru', _('Russian')
        ZH = 'zh', _('Chinese')
        JA = 'ja', _('Japanese')
        KO = 'ko', _('Korean')
        AR = 'ar', _('Arabic')
        HI = 'hi', _('Hindi')
        BN = 'bn', _('Bengali')
        PA = 'pa', _('Punjabi')
        TR = 'tr', _('Turkish')
        NL = 'nl', _('Dutch')
        SV = 'sv', _('Swedish')
        FI = 'fi', _('Finnish')
        DA = 'da', _('Danish')
        NO = 'no', _('Norwegian')
        PL = 'pl', _('Polish')
        UK = 'uk', _('Ukrainian')
        TH = 'th', _('Thai')
        VI = 'vi', _('Vietnamese')
        ID = 'id', _('Indonesian')
        MS = 'ms', _('Malay')
        FIL = 'fil', _('Filipino')
        

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    bio = models.TextField(_('biography'), blank=True)
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        choices=TimezoneChoices.choices,
        default=TimezoneChoices.UTC
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        verbose_name=_('role')
    )
    department = models.CharField(_('department'), max_length=100, blank=True)
    position = models.CharField(_('position'), max_length=100, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=LanguageChoices.choices,
        default=LanguageChoices.EN
    )
    two_factor_enabled = models.BooleanField(
        _('two factor authentication'),
        default=False,
        help_text=_('Designates whether the user has enabled two-factor authentication.')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return f'{self.user.email}\'s Profile'


class AuditLog(models.Model):
    class ActionChoices(models.TextChoices):
        LOGIN = 'login', _('User Login')
        LOGOUT = 'logout', _('User Logout')
        PASSWORD_CHANGE = 'password_change', _('Password Changed')
        PROFILE_UPDATE = 'profile_update', _('Profile Updated')
        ROLE_UPDATE = 'role_update', _('Role Updated')
        PERMISSION_UPDATE = 'permission_update', _('Permission Updated')
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('user')
    )
    action = models.CharField(
        _('action'),
        max_length=50,
        choices=ActionChoices.choices
    )
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)

    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f'{self.get_action_display()} - {self.user} - {self.timestamp}'