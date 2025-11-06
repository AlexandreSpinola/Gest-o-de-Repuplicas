# gestao/urls.py
from django.urls import path
from .views import (
    DashboardView, 
    MarcarComoPagoView,
    RepublicaCreateView,
    RepublicaListView,
    SolicitarEntradaRepublicaView,
    AprovarMoradorView,          # <-- ADICIONE ESTE
    RejeitarMoradorView,          # <-- ADICIONE ESTE
    ContaCreateView,
    ConfirmarPagamentoView,  # <-- ADICIONE
    RejeitarPagamentoView,   # <-- ADICIONE
    ContaDeleteView,
    RemoverMoradorView
)

app_name = 'gestao'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('marcar-pago/<int:pk>/', MarcarComoPagoView.as_view(), name='marcar_pago'),
    
    # NOVAS ROTAS
    path('republica/nova/', RepublicaCreateView.as_view(), name='republica_nova'),
    path('republicas/', RepublicaListView.as_view(), name='republica_list'),
    path('republicas/solicitar/<int:pk>/', SolicitarEntradaRepublicaView.as_view(), name='solicitar_entrada'),
    path('aprovar-morador/<int:pk>/', AprovarMoradorView.as_view(), name='aprovar_morador'),
    path('rejeitar-morador/<int:pk>/', RejeitarMoradorView.as_view(), name='rejeitar_morador'),
    path('conta/nova/', ContaCreateView.as_view(), name='conta_nova'),
    path('confirmar-pagamento/<int:pk>/', ConfirmarPagamentoView.as_view(), name='confirmar_pagamento'),
    path('rejeitar-pagamento/<int:pk>/', RejeitarPagamentoView.as_view(), name='rejeitar_pagamento'),
    path('conta/deletar/<int:pk>/', ContaDeleteView.as_view(), name='conta_delete'),
    path('remover-morador/<int:pk>/', RemoverMoradorView.as_view(), name='remover_morador'),
]