from django.contrib import admin
from django.urls import path
from gestion import views

# --- CONFIGURACIÓN DE MARCA DEL ADMIN ---
admin.site.site_header = "Panel Staff - Heimpel Power Gym"  # Texto grande en el login y arriba
admin.site.site_title = "Admin Heimpel"                     # Título de la pestaña del navegador
admin.site.index_title = "Gestión del Gimnasio"             # Subtítulo en la lista de tablas

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Tus rutas normales...
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registro/', views.registro_publico, name='registro'),
    path('acceso-socios/', views.acceso_usuarios, name='acceso_socios'),
    path('mi-perfil/', views.perfil_usuario, name='mi_perfil'),
    path('pagar/<int:cliente_id>/', views.pantalla_pago, name='pantalla_pago'),
    path('procesar-pago/<int:cliente_id>/', views.procesar_pago_real, name='procesar_pago'),
]