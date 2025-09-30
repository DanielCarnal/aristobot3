# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialise Aristobot3 avec les utilisateurs de base'
    
    def handle(self, *args, **options):
        with transaction.atomic():
            # Creer l'utilisateur dev (utilisateur normal avec mot de passe)
            if not User.objects.filter(username='dev').exists():
                User.objects.create_user(
                    username='dev',
                    email='dev@aristobot.local',
                    password='dev123',  # Mot de passe pour utilisateur normal
                    first_name='Mode',
                    last_name='Developpement',
                )
                self.stdout.write(
                    self.style.SUCCESS('OK Utilisateur "dev" cree avec mot de passe')
                )
            else:
                self.stdout.write('Utilisateur "dev" existe deja')
            
            # Creer l'utilisateur dac
            if not User.objects.filter(username='dac').exists():
                User.objects.create_user(
                    username='dac',
                    email='daniel.carnal@gmail.com',
                    password='aristobot',
                    first_name='Daniel',
                    last_name='Carnal',
                    is_staff=True,
                    is_superuser=True,
                )
                self.stdout.write(
                    self.style.SUCCESS('OK Utilisateur "dac" cree (superuser)')
                )
            else:
                self.stdout.write('Utilisateur "dac" existe deja')
            
            self.stdout.write(
                self.style.SUCCESS('\nOK Initialisation terminee!')
            )
            
            # Initialiser la table HeartbeatStatus
            from apps.core.models import HeartbeatStatus
            if not HeartbeatStatus.objects.exists():
                HeartbeatStatus.objects.create(
                    is_connected=False,
                    symbols_monitored=['BTC/USDT']  # Symbole par defaut
                )
                self.stdout.write(
                    self.style.SUCCESS('OK Table HeartbeatStatus initialisee')
                )
            
            # Initialiser la table DebugMode
            from apps.auth_custom.models import DebugMode
            if not DebugMode.objects.exists():
                DebugMode.objects.create(
                    is_active=False  # Par defaut desactive
                )
                self.stdout.write(
                    self.style.SUCCESS('OK Table DebugMode initialisee')
                )