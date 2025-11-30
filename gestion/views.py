from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from .models import Pago, Cliente, Membresia
from .forms import RegistroClienteForm
from datetime import date
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse
import random
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from django.views.decorators.csrf import csrf_exempt # Para que Transbank pueda volver
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
def configuracion_inicial(request):
    # 1. CREAR SUPERUSUARIO (DUEÑO)
    # Cambia 'admin' y '1234' por el usuario y contraseña que quieras
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@heimpel.cl', '1234')
        mensaje_user = "✅ Usuario 'admin' creado (Clave: 1234)<br>"
    else:
        mensaje_user = "ℹ️ El usuario 'admin' ya existía<br>"

    # 2. CREAR PLANES
    planes = [
        {"nombre": "Plan Estudiante Libre", "precio": 35000, "dias": 30},
        {"nombre": "Plan Estudiante Semi Personalizado", "precio": 45000, "dias": 30},
        {"nombre": "Plan Libre", "precio": 45000, "dias": 30},
        {"nombre": "Plan Semi Personalizado", "precio": 60000, "dias": 30},
    ]

    mensaje_planes = ""
    for p in planes:
        obj, created = Plan.objects.get_or_create(
            nombre=p['nombre'],
            defaults={'precio': p['precio'], 'duracion_dias': p['dias']}
        )
        if created:
            mensaje_planes += f"✅ Plan creado: {p['nombre']}<br>"
        else:
            mensaje_planes += f"ℹ️ Plan ya existía: {p['nombre']}<br>"

    return HttpResponse(f"<h1>Configuración Completa</h1>{mensaje_user}{mensaje_planes}<br><a href='/'>Volver al Inicio</a>")
def iniciar_webpay(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    membresia = Membresia.objects.filter(cliente=cliente).last()
    monto = int(membresia.plan.precio)
    
    # 1. Configuración de Transbank (Modo Pruebas)
    tx = Transaction(WebpayOptions(
        commerce_code="597055555532", # Código oficial de pruebas
        api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C", # Llave oficial de pruebas
        integration_type=IntegrationType.TEST
    ))
    
    # 2. Datos de la compra
    buy_order = str(random.randrange(1000000, 99999999)) # Orden única
    session_id = str(cliente.id)
    
    # IMPORTANTE: Cambia esto por TU URL DE RENDER cuando subas
    # En tu PC usa: http://127.0.0.1:8000/webpay-retorno/
    # En Render usa: https://heimpel-gym-1.onrender.com/webpay-retorno/
    return_url = request.build_absolute_uri('/webpay-retorno/') 

    # 3. Crear la transacción
    response = tx.create(buy_order, session_id, monto, return_url)
    
    # 4. Redirigir al usuario al formulario de Transbank
    return render(request, 'redireccion_webpay.html', {
        'url': response['url'],
        'token': response['token']
    })

@csrf_exempt # Necesario porque Transbank nos envía datos de vuelta
def confirmar_webpay(request):
    # Recibimos el token que manda Transbank
    token = request.GET.get("token_ws") or request.POST.get("token_ws")
    
    try:
        # 1. Confirmar la transacción con Transbank
        tx = Transaction(WebpayOptions(
            commerce_code="597055555532", 
            api_key="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
            integration_type=IntegrationType.TEST
        ))
        
        response = tx.commit(token) # Preguntamos: ¿Pagó de verdad?
        
        # 2. Si el estado es AUTHORIZED (Aprobado)
        if response['status'] == 'AUTHORIZED':
            cliente_id = response['session_id']
            monto = response['amount']
            cliente = Cliente.objects.get(id=cliente_id)
            
            # Guardamos el pago real en la base de datos
            Pago.objects.create(
                cliente=cliente,
                monto=monto,
                metodo='WEBPAY'
            )
            
            # Llevamos al éxito
            return render(request, 'exito.html', {'nombre': cliente.nombre})
            
        else:
            # Si el pago falló o lo anularon
            return HttpResponse("El pago fue rechazado o anulado por Transbank.")
            
    except Exception as e:
        # Si algo explota (token inválido, etc)
        return HttpResponse(f"Error en la transacción: {e}")