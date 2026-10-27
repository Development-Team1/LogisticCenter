from django.contrib import admin

from .models import Cliente, Empleado

admin.site.register(Empleado)
admin.site.register(Cliente)
