# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.db.models.deletion
import django.core.validators
import django.utils.timezone
import crewdb.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Access',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('amount', models.DecimalField(max_digits=4, default=1, verbose_name='Number', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('1'))])),
            ],
            options={
                'verbose_name': 'Access object',
                'ordering': ['ticket__type'],
                'verbose_name_plural': 'Access objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AccountingDone',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
                ('comment_process', models.TextField(verbose_name='Comment Realization', null=True, blank=True)),
                ('finalized', models.BooleanField(verbose_name='Finalized', default=False, help_text='no crew (and related member/bill) change possibile after Finalization!')),
            ],
            options={
                'verbose_name': 'AccountingDone object',
                'verbose_name_plural': 'AccountingDone objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Advance',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('amount', models.DecimalField(default=0, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], max_digits=7, help_text='use dot instead of comma for decimals', verbose_name='Money', decimal_places=0)),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date')),
                ('crew_advance', models.BooleanField(verbose_name='Advance for Crew', default=False)),
                ('counterbalanced', models.BooleanField(verbose_name='Counterbalanced', default=False)),
            ],
            options={
                'verbose_name': 'Advance object',
                'ordering': ['date'],
                'verbose_name_plural': 'Advance objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Billing',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('date_internal', models.DateField(auto_now_add=True)),
                ('receipt', models.BooleanField(verbose_name='Receipt', default=False)),
                ('recipient_local', models.TextField(default=crewdb.models.Billing.default_recipient_local, verbose_name='Recipient')),
                ('member_local', models.CharField(max_length=400, blank=True, verbose_name='Crew Member')),
                ('invoicing_party', models.TextField(verbose_name='invoicing Party')),
                ('tax_nr', models.CharField(max_length=200, null=True, blank=True, verbose_name='Tax-Number')),
                ('bill_nr', models.CharField(max_length=200, default=crewdb.models.Billing.default_bill_nr, verbose_name='Bill-Number')),
                ('vat_id', models.CharField(max_length=200, null=True, blank=True, verbose_name='VAT ID')),
                ('tax_id', models.CharField(max_length=200, null=True, blank=True, verbose_name='Tax ID')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Datum')),
                ('service_free', models.TextField(verbose_name='Service', null=True, blank=True)),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
                ('delivery_date', models.DateField(null=True, verbose_name='Delivery date', default=django.utils.timezone.now, blank=True)),
                ('netto', models.DecimalField(max_digits=8, verbose_name='Netto', decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('brutto', models.DecimalField(max_digits=8, verbose_name='Brutto', decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('vat_rate_local', models.CharField(max_length=250, blank=True, verbose_name='VAT Rate')),
                ('reverse_charge', models.BooleanField(verbose_name='Reverse Charge', default=False)),
                ('storno', models.BooleanField(verbose_name='Storno', default=False)),
            ],
            options={
                'verbose_name': 'Billing object',
                'verbose_name_plural': 'Billing objects',
            },
            bases=(models.Model, crewdb.models.ModelDiffMixin),
        ),
        migrations.CreateModel(
            name='BillRecipient',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(unique=True, verbose_name='Name', max_length=200)),
                ('address', models.TextField(verbose_name='Address')),
            ],
            options={
                'verbose_name': 'BillRecipient object',
                'ordering': ['name'],
                'verbose_name_plural': 'BillRecipient objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(unique=True, verbose_name='Name', max_length=200)),
                ('phone', models.CharField(max_length=13, null=True, blank=True, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')], verbose_name='Phone')),
                ('email', models.EmailField(max_length=75, null=True, blank=True, verbose_name='Email')),
                ('address', models.TextField(verbose_name='Address', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Company object',
                'ordering': ['name'],
                'verbose_name_plural': 'Company objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Compensation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Compensation object',
                'verbose_name_plural': 'Compensation objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompensationSchema',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('schema', models.CharField(unique=True, verbose_name='name', max_length=200)),
                ('individual_billing', models.BooleanField(verbose_name='individual billing', default=False, help_text='If active, worktimes for crew members are considered')),
            ],
            options={
                'verbose_name': 'CompensationSchema object',
                'verbose_name_plural': 'CompensationSchema objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Crew',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(unique=True, verbose_name='Crew name', max_length=200)),
                ('budget', models.DecimalField(validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], max_digits=8, blank=True, null=True, verbose_name='Budget', decimal_places=2)),
                ('budget_comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
                ('can_use_supporter', models.BooleanField(verbose_name='Can use supporter', default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Host contact', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name': 'Crew object',
                'ordering': ['name'],
                'verbose_name_plural': 'Crew objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventTimes',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('date_from', models.DateField(default=django.utils.timezone.now, verbose_name='From')),
                ('date_to', models.DateField(default=django.utils.timezone.now, verbose_name='To')),
                ('fee', models.DecimalField(default=0, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], max_digits=3, help_text='Amount of money for workers per day', verbose_name='Fee', decimal_places=0)),
                ('description', models.CharField(unique=True, help_text='Use short description (best one word)', verbose_name='Description', max_length=200)),
            ],
            options={
                'verbose_name': 'EventTimes object',
                'ordering': ['date_from'],
                'verbose_name_plural': 'EventTimes objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('phone', models.CharField(max_length=13, null=True, blank=True, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')], verbose_name='Phone')),
                ('email', models.EmailField(max_length=75, null=True, blank=True, verbose_name='Email')),
                ('address', models.TextField(verbose_name='Address', null=True, blank=True)),
                ('crew_contact', models.BooleanField(verbose_name='Crew Contact', default=False)),
                ('access_given', models.BooleanField(verbose_name='Access given', default=False, help_text='lanyard given')),
            ],
            options={
                'verbose_name': 'Member object',
                'ordering': ['name'],
                'verbose_name_plural': 'Member objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Provision',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('before_number', models.DecimalField(max_digits=4, default=0, verbose_name='Before Number', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('before_voucher', models.BooleanField(verbose_name='Voucher', default=False)),
                ('before_issued', models.BooleanField(verbose_name='Issued', default=False)),
                ('during_number', models.DecimalField(max_digits=4, default=0, verbose_name='During Number', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('during_voucher', models.BooleanField(verbose_name='Voucher', default=False)),
                ('during_issued', models.BooleanField(verbose_name='Issued', default=False)),
                ('after_number', models.DecimalField(max_digits=4, default=0, verbose_name='After Number', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('after_voucher', models.BooleanField(verbose_name='Voucher', default=False)),
                ('after_issued', models.BooleanField(verbose_name='Issued', default=False)),
                ('crew', models.OneToOneField(to='crewdb.Crew', verbose_name='Crew', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name': 'Provision object',
                'verbose_name_plural': 'Provision objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('service', models.CharField(max_length=200, null=True, blank=True, verbose_name='Service')),
            ],
            options={
                'verbose_name': 'Service object',
                'ordering': ['service'],
                'verbose_name_plural': 'Service objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('type', models.CharField(unique=True, verbose_name='Type', max_length=10)),
                ('description', models.CharField(max_length=200, null=True, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Ticket object',
                'ordering': ['type'],
                'verbose_name_plural': 'Ticket objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TicketAdmin',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('amount', models.DecimalField(max_digits=4, default=1, verbose_name='Amount', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('1'))])),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date')),
                ('member', models.ForeignKey(to='crewdb.Member', verbose_name='Crew Member')),
                ('ticket_in', models.ForeignKey(default='', to='crewdb.Ticket', verbose_name='Ticket to Host (in)', null=True, blank=True, related_name='ticket_in')),
                ('ticket_out', models.ForeignKey(default='', to='crewdb.Ticket', verbose_name='Ticket to Member (out)', null=True, blank=True, related_name='ticket_out')),
            ],
            options={
                'verbose_name': 'TicketAdmin object',
                'ordering': ['date'],
                'verbose_name_plural': 'TicketAdmin objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserExtras',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('phone', models.CharField(max_length=13, null=True, blank=True, validators=[django.core.validators.RegexValidator('^\\+?1?\\d{9,15}$', message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')], verbose_name='Phone')),
                ('address', models.TextField(verbose_name='Address', null=True, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VatRate',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('rate', models.DecimalField(max_digits=2, verbose_name='VAT rate %', decimal_places=0, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('description', models.CharField(max_length=200, null=True, blank=True, verbose_name='Description')),
                ('bill_title', models.CharField(max_length=200, null=True, blank=True, verbose_name='Bill Title')),
                ('additional_bill_comment', models.TextField(verbose_name='Additional Bill Comment', null=True, blank=True)),
                ('max_netto', models.DecimalField(max_digits=8, default=0, verbose_name='Maximal Netto', decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
            ],
            options={
                'verbose_name': 'VatRate object',
                'ordering': ['rate'],
                'verbose_name_plural': 'VatRate objects',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkTime',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('date_from', models.DateField(default=django.utils.timezone.now, verbose_name='From')),
                ('date_to', models.DateField(default=django.utils.timezone.now, verbose_name='To')),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
                ('member', models.ForeignKey(to='crewdb.Member', verbose_name='Crew Member')),
            ],
            options={
                'verbose_name': 'WorkTime object',
                'ordering': ['date_from'],
                'verbose_name_plural': 'WorkTime objects',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='service',
            name='vat_rate',
            field=models.ForeignKey(help_text='If none selected, service available for all bills', to='crewdb.VatRate', verbose_name='Allowed Vat-Rates', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='access',
            field=models.ForeignKey(help_text='planned access only.', to='crewdb.Ticket', verbose_name='Access', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='crew',
            field=models.ForeignKey(to='crewdb.Crew'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='compensation',
            name='crew',
            field=models.OneToOneField(to='crewdb.Crew', verbose_name='Crew'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='compensation',
            name='schema',
            field=models.ForeignKey(to='crewdb.CompensationSchema', verbose_name='Compensation Schema'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billing',
            name='company',
            field=models.ForeignKey(to='crewdb.Company', verbose_name='Company', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billing',
            name='member',
            field=models.ForeignKey(to='crewdb.Member', null=True, verbose_name='Crew Member'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billing',
            name='recipient',
            field=models.ForeignKey(default=crewdb.models.Billing.default_recipient, to='crewdb.BillRecipient', null=True, verbose_name='Recipient', on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billing',
            name='service',
            field=models.ManyToManyField(verbose_name='Service', null=True, blank=True, to='crewdb.Service'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='billing',
            name='vat_rate',
            field=models.ForeignKey(default=crewdb.models.Billing.default_vat_rate, to='crewdb.VatRate', null=True, verbose_name='VAT Rate', on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='advance',
            name='member',
            field=models.ForeignKey(to='crewdb.Member', verbose_name='Crew Member'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accountingdone',
            name='crew',
            field=models.OneToOneField(to='crewdb.Crew', verbose_name='Crew', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='access',
            name='crew',
            field=models.ForeignKey(to='crewdb.Crew', verbose_name='Crew'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='access',
            name='ticket',
            field=models.ForeignKey(to='crewdb.Ticket', verbose_name='Ticket'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='access',
            unique_together=set([('crew', 'ticket')]),
        ),
    ]
