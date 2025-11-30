from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from .models import Pago, Cliente, Membresia
from .forms import RegistroClienteForm
from datetime import date
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
def dashboard(request):
    # 1. Calcular Ganancia Total Histórica (Suma todo lo que hay en la tabla Pagos)
    total_ganado = Pago.objects.aggregate(Sum('monto'))['monto__sum'] or 0

    # 2. Calcular Ganancia de ESTE MES
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0)
    ganancia_mes = Pago.objects.filter(fecha_pago__gte=inicio_mes).aggregate(Sum('monto'))['monto__sum'] or 0

    # 3. Contar Clientes Totales
    total_clientes = Cliente.objects.count()

    # 4. Empaquetar los datos para enviarlos a la web
    context = {
        'total_ganado': total_ganado,
        'ganancia_mes': ganancia_mes,
        'total_clientes': total_clientes,
    }
    
    return render(request, 'dashboard.html', context)
def registro_publico(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            # ... (tu código de encriptar clave y guardar cliente) ...
            cliente = form.save(commit=False)
            cliente.password = make_password(form.cleaned_data['password'])
            cliente.save()
            
            # ... (tu código de crear membresía) ...
            plan_elegido = form.cleaned_data['plan_seleccionado']
            Membresia.objects.create(cliente=cliente, plan=plan_elegido)
            
            # --- CAMBIO AQUÍ: ---
            # En vez de 'render(request, 'exito.html'...)' pon esto:
            return redirect('pantalla_pago', cliente_id=cliente.id) 
            
    else:
        form = RegistroClienteForm()

    return render(request, 'registro_publico.html', {'form': form})

def home(request):
    return render(request, 'home.html')

def acceso_usuarios(request):
    if request.method == 'POST':
        dni_ingresado = request.POST.get('dni')
        password_ingresado = request.POST.get('password') # Recibimos la clave
        
        try:
            cliente = Cliente.objects.get(dni=dni_ingresado)
            
            # SEGURIDAD: Verificamos si la contraseña coincide con la encriptada
            if check_password(password_ingresado, cliente.password):
                request.session['cliente_id'] = cliente.id
                return redirect('mi_perfil')
            else:
                # Contraseña incorrecta
                return render(request, 'login_usuario.html', {'error': 'Contraseña incorrecta.'})
            
        except Cliente.DoesNotExist:
            return render(request, 'login_usuario.html', {'error': 'Ese RUT no existe.'})

    return render(request, 'login_usuario.html')

def perfil_usuario(request):
    # Recuperamos el ID de la sesión
    cliente_id = request.session.get('cliente_id')
    
    if not cliente_id:
        return redirect('acceso_usuarios') # Si no hay sesión, volver al login
        
    cliente = Cliente.objects.get(id=cliente_id)
    
    # Buscamos su última membresía
    membresia = Membresia.objects.filter(cliente=cliente).last()
    
    dias_restantes = 0
    estado = "Sin Plan"
    porcentaje = 0
    
    if membresia and membresia.fecha_fin:
        hoy = date.today()
        delta = membresia.fecha_fin - hoy
        dias_restantes = delta.days
        
        if dias_restantes > 0:
            estado = "Activo"
            # Calculamos porcentaje para barrita de progreso
            total_dias = membresia.plan.duracion_dias
            porcentaje = (dias_restantes / total_dias) * 100
        else:
            dias_restantes = 0
            estado = "Vencido"

    context = {
        'cliente': cliente,
        'membresia': membresia,
        'dias_restantes': dias_restantes,
        'estado': estado,
        'porcentaje': int(porcentaje)
    }
    
    return render(request, 'perfil_usuario.html', context)
def pantalla_pago(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    # Buscamos su última membresía para saber qué plan eligió
    membresia = Membresia.objects.filter(cliente=cliente).last()
    
    return render(request, 'pago_simulado.html', {
        'cliente': cliente,
        'plan': membresia.plan,
        'monto': membresia.plan.precio
    })

# 2. Función que "Cobra" y guarda el dinero en el sistema
def procesar_pago_real(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    membresia = Membresia.objects.filter(cliente=cliente).last()
    
    # CREAMOS EL PAGO EN LA BASE DE DATOS AUTOMÁTICAMENTE
    Pago.objects.create(
        cliente=cliente,
        monto=membresia.plan.precio,
        metodo='TRANSFERENCIA' # Asumimos transferencia web
    )
    
    # Enviamos a la pantalla de éxito final
    return render(request, 'exito.html', {'nombre': cliente.nombre})