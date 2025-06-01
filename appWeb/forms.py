from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser, Profile


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu email místico...'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu clave secreta...'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded bg-cosmic-800 border-cosmic-600 text-primary-500 focus:ring-primary-500'
        })
    )


class RegisterForm(UserCreationForm):
    nombre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu nombre místico...'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu email cósmico...'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Crea tu clave secreta...'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Confirma tu clave...'
        })
    )
    acepta_terminos = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded bg-cosmic-800 border-cosmic-600 text-primary-500 focus:ring-primary-500'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('nombre', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.nombre = self.cleaned_data['nombre']
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['fecha_nacimiento', 'telefono', 'biografia', 'avatar']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
                'placeholder': 'Tu número de contacto...'
            }),
            'biografia': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
                'placeholder': 'Cuéntanos sobre tu conexión con lo místico...',
                'rows': 4
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100',
                'accept': 'image/*'
            })
        }


class ConsultaTarotForm(forms.Form):
    pregunta = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Escribe tu pregunta al universo... ¿Qué deseas saber?',
            'rows': 4,
            'maxlength': 500
        }),
        max_length=500,
        help_text='Máximo 500 caracteres. Sé específico en tu consulta.'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar contador de caracteres con JavaScript
        self.fields['pregunta'].widget.attrs.update({
            'oninput': 'updateCharCount(this)',
            'data-max': '500'
        })


class ContactForm(forms.Form):
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu nombre...'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Tu email...'
        })
    )
    asunto = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Asunto de tu mensaje...'
        })
    )
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 bg-cosmic-800 border border-cosmic-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-cosmic-100 placeholder-cosmic-400',
            'placeholder': 'Escribe tu mensaje...',
            'rows': 6
        })
    )