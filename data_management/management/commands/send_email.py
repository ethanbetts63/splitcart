import os
from django.core.management.base import BaseCommand, CommandParser
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags

class Command(BaseCommand):
    help = 'Sends a test email using a specified HTML file as the body.'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('recipient_email', type=str, help='The email address to send the test email to.')
        parser.add_argument('html_file_path', type=str, help='The absolute path to the HTML file to use as the email body.')
        parser.add_argument('--subject', type=str, default='Test Email from SplitCart', help='The subject of the email.')

    def handle(self, *args, **options):
        recipient_email = options['recipient_email']
        html_file_path = options['html_file_path']
        subject = options['subject']

        if not os.path.exists(html_file_path):
            self.stdout.write(self.style.ERROR(f'Error: The file "{html_file_path}" was not found.'))
            return

        self.stdout.write(f'Attempting to send a test email to {recipient_email}...')

        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Create a plain text version
            text_content = strip_tags(html_content)

            # Create the email
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send the email
            msg.send(fail_silently=False)

            self.stdout.write(self.style.SUCCESS('Successfully sent the test email.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred while sending the email: {e}'))
