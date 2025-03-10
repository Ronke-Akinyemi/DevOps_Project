# Generated by Django 5.1.3 on 2024-11-28 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_user_phone_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('OWNER', 'Business Owner'), ('ATTENDANT', 'Business Attendant'), ('ADMIN', 'Admin users')], default='OWNER', max_length=10),
        ),
    ]
