# Generated by Django 4.1.2 on 2023-02-28 19:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chemlogs', '0010_remove_chemical_barcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionEdit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('old_amount', models.IntegerField()),
                ('new_amount', models.IntegerField()),
                ('old_type', models.CharField(choices=[('T', 'TRANSACT'), ('N', 'NEW'), ('R', 'RESET'), ('I', 'IGNORED')], max_length=1)),
                ('new_type', models.CharField(choices=[('T', 'TRANSACT'), ('N', 'NEW'), ('R', 'RESET'), ('I', 'IGNORED')], max_length=1)),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chemlogs.transaction')),
            ],
        ),
    ]
