from django import forms
from .models import Cliente, Plan

class RegistroClienteForm(forms.ModelForm):
    plan_seleccionado = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        label="Selecciona tu Plan",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # NUEVO: Campo de contraseña (el widget PasswordInput hace que salgan puntitos ••••)
    password = forms.CharField(
        label="Crea una contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 4 caracteres'})
    )

    class Meta:
        model = Cliente
        # Agregamos 'password' a la lista de campos
        fields = ['nombre', 'dni', 'password', 'telefono', 'email', 'enfermedades', 'medicamentos', 'contacto_emergencia']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT / DNI'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'enfermedades': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
        }