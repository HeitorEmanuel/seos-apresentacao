from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ordens, name='lista_ordens'),
    path('tecnico/', views.minha_fila, name='minha_fila'),
    path('tecnico/ordens/<int:ordem_id>/', views.detalhe_ordem_tecnico, name='detalhe_ordem_tecnico'),
    path('tecnico/ordens/<int:ordem_id>/atualizar/', views.atualizar_ordem_tecnico, name='atualizar_ordem_tecnico'),
    path('tema-atual/', views.tema_atual, name='tema_atual'),
    path('salvar-tema/', views.salvar_tema, name='salvar_tema'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
]
