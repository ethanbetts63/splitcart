# Generated manually for Store removal.

import django.db.models.deletion
from django.db import migrations, models


def copy_store_company_to_price(apps, schema_editor):
    Price = apps.get_model('products', 'Price')
    Store = apps.get_model('companies', 'Store')

    store_company = dict(Store.objects.values_list('id', 'company_id'))
    prices = Price.objects.only('id', 'store_id', 'company_id').iterator(chunk_size=1000)

    to_update = []
    for price in prices:
        company_id = store_company.get(price.store_id)
        if company_id:
            price.company_id = company_id
            to_update.append(price)

        if len(to_update) >= 1000:
            Price.objects.bulk_update(to_update, ['company'])
            to_update = []

    if to_update:
        Price.objects.bulk_update(to_update, ['company'])


def copy_price_company_to_store(apps, schema_editor):
    # Store rows are deleted by the next companies migration, so reversal cannot
    # faithfully rebuild the old per-store FK.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='price',
            name='company',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prices',
                to='companies.company',
            ),
        ),
        migrations.RunPython(copy_store_company_to_price, copy_price_company_to_store),
        migrations.AlterUniqueTogether(
            name='price',
            unique_together={('product', 'company')},
        ),
        migrations.RemoveIndex(
            model_name='price',
            name='products_pr_store_i_fcd987_idx',
        ),
        migrations.AddIndex(
            model_name='price',
            index=models.Index(fields=['company', 'product'], name='products_pr_company_d44d69_idx'),
        ),
        migrations.AlterField(
            model_name='price',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prices',
                to='companies.company',
            ),
        ),
        migrations.RemoveField(
            model_name='price',
            name='store',
        ),
    ]
