# gestao/forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, Conta
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        # Adicione os campos que você quer no formulário de registro
        # 'username' e 'password' já estão incluídos por padrão
        fields = ('username', 'email', 'apelido')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'apelido')

class ContaCreateForm(forms.ModelForm):
    # Este campo 'participantes' não existe no modelo Conta,
    # estamos criando ele SÓ para o formulário
    participantes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.none(), # O queryset real será definido na view
        widget=forms.CheckboxSelectMultiple, # Queremos checkboxes
        required=True,
        label="Participantes da conta"
    )

    class Meta:
        model = Conta
        fields = ['nome_conta', 'valor_total', 'data_vencimento', 'tipo']
        # Adiciona widgets para os campos de data e valor
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'valor_total': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        # Pega o 'user' que a View vai nos passar
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Se temos um usuário, filtramos o queryset de 'participantes'
        # para mostrar APENAS os membros APROVADOS da república dele.
        if user and user.republica:
            self.fields['participantes'].queryset = Usuario.objects.filter(
                republica=user.republica,
                status_associacao=Usuario.StatusAssociacao.APROVADO
            ).order_by('username')