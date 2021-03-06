# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-11 15:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name for the object', max_length=255)),
                ('date_modified', models.DateTimeField(auto_now=True, help_text='DateTime of last modification')),
                ('flag', models.CharField(blank=True, choices=[('FLAG', 'Flagged'), ('FLAG_HEART', 'Flagged (Heart)'), ('IMPORTANT', 'Important'), ('REVOKED', 'Revoked'), ('SUPERSEDED', 'Superseded')], help_text='Flag for highlighting the item (optional)', max_length=64, null=True)),
                ('description', models.CharField(blank=True, help_text='Description (optional)', max_length=255)),
                ('omics_uuid', models.UUIDField(default=uuid.uuid4, help_text='Filesfolders Omics UUID', unique=True)),
                ('file', models.FileField(blank=True, help_text='Uploaded file', null=True, upload_to='filesfolders.FileData/bytes/file_name/content_type')),
                ('public_url', models.BooleanField(default=False, help_text='Allow providing a public URL for the file')),
                ('secret', models.CharField(help_text='Secret string for creating public URL', max_length=255, unique=True)),
            ],
            options={
                'ordering': ['folder', 'name'],
            },
        ),
        migrations.CreateModel(
            name='FileData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bytes', models.TextField()),
                ('file_name', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name for the object', max_length=255)),
                ('date_modified', models.DateTimeField(auto_now=True, help_text='DateTime of last modification')),
                ('flag', models.CharField(blank=True, choices=[('FLAG', 'Flagged'), ('FLAG_HEART', 'Flagged (Heart)'), ('IMPORTANT', 'Important'), ('REVOKED', 'Revoked'), ('SUPERSEDED', 'Superseded')], help_text='Flag for highlighting the item (optional)', max_length=64, null=True)),
                ('description', models.CharField(blank=True, help_text='Description (optional)', max_length=255)),
                ('omics_uuid', models.UUIDField(default=uuid.uuid4, help_text='Filesfolders Omics UUID', unique=True)),
            ],
            options={
                'ordering': ['project', 'name'],
            },
        ),
        migrations.CreateModel(
            name='HyperLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name for the object', max_length=255)),
                ('date_modified', models.DateTimeField(auto_now=True, help_text='DateTime of last modification')),
                ('flag', models.CharField(blank=True, choices=[('FLAG', 'Flagged'), ('FLAG_HEART', 'Flagged (Heart)'), ('IMPORTANT', 'Important'), ('REVOKED', 'Revoked'), ('SUPERSEDED', 'Superseded')], help_text='Flag for highlighting the item (optional)', max_length=64, null=True)),
                ('description', models.CharField(blank=True, help_text='Description (optional)', max_length=255)),
                ('omics_uuid', models.UUIDField(default=uuid.uuid4, help_text='Filesfolders Omics UUID', unique=True)),
                ('url', models.URLField(help_text='URL for the link', max_length=2000)),
                ('folder', models.ForeignKey(blank=True, help_text='Folder under which object exists (null if root folder)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filesfolders_hyperlink_children', to='filesfolders.Folder')),
            ],
            options={
                'ordering': ['folder', 'name'],
            },
        ),
    ]
