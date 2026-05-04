from django import forms

from .models import ContactMessage, PliegoDemoLead


PLIEGO_MAX_BYTES = 20 * 1024 * 1024  # 20 MB — coincide con nginx client_max_body_size
PLIEGO_ALLOWED_MIME = ('application/pdf', 'application/octet-stream', '')


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['nombre', 'email', 'empresa', 'interes', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'Tu nombre',
                'autocomplete': 'name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'tu@empresa.com',
                'autocomplete': 'email',
                'required': True,
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'Nombre de tu empresa',
                'autocomplete': 'organization',
            }),
            'interes': forms.Select(attrs={
                'class': 'select select-bordered bg-base-300/50 w-full',
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered bg-base-300/50 w-full',
                'rows': 4,
                'placeholder': 'Contame brevemente qué necesitás — proceso a automatizar, sistema a construir o infra a migrar.',
                'required': True,
                'minlength': 20,
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'email': 'Email',
            'empresa': 'Empresa',
            'interes': '¿Qué te interesa?',
            'mensaje': 'Tu consulta',
        }

    def clean_mensaje(self):
        mensaje = self.cleaned_data.get('mensaje', '').strip()
        if len(mensaje) < 20:
            raise forms.ValidationError(
                'Contame un poco más — al menos 20 caracteres para que sepa por dónde empezar.'
            )
        return mensaje


class PliegoDemoForm(forms.ModelForm):
    """Form del lead magnet de licitaciones (upload de PDF + datos de contacto)."""

    class Meta:
        model = PliegoDemoLead
        fields = ['nombre', 'email', 'empresa', 'telefono', 'pdf_original', 'consentimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'Tu nombre',
                'autocomplete': 'name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'tu@empresa.com',
                'autocomplete': 'email',
                'required': True,
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': 'Nombre de tu empresa',
                'autocomplete': 'organization',
                'required': True,
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'input input-bordered bg-base-300/50 w-full',
                'placeholder': '+54 11 ...',
                'autocomplete': 'tel',
            }),
            'pdf_original': forms.ClearableFileInput(attrs={
                'class': 'file-input file-input-bordered bg-base-300/50 w-full',
                'accept': 'application/pdf,.pdf',
                'required': True,
            }),
            'consentimiento': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-warning',
                'required': True,
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'email': 'Email corporativo',
            'empresa': 'Empresa',
            'telefono': 'Teléfono (opcional)',
            'pdf_original': 'Subí tu TDR, compulsa o pliego de ejemplo',
            'consentimiento': (
                'Acepto recibir el borrador por email y un seguimiento comercial '
                'relacionado con esta demo.'
            ),
        }

    def clean_empresa(self):
        empresa = self.cleaned_data.get('empresa', '').strip()
        if not empresa:
            raise forms.ValidationError(
                'Necesitamos el nombre de tu empresa para generar el borrador con contexto real.'
            )
        return empresa

    def clean_consentimiento(self):
        v = self.cleaned_data.get('consentimiento')
        if not v:
            raise forms.ValidationError(
                'Necesitamos tu consentimiento para enviarte el borrador por mail.'
            )
        return v

    def clean_pdf_original(self):
        f = self.cleaned_data.get('pdf_original')
        if f is None:
            raise forms.ValidationError('Subí un archivo PDF para generar el borrador.')

        if f.size > PLIEGO_MAX_BYTES:
            raise forms.ValidationError(
                'El PDF supera 20 MB. Escribinos por WhatsApp para subirlo por otro canal.'
            )
        if f.size == 0:
            raise forms.ValidationError('El archivo está vacío.')

        # MIME declarado por el browser (no confiable, pero filtra errores obvios)
        content_type = getattr(f, 'content_type', '') or ''
        if content_type and content_type not in PLIEGO_ALLOWED_MIME:
            raise forms.ValidationError('Subí un archivo PDF.')

        # Magic bytes: los PDFs empiezan con "%PDF"
        pos = f.tell()
        try:
            head = f.read(5)
        finally:
            f.seek(pos)
        if not head.startswith(b'%PDF'):
            raise forms.ValidationError(
                'El archivo no parece un PDF válido. Verificá que no esté corrupto.'
            )
        return f
