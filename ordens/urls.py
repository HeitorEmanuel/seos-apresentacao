from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ordens, name='lista_ordens'),
    path('tema-atual/', views.tema_atual, name='tema_atual'),
    path('salvar-tema/', views.salvar_tema, name='salvar_tema'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
]