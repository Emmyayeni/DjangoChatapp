# Generated by Django 4.1.5 on 2023-02-03 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_privatechatroom_connected_users_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='privatechatroom',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
