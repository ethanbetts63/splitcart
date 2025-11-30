from django.db import migrations

def recreate_bargain_table(apps, schema_editor):
    # Get the model from the app registry. This ensures we have the final,
    # fully-defined version of the model, including all fields from all
    # previous migrations.
    Bargain = apps.get_model('products', 'Bargain')
    
    # Use the schema editor's create_model method to build the table
    # from the model's state. This is the standard way to manually
    # create a table for a model that Django thinks already exists.
    schema_editor.create_model(Bargain)

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