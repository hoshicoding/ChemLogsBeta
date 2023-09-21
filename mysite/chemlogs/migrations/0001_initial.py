# Generated by Django 4.1.2 on 2023-01-04 19:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bottle',
            fields=[
                ('loc', models.CharField(choices=[('US', 'Upper School'), ('MS', 'Middle School'), ('TALI', 'TALI')], default='US', max_length=4)),
                ('initial_value', models.IntegerField()),
                ('molarity', models.FloatField()),
                ('id', models.CharField(max_length=2, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Chemical',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cas', models.CharField(max_length=12)),
                ('formula', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=50)),
                ('safety', models.TextField()),
                ('barcode', models.BinaryField()),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('time', models.DateTimeField()),
                ('new', models.BooleanField(default=False)),
                ('bottle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chemlogs.bottle')),
            ],
        ),
        migrations.CreateModel(
            name='ChemicalState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('S', 'Solid'), ('L', 'Liquid'), ('G', 'Gas'), ('AQ', 'Aqueous')], default='S', max_length=2)),
                ('type', models.TextField(max_length=40)),
                ('min_thresh', models.IntegerField()),
                ('chemical', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chemlogs.chemical')),
            ],
        ),
        migrations.AddField(
            model_name='bottle',
            name='contents',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chemlogs.chemicalstate'),
        ),
    ]