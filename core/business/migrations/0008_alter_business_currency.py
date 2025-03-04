# Generated by Django 5.1.3 on 2024-11-30 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0007_alter_business_currency_alter_business_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='business',
            name='currency',
            field=models.CharField(choices=[('NGN', 'Nigerian Naira'), ('USD', 'United state dollar'), ('EUR', 'Euro'), ('GBP', 'British Pound Sterling'), ('KES', 'Kenya Shillings'), ('GHS', 'Ghana Cedis')], default='NGN', max_length=5),
        ),
    ]
