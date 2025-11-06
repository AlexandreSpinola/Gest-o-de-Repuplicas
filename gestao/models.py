from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Usuario(AbstractUser):
    class StatusAssociacao(models.TextChoices):
        AGUARDANDO_APROVACAO = 'AGUARDANDO_APROVACAO', 'Aguardando Aprovacao'
        APROVADO = 'APROVADO', 'Aprovado'
        NAO_APROVADO = 'NAO_APROVADO', 'Nao Aprovado'
    
    apelido = models.CharField(max_length=50, blank=True, null=True)
    republica = models.ForeignKey(
        'Republica', 
        on_delete=models.SET_NULL, # Se a república for deletada, o usuário não é.
        null=True, 
        blank=True,
        related_name='moradores' # Nome para acessar os usuários a partir da república
    )
    status_associacao = models.CharField(max_length=20, choices=StatusAssociacao.choices, default=StatusAssociacao.NAO_APROVADO)

    def __str__(self):
        return self.username

class Republica(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    adm = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Aponta para o modelo Usuario
        on_delete=models.CASCADE, # Se o ADM for deletado, a república também é
        related_name='republica_administrada'
    )

    def __str__(self):
        return self.nome

class Conta(models.Model):
    class TipoConta(models.TextChoices):
        FIXA = 'FIXA', 'Fixa'
        VARIAVEL = 'VARIAVEL', 'Variável'

    class StatusConta(models.TextChoices):
        NAO_PAGA = 'NAO_PAGA', 'Não Paga'
        PARCIALMENTE_PAGA = 'PARCIALMENTE_PAGA', 'Parcialmente Paga'
        PAGA = 'PAGA', 'Paga'

    republica = models.ForeignKey(Republica, on_delete=models.CASCADE, related_name='contas')
    nome_conta = models.CharField(max_length=100)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    tipo = models.CharField(max_length=20, choices=TipoConta.choices, default=TipoConta.VARIAVEL)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, # Protege para não deletar um usuário que tem contas sob sua responsabilidade
        related_name='contas_responsaveis'
    )
    status_conta = models.CharField(max_length=20, choices=StatusConta.choices, default=StatusConta.NAO_PAGA)

    def __str__(self):
        return f"{self.nome_conta} - {self.republica.nome}"

class ParticipanteConta(models.Model):
    class StatusPagamento(models.TextChoices):
        NAO_PAGO = 'NAO_PAGO', 'Não Pago'
        CONFIRMACAO_PENDENTE = 'CONFIRMACAO_PENDENTE', 'Confirmação Pendente'
        PAGO = 'PAGO', 'Pago'

    conta = models.ForeignKey(Conta, on_delete=models.CASCADE, related_name='participantes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='participacoes')
    valor_individual = models.DecimalField(max_digits=10, decimal_places=2)
    status_pagamento = models.CharField(max_length=25, choices=StatusPagamento.choices, default=StatusPagamento.NAO_PAGO)

    def __str__(self):
        return f"{self.usuario.username} na conta {self.conta.nome_conta}"