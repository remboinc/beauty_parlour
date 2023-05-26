# Generated by Django 4.2.1 on 2023-05-26 13:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('Парикмахерские услуги', 'Парикмахерские услуги'), ('Маникюр', 'Маникюр'), ('Макияж', 'Макияж')], max_length=30, verbose_name='Категория услуг')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
            },
        ),
        migrations.CreateModel(
            name='Master',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15, verbose_name='Имя мастера')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
            ],
            options={
                'verbose_name': 'Мастер',
                'verbose_name_plural': 'Мастера',
            },
        ),
        migrations.CreateModel(
            name='Saloon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20, verbose_name='Название салона')),
                ('city', models.CharField(max_length=20, verbose_name='Город')),
                ('address', models.CharField(max_length=50, verbose_name='Адрес')),
                ('phonenumber', phonenumber_field.modelfields.PhoneNumberField(blank=True, db_index=True, max_length=20, null=True, region=None, verbose_name='Номер телефона салона')),
                ('time_open', models.TimeField(verbose_name='Время открытия')),
                ('time_close', models.TimeField(verbose_name='Время закрытия')),
            ],
            options={
                'verbose_name': 'Салон',
                'verbose_name_plural': 'Салоны',
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('Мужская стрижка', 'Мужская стрижка'), ('Женская стрижка', 'Женская стрижка'), ('Европейский маникюр', 'Европейский маникюр'), ('Аппаратный маникюр', 'Аппаратный маникюр'), ('Макияж стандарт', 'Макияж стандарт'), ('Свадебный макияж', 'Свадебный макияж')], max_length=30, verbose_name='Наименование услуги')),
                ('price', models.DecimalField(decimal_places=0, max_digits=5, verbose_name='Цена услуги')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='masters', to='service.category', verbose_name='Из какой категории')),
                ('masters', models.ManyToManyField(related_name='services', to='service.master', verbose_name='Какой мастер')),
            ],
            options={
                'verbose_name': 'Услуга',
                'verbose_name_plural': 'Услуги',
            },
        ),
        migrations.AddField(
            model_name='master',
            name='saloon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='masters', to='service.saloon', verbose_name='В каком салоне'),
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='Имя клиента')),
                ('phonenumber', phonenumber_field.modelfields.PhoneNumberField(db_index=True, max_length=20, region=None, verbose_name='Номер телефона клиента')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clients', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Клиент',
                'verbose_name_plural': 'Клиенты',
            },
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField(null=True, verbose_name='Дата визита')),
                ('appointment_time', models.CharField(choices=[('10:00', '10:00'), ('10:30', '10:30'), ('11:00', '11:00'), ('11:30', '11:30'), ('12:00', '12:00'), ('12:30', '12:30'), ('13:00', '13:00'), ('13:30', '13:30'), ('14:00', '14:00'), ('14:30', '14:30'), ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'), ('16:30', '16:30'), ('17:00', '17:00'), ('17:30', '17:30'), ('18:00', '18:00'), ('18:30', '18:30'), ('19:00', '19:00'), ('19:30', '19:30'), ('20:00', '20:00'), ('20:30', '20:30')], db_index=True, max_length=30, verbose_name='Время визита')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='service.client', verbose_name='Кто клиент')),
                ('master', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='service.master', verbose_name='К какому мастеру')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='service.service', verbose_name='Какая услуга')),
            ],
            options={
                'verbose_name': 'Запись на услугу',
                'verbose_name_plural': 'Записи на услуги',
            },
        ),
    ]
