from django.db import migrations

def recreate_bargain_table(apps, schema_editor):
    # This migration was problematic for test databases.
    # The create_model call is removed as the table is created in a previous migration.
    pass

class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        # This migration needs to run after the last migration that touched
        # any related models, especially the 'Bargain' model itself.
        ('products', '0006_alter_bargain_cheaper_store_and_more'),
    ]

    operations = [
        # The RunPython operation executes our custom function.
        migrations.RunPython(recreate_bargain_table),
    ]