# Generated by Django 2.1.7 on 2019-03-08 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_auto_20190308_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(default='images/default.png', null=True, upload_to='images/'),
        ),
    ]
