from django.contrib import admin
from django.urls import path, include
from gestao.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('gestao.urls')),
    path('contas/', include('django.contrib.auth.urls')),
    path('register/', RegisterView.as_view(), name='register'),
]