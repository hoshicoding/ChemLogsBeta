# Generated by Django 4.1.2 on 2023-01-04 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemlogs', '0004_alter_bottle_molarity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bottle',
            name='molarity',
            field=models.FloatField(blank=True, null=True),
        ),
    ]