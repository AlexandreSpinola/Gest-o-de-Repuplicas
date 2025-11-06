# gestao/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages # Para dar feedback ao usuário
from .models import Conta, ParticipanteConta, Republica, Usuario
from .forms import CustomUserCreationForm ,ContaCreateForm
from datetime import date # Vamos usar para verificar contas atrasadas
from django.db.models import Q 

# View de Registro (Você já tem essa)
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'


class DashboardView(LoginRequiredMixin, ListView):
    model = ParticipanteConta
    template_name = 'gestao/dashboard.html'
    context_object_name = 'lista_pendencias'

    def get_queryset(self):
        """
        MUDANÇA: Busca TODAS as participações do usuário,
        e não apenas as 'NAO_PAGO'.
        Ordena por status e depois por vencimento.
        """
        queryset = ParticipanteConta.objects.filter(
            usuario=self.request.user
        ).select_related('conta').order_by('status_pagamento', 'conta__data_vencimento')
        # 'status_pagamento' vai ordenar 'CONFIRMACAO_PENDENTE' e 'NAO_PAGO' primeiro
        
        return queryset

    def get_context_data(self, **kwargs):
        """ Adiciona dados extras ao template """
        context = super().get_context_data(**kwargs)
        context['hoje'] = date.today()
        
        user = self.request.user

        # Painel do ADM (aprovar novos moradores) - VOCÊ JÁ TEM ISSO
        if user.republica and user == user.republica.adm:
            solicitacoes = Usuario.objects.filter(
                republica=user.republica,
                status_associacao=Usuario.StatusAssociacao.AGUARDANDO_APROVACAO
            )
            context['lista_solicitacoes'] = solicitacoes

        # NOVO: Painel do RESPONSÁVEL (confirmar pagamentos)
        # Busca todas as participações onde:
        # 1. O status é 'CONFIRMACAO_PENDENTE'
        # 2. O usuário logado (user) é o 'responsavel' da conta associada
        confirmacoes_pendentes = ParticipanteConta.objects.filter(
            status_pagamento=ParticipanteConta.StatusPagamento.CONFIRMACAO_PENDENTE,
            conta__responsavel=user
        ).select_related('usuario', 'conta')
        # .select_related() é para performance, para buscar dados do usuário e da conta
        
        context['lista_confirmacoes_pendentes'] = confirmacoes_pendentes

        return context


# NOVO: Esta view cuida do clique no botão "Paguei"
class MarcarComoPagoView(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        pk_participacao = self.kwargs.get('pk')
        participacao = get_object_or_404(ParticipanteConta, pk=pk_participacao)

        # Checagem de segurança (igual a antes)
        if participacao.usuario != request.user:
            messages.error(request, 'Acesso não autorizado.')
            return redirect('gestao:dashboard')

        if participacao.status_pagamento == 'NAO_PAGO':
            
            # MUDANÇA: Lógica de auto-aprovação
            # O usuário logado é o responsável (dono) da conta?
            if request.user == participacao.conta.responsavel:
                participacao.status_pagamento = ParticipanteConta.StatusPagamento.PAGO
                participacao.save()
                messages.success(request, 'Seu pagamento (como responsável) foi confirmado.')
            else:
                # Se não for o dono, entra na fila de confirmação (como antes)
                participacao.status_pagamento = ParticipanteConta.StatusPagamento.CONFIRMACAO_PENDENTE
                participacao.save()
                messages.success(request, 'Pagamento marcado! Aguardando confirmação do responsável.')
        
        else:
            messages.warning(request, 'Esta ação não pôde ser executada.')

        return redirect('gestao:dashboard')
    
class RepublicaCreateView(LoginRequiredMixin, CreateView):
    model = Republica
    fields = ['nome'] # O usuário só precisa digitar o nome
    template_name = 'gestao/republica_form.html'
    success_url = reverse_lazy('gestao:dashboard') # Volta para a dashboard

    def form_valid(self, form):
        # 1. Antes de salvar, define o usuário logado como ADM
        form.instance.adm = self.request.user
        
        # 2. Salva a nova república
        response = super().form_valid(form)
        
        # 3. Atualiza o *próprio* usuário para que ele pertença a esta república
        #    que ele acabou de criar.
        user = self.request.user
        user.republica = self.object # 'self.object' é a república recém-criada
        user.status_associacao = Usuario.StatusAssociacao.APROVADO
        user.save()
        
        messages.success(self.request, f'República "{self.object.nome}" criada com sucesso!')
        return response

    def get(self, request, *args, **kwargs):
        # Checagem: Se o usuário já tem uma república, não pode criar outra
        if request.user.republica:
            messages.error(request, 'Você já faz parte de uma república.')
            return redirect('gestao:dashboard')
        return super().get(request, *args, **kwargs)
    

class RepublicaListView(LoginRequiredMixin, ListView):
    model = Republica
    template_name = 'gestao/republica_list.html'
    context_object_name = 'republicas'
    paginate_by = 10 # Bom para quando tiver muitas

    def get_queryset(self):
        # Pega o parâmetro 'q' da URL (ex: /republicas/?q=Galo)
        query = self.request.GET.get('q')
        
        # Filtra apenas por repúblicas que tenham um nome parecido
        if query:
            object_list = Republica.objects.filter(nome__icontains=query)
        else:
            object_list = Republica.objects.all()
            
        return object_list.order_by('nome')

    def get(self, request, *args, **kwargs):
        # Checagem: Se o usuário já tem uma república, não pode procurar outra
        if request.user.republica:
            messages.error(request, 'Você já faz parte de uma república.')
            return redirect('gestao:dashboard')
        return super().get(request, *args, **kwargs)


# NOVA VIEW: Processar a solicitação de entrada
class SolicitarEntradaRepublicaView(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        republica_pk = self.kwargs.get('pk')
        republica = get_object_or_404(Republica, pk=republica_pk)
        user = request.user
        
        # Checagem dupla: não pode solicitar se já está em uma
        if user.republica:
            messages.error(request, 'Você já está em uma república.')
            return redirect('gestao:dashboard')
            
        # Atualiza o usuário, ligando-o à república e marcando como pendente
        user.republica = republica
        user.status_associacao = Usuario.StatusAssociacao.AGUARDANDO_APROVACAO
        user.save()
        
        messages.success(request, f'Solicitação para entrar em "{republica.nome}" foi enviada ao administrador!')
        
        # Manda o usuário de volta para a dashboard, já que agora ele tem
        # um status de "aguardando"
        return redirect('gestao:dashboard')
    
class AprovarMoradorView(LoginRequiredMixin, View):
    
    def post(self, request, *args, **kwargs):
        # O 'pk' da URL é o ID do usuário que quer ser aprovado (o Alexandre)
        usuario_a_aprovar_pk = self.kwargs.get('pk')
        usuario_a_aprovar = get_object_or_404(Usuario, pk=usuario_a_aprovar_pk)
        
        # O usuário logado (o Gustavo)
        adm = request.user

        # CHECAGEM DE SEGURANÇA:
        # 1. O usuário a aprovar tem que estar ligado a uma república
        # 2. O usuário logado (adm) tem que ser o ADM *dessa* república
        if not usuario_a_aprovar.republica or adm != usuario_a_aprovar.republica.adm:
            messages.error(request, 'Você não tem permissão para esta ação.')
            return redirect('gestao:dashboard')

        # Se tudo estiver ok, aprova o usuário
        if usuario_a_aprovar.status_associacao == Usuario.StatusAssociacao.AGUARDANDO_APROVACAO:
            usuario_a_aprovar.status_associacao = Usuario.StatusAssociacao.APROVADO
            usuario_a_aprovar.save()
            messages.success(request, f'{usuario_a_aprovar.username} foi aprovado na república!')
        else:
            messages.warning(request, 'Este usuário não estava aguardando aprovação.')

        return redirect('gestao:dashboard')


# NOVA VIEW: Rejeitar Morador
class RejeitarMoradorView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        # O 'pk' da URL é o ID do usuário a ser rejeitado
        usuario_a_rejeitar_pk = self.kwargs.get('pk')
        usuario_a_rejeitar = get_object_or_404(Usuario, pk=usuario_a_rejeitar_pk)
        
        adm = request.user

        # Mesma checagem de segurança
        if not usuario_a_rejeitar.republica or adm != usuario_a_rejeitar.republica.adm:
            messages.error(request, 'Você não tem permissão para esta ação.')
            return redirect('gestao:dashboard')

        # Se ok, rejeita o usuário (desvincula ele da república)
        if usuario_a_rejeitar.status_associacao == Usuario.StatusAssociacao.AGUARDANDO_APROVACAO:
            republica_nome = usuario_a_rejeitar.republica.nome # Salva o nome para a msg
            
            usuario_a_rejeitar.status_associacao = Usuario.StatusAssociacao.NAO_APROVADO
            usuario_a_rejeitar.republica = None # Desvincula da república
            usuario_a_rejeitar.save()
            
            messages.warning(request, f'{usuario_a_rejeitar.username} foi rejeitado da república {republica_nome}.')
        else:
            messages.warning(request, 'Este usuário não estava aguardando aprovação.')

        return redirect('gestao:dashboard')
    

class ContaCreateView(LoginRequiredMixin, CreateView):
    model = Conta
    form_class = ContaCreateForm # MUDANÇA: Usando nosso formulário customizado
    template_name = 'gestao/conta_form.html'
    success_url = reverse_lazy('gestao:dashboard')

    def get_form_kwargs(self):
        """ Passa o usuário logado para o __init__ do formulário """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if not request.user.republica or request.user.status_associacao != 'APROVADO':
            messages.error(request, 'Você precisa ser um membro aprovado de uma república para criar contas.')
            return redirect('gestao:dashboard')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        
        # 1. Define o responsável e a república (igual a antes)
        form.instance.responsavel = user
        form.instance.republica = user.republica
        
        # 2. Salva a Conta principal (igual a antes)
        response = super().form_valid(form)
        
        # 3. MUDANÇA: Pega a lista de participantes do formulário
        nova_conta = self.object
        participantes_selecionados = form.cleaned_data['participantes']
        total_participantes = participantes_selecionados.count()
        
        if total_participantes > 0:
            # Divide o valor apenas entre os selecionados
            valor_individual = nova_conta.valor_total / total_participantes
            
            participantes_para_criar = []
            for morador in participantes_selecionados:
                participantes_para_criar.append(
                    ParticipanteConta(
                        conta=nova_conta,
                        usuario=morador,
                        valor_individual=valor_individual
                    )
                )
            
            ParticipanteConta.objects.bulk_create(participantes_para_criar)
            
            messages.success(self.request, f'Conta "{nova_conta.nome_conta}" criada para {total_participantes} participantes.')
        else:
            # Isso não deve acontecer por causa do 'required=True', mas é bom ter
            messages.warning(self.request, 'Conta criada, mas ninguém foi selecionado.')

        return response

class ConfirmarPagamentoView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        # 'pk' é o ID do 'ParticipanteConta' (a participação do Alexandre)
        participacao_pk = self.kwargs.get('pk')
        participacao = get_object_or_404(ParticipanteConta, pk=participacao_pk)
        
        # O usuário logado (o Gustavo)
        responsavel = request.user

        # CHECAGEM DE SEGURANÇA CRÍTICA:
        # O usuário logado é o 'responsavel' (dono) desta conta?
        if participacao.conta.responsavel != responsavel:
            messages.error(request, 'Você não tem permissão para confirmar este pagamento.')
            return redirect('gestao:dashboard')

        # Se for o dono, confirma o pagamento
        if participacao.status_pagamento == ParticipanteConta.StatusPagamento.CONFIRMACAO_PENDENTE:
            participacao.status_pagamento = ParticipanteConta.StatusPagamento.PAGO
            participacao.save()
            messages.success(request, f'Pagamento de {participacao.usuario.username} confirmado!')
        else:
            messages.warning(request, 'Esta ação não pôde ser executada.')

        return redirect('gestao:dashboard')


# NOVA VIEW: Rejeitar o pagamento de um participante
class RejeitarPagamentoView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        participacao_pk = self.kwargs.get('pk')
        participacao = get_object_or_404(ParticipanteConta, pk=participacao_pk)
        responsavel = request.user

        # Mesma checagem de segurança
        if participacao.conta.responsavel != responsavel:
            messages.error(request, 'Você não tem permissão para esta ação.')
            return redirect('gestao:dashboard')

        # Se for o dono, rejeita (volta para 'NAO_PAGO')
        if participacao.status_pagamento == ParticipanteConta.StatusPagamento.CONFIRMACAO_PENDENTE:
            participacao.status_pagamento = ParticipanteConta.StatusPagamento.NAO_PAGO
            participacao.save()
            messages.warning(request, f'Pagamento de {participacao.usuario.username} rejeitado. O status voltou para "Não Pago".')
        else:
            messages.warning(request, 'Esta ação não pôde ser executada.')

        return redirect('gestao:dashboard')