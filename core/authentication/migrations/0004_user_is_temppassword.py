# Generated by Django 5.1.3 on 2024-11-28 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_tempPassword',
            field=models.BooleanField(default=False),
        ),
    ]
