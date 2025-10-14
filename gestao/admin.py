# gestao/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Republica, Conta, ParticipanteConta

# Para mostrar campos customizados do nosso Usuario no admin
class CustomUserAdmin(UserAdmin):
    model = Usuario
    # Adicione 'apelido' e 'republica' nos fieldsets para que apareçam no form de edição
    fieldsets = UserAdmin.fieldsets + (
        ('Campos Personalizados', {'fields': ('apelido', 'republica')}),
    )

@admin.register(Republica)
class RepublicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'adm')
    search_fields = ('nome',)

@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome_conta', 'republica', 'valor_total', 'data_vencimento', 'status_conta')
    list_filter = ('status_conta', 'republica', 'tipo')
    search_fields = ('nome_conta',)

@admin.register(ParticipanteConta)
class ParticipanteContaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'conta', 'valor_individual', 'status_pagamento')
    list_filter = ('status_pagamento',)
    search_fields = ('usuario__username', 'conta__nome_conta')

# Desregistra o UserAdmin padrão e registra o nosso customizado
admin.site.register(Usuario, CustomUserAdmin)