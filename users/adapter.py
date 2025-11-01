from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
import os

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context, request=None):
        """
        Overrides the default send_mail method to embed the logo and send multipart emails.
        """
        # Render subject, text body, and HTML body.
        subject = render_to_string(f'{template_prefix}_subject.txt', context, request=request).strip()
        text_body = render_to_string(f'{template_prefix}_message.txt', context, request=request)
        html_body = render_to_string(f'{template_prefix}_message.html', context, request=request)

        # Create the email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        msg.attach_alternative(html_body, "text/html")

        # Embed the logo
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'splitcart_logo.webp')
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            logo = MIMEImage(logo_data)
            logo.add_header('Content-ID', '<logo>')
            msg.attach(logo)
        except FileNotFoundError:
            # Handle case where logo is not found, maybe log it
            pass

        # Send the email
        msg.send()
