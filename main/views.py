from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from usuarios.models import Usuario

# Create your views here.

def BienvenidaView(request):
    return render(request, 'bienvenida.html')


@login_required
def DashboardView(request):
    return render(request, 'dashboard.html')