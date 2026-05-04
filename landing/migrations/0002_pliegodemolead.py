"""Sprint 8 · Bloque 8: lead magnet de licitaciones."""

from django.db import migrations, models

import landing.models


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PliegoDemoLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120)),
                ('email', models.EmailField(max_length=254)),
                ('empresa', models.CharField(blank=True, max_length=120)),
                ('telefono', models.CharField(blank=True, max_length=30)),
                ('consentimiento', models.BooleanField(
                    default=False,
                    help_text='Aceptó recibir el borrador + seguimiento comercial',
                    verbose_name='Opt-in',
                )),
                ('pdf_original', models.FileField(
                    help_text='TDR/compulsa subido por el prospecto (fuera del MEDIA público)',
                    max_length=255,
                    storage=landing.models._pliegos_storage,
                    upload_to=landing.models._pliego_upload_to,
                    verbose_name='PDF original',
                )),
                ('pdf_filename_original', models.CharField(
                    blank=True, max_length=255,
                    help_text='Filename tal como llegó (el archivo se guarda con UUID)',
                    verbose_name='Nombre original',
                )),
                ('pdf_size_bytes', models.PositiveIntegerField(
                    default=0, verbose_name='Tamaño (bytes)',
                )),
                ('meta_origen', models.CharField(
                    blank=True,
                    help_text='Path de la página desde donde se envió',
                    max_length=120,
                )),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('enviado_n8n', models.BooleanField(
                    default=False,
                    help_text='True si el webhook n8n respondió 2xx',
                )),
                ('borrador_entregado', models.BooleanField(
                    default=False,
                    help_text='Marcar cuando el borrador de pliego fue enviado al prospecto',
                )),
                ('respondido', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Lead de pliego (demo)',
                'verbose_name_plural': 'Leads de pliego (demo)',
                'ordering': ['-creado_en'],
            },
        ),
    ]
