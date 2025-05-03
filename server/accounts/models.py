from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for the User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email as the unique identifier."""
    
    ROLE_CHOICES = (
        ('admin', _('Admin')),
        ('manager', _('Manager')),
        ('accountant', _('Accountant')),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='accountant')
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )
    phone_number = models.CharField(_('phone number'), validators=[phone_regex], max_length=17, blank=True)
    is_two_factor_enabled = models.BooleanField(_('two-factor authentication'), default=False)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_accountant(self):
        return self.role == 'accountant'


class UserLoginHistory(models.Model):
    """Model to track user login history for security purposes."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_datetime = models.DateTimeField(_('login datetime'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'), blank=True, null=True)
    device_type = models.CharField(_('device type'), max_length=50, blank=True, null=True)
    login_status = models.BooleanField(_('login status'), default=True)
    
    class Meta:
        verbose_name = _('user login history')
        verbose_name_plural = _('user login histories')
        ordering = ['-login_datetime']
    
    def __str__(self):
        return f"{self.user.email} - {self.login_datetime}"
