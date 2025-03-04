# Generated by Django 5.1.3 on 2025-01-13 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='type',
            field=models.CharField(choices=[('PRODUCT', 'Product category'), ('EXPENSES', 'Expenses category'), ('SERVICE', 'Service category')], default='PRODUCT', max_length=10),
        ),
    ]
