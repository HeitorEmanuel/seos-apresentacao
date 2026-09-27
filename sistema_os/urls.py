from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from ordens import views
from ordens.forms import CPFAuthenticationForm

urlpatterns = [
    path('accounts/login/', LoginView.as_view(authentication_form=CPFAuthenticationForm), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('redirecionar/', views.redirecionar_usuario, name='redirecionar'),
    path('', include('ordens.urls')),
]
