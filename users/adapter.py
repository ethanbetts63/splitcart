from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context, request=None):
        subject = render_to_string(f'{template_prefix}_subject.txt', context, request=request).strip()
        text_body = render_to_string(f'{template_prefix}_message.txt', context, request=request)
        html_body = render_to_string(f'{template_prefix}_message.html', context, request=request)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
