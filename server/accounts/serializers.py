from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'phone_number', 
                  'is_two_factor_enabled', 'is_active', 'password', 'last_login')
        read_only_fields = ('id', 'last_login')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        """Update user, setting the password correctly if present."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        """Validate that the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Old password is not correct'))
        return value
    
    def validate_new_password(self, value):
        """Validate the new password using Django's password validation."""
        validate_password(value)
        return value
    
    def validate(self, data):
        """Validate that the new password and confirm password match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _('The two password fields didn\'t match.')
            })
        return data


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for requesting a password reset."""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that a user exists with the given email."""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            # We don't want to reveal whether a user exists or not for security reasons
            pass
        return value
    
    def save(self):
        """Generate a password reset token and send an email."""
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # In a real application, you would send an email here
            # For this example, we'll just print the token and uid
            print(f"Password reset token for {email}: {uid}-{token}")
        except User.DoesNotExist:
            # We don't want to reveal whether a user exists or not
            pass


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset."""
    
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate that the new password and confirm password match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': _('The two password fields didn\'t match.')
            })
        
        try:
            uid = urlsafe_base64_decode(data['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'uid': _('Invalid user ID')
            })
        
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({
                'token': _('Invalid or expired token')
            })
        
        # Validate the new password
        validate_password(data['new_password'], user)
        
        return data
    
    def save(self):
        """Set the new password."""
        uid = urlsafe_base64_decode(self.validated_data['uid']).decode()
        user = User.objects.get(pk=uid)
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
