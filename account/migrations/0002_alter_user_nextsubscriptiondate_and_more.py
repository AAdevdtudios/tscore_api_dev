# Generated by Django 5.0 on 2023-12-14 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='nextSubscriptionDate',
            field=models.DateTimeField(auto_now=True, verbose_name='Next Date'),
        ),
        migrations.AlterField(
            model_name='user',
            name='subscriptionDate',
            field=models.DateTimeField(auto_now=True, verbose_name='Subscription Date'),
        ),
    ]
