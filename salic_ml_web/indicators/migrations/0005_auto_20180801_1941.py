# Generated by Django 2.0.7 on 2018-08-01 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0004_auto_20180801_1925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='pronac',
            field=models.IntegerField(default=0),
        ),
    ]
