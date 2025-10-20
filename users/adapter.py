from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context, request=None):
        """
        Overrides the default send_mail method to ensure multipart (HTML and text)
        emails are sent correctly.
        """
        # The context already contains the user and activate_url.
        # We render the subject, text body, and HTML body.
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

        # Attach the HTML version
        msg.attach_alternative(html_body, "text/html")

        # Send the email
        msg.send()
