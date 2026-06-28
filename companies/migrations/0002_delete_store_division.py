# Generated manually for Store and Division removal.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_price_company'),
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Store',
        ),
        migrations.DeleteModel(
            name='Division',
        ),
    ]
