from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class Usuario(AbstractUser):
    user_id = models.AutoField(primary_key=True)

    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'





