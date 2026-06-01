"""
Custom SMTP backend para servidores cPanel/WHM con certificados self-signed.

El proveedor de hosting usa una CA propia no incluida en los bundles estándar
(certifi, Debian, Alpine). Django falla con CERTIFICATE_VERIFY_FAILED al
intentar enviar email via SSL. Este backend desactiva la verificación del cert
manteniendo el cifrado TLS — los datos viajan cifrados, solo se omite la
comprobación de la cadena de CA.

Usar solo cuando el servidor SMTP es de confianza (hosting propio/conocido).
"""
import ssl

from django.core.mail.backends.smtp import EmailBackend as _BaseBackend


class UntrustedCertEmailBackend(_BaseBackend):
    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def open(self):
        if self.connection:
            return False
        from django.core.mail.utils import DNS_NAME
        connection_params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params['context'] = self._get_ssl_context()
        try:
            import smtplib
            self.connection = smtplib.SMTP_SSL(
                self.host, self.port, **connection_params
            ) if self.use_ssl else smtplib.SMTP(
                self.host, self.port, **connection_params
            )
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                self.connection.starttls(context=self._get_ssl_context())
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
