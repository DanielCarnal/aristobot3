from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import base64

class User(AbstractUser):
    """Utilisateur etendu pour Aristobot3"""
    default_broker = models.ForeignKey(
        'brokers.Broker', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='default_for_users'
    )
    
    # Configuration IA
    ai_provider = models.CharField(
        max_length=20,
        choices=[
            ('openrouter', 'OpenRouter'),
            ('ollama', 'Ollama'),
            ('none', 'Aucun')
        ],
        default='none'
    )
    ai_enabled = models.BooleanField(default=False)
    ai_api_key = models.TextField(blank=True, null=True)  # Sera chiffre
    ai_endpoint_url = models.URLField(
        default='http://localhost:11434',
        blank=True
    )
    
    # Preferences d'affichage
    theme = models.CharField(
        max_length=10,
        choices=[
            ('dark', 'Sombre'),
            ('light', 'Clair'),
        ],
        default='dark'
    )
    display_timezone = models.CharField(
        max_length=50,
        choices=[
            ('UTC', 'UTC'),
            ('local', 'Fuseau horaire local'),
        ],
        default='local'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Chiffrer l'API key avant sauvegarde
        if self.ai_api_key and not self.ai_api_key.startswith('gAAAA'):
            self.ai_api_key = self.encrypt_api_key(self.ai_api_key)
        super().save(*args, **kwargs)
    
    def encrypt_api_key(self, raw_key):
        """Chiffre une cle API"""
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.encrypt(raw_key.encode()).decode()
    
    def decrypt_api_key(self):
        """Dechiffre la cle API"""
        if not self.ai_api_key or not self.ai_api_key.startswith('gAAAA'):
            return self.ai_api_key
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32)[:32])
        f = Fernet(key)
        return f.decrypt(self.ai_api_key.encode()).decode()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'