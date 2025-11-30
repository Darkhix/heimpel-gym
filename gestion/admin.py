
from django.contrib import admin
from .models import Plan, Cliente, Membresia, Pago

# Esto hace que aparezcan cuadros bonitos en tu panel
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'dni', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'dni')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'monto', 'metodo', 'fecha_pago')
    list_filter = ('fecha_pago', 'metodo')

admin.site.register(Plan)
admin.site.register(Membresia)