from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ordens, name='lista_ordens'),
    path('notificacoes/', views.notificacoes, name='notificacoes'),
    path('notificacoes/<int:notificacao_id>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('anexos/<int:anexo_id>/baixar/', views.baixar_anexo, name='baixar_anexo'),
    path('ordens/<int:ordem_id>/anexos/', views.anexos_ordem, name='anexos_ordem'),
    path('anexos/<int:anexo_id>/excluir/', views.excluir_anexo, name='excluir_anexo'),
    path('relatorios/', views.relatorios_administrativos, name='relatorios_administrativos'),
    path('relatorios/csv/', views.relatorios_csv, name='relatorios_csv'),
    path('relatorios/pdf/', views.relatorios_pdf, name='relatorios_pdf'),
    path('tecnico/', views.minha_fila, name='minha_fila'),
    path('tecnico/ordens/<int:ordem_id>/', views.detalhe_ordem_tecnico, name='detalhe_ordem_tecnico'),
    path('tecnico/ordens/<int:ordem_id>/atualizar/', views.atualizar_ordem_tecnico, name='atualizar_ordem_tecnico'),
    path('tema-atual/', views.tema_atual, name='tema_atual'),
    path('salvar-tema/', views.salvar_tema, name='salvar_tema'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
]
