# Generated by Django 5.1.3 on 2025-01-03 10:45

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0010_business_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessBank',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bank_name', models.CharField(max_length=100)),
                ('account_name', models.CharField(max_length=100)),
                ('account_number', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='business_banks', to='business.business')),
            ],
        ),
    ]
