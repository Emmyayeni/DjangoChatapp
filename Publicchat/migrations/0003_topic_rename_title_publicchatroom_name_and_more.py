# Generated by Django 4.1.5 on 2023-02-12 21:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Publicchat', '0002_alter_publicchatroom_users'),
    ]

    operations = [
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.RenameField(
            model_name='publicchatroom',
            old_name='title',
            new_name='name',
        ),
        migrations.RemoveField(
            model_name='publicchatroom',
            name='users',
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='active_users',
            field=models.ManyToManyField(blank=True, help_text='users who are connected to the chat', related_name='active_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='host',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='participants',
            field=models.ManyToManyField(blank=True, help_text='users who has joined the chat room', related_name='participants', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='publicchatroom',
            name='topic',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Publicchat.topic'),
        ),
    ]
