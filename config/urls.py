from django.contrib import admin
from django.urls import path, include
from gestao.views import RegisterView , UsuarioDeleteView
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='index'),
    path('admin/', admin.site.urls),
    path('dashboard/', include('gestao.urls')),
    path('contas/', include('django.contrib.auth.urls')),
    path('register/', RegisterView.as_view(), name='register'),
    path('deletar-minha-conta/', UsuarioDeleteView.as_view(), name='usuario_delete'),
]