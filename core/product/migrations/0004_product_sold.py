# Generated by Django 5.1.3 on 2024-11-16 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_productstocking'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sold',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
