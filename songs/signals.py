from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FanProfile


@receiver(post_save, sender=User)
def create_fan_profile(sender, instance, created, **kwargs):
    if created:
        FanProfile.objects.create(user=instance)