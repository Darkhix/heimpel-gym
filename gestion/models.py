from django.db import models
from django.utils import timezone
from datetime import timedelta

# 1. El tipo de Plan
class Plan(models.Model):
    nombre = models.CharField(max_length=50) 
    precio = models.DecimalField(max_digits=10, decimal_places=0) 
    duracion_dias = models.IntegerField() 

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

# 2. El Cliente (AHORA CON CONTRASEÑA)
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, verbose_name="DNI / RUT")
    
    # Campo de seguridad agregado
    password = models.CharField(max_length=128, verbose_name="Contraseña")
    
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20)
    
    # Datos Médicos
    enfermedades = models.TextField(blank=True)
    medicamentos = models.TextField(blank=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# 3. La Membresía
class Membresia(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.fecha_fin and self.plan:
            self.fecha_fin = self.fecha_inicio + timedelta(days=self.plan.duracion_dias)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente} - {self.plan}"

# 4. Los Pagos
class Pago(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=0)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo = models.CharField(max_length=50, choices=[('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia')])

    def __str__(self):
        return f"${self.monto} - {self.cliente}"