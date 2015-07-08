# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.auth.models import Group, Permission
from datetime import date

def fill_vatrate(apps, percent, description, bill_title, additional_bill_comment, max_netto):
    VatRate = apps.get_model("crewdb", "VatRate")
    vatrate = VatRate()
    vatrate.rate = percent
    vatrate.description = description
    vatrate.bill_title = bill_title
    vatrate.additional_bill_comment = additional_bill_comment
    vatrate.max_netto = max_netto
    vatrate.save()

def fill_ticket(apps, type, description):
    Ticket = apps.get_model("crewdb", "Ticket")
    ticket = Ticket()
    ticket.type = type
    ticket.description = description
    ticket.save()

def fill_compensationschema(apps, schema, individual_billing):
    CompensationSchema = apps.get_model("crewdb", "CompensationSchema")
    compensationschema = CompensationSchema()
    compensationschema.schema = schema
    compensationschema.individual_billing = individual_billing
    compensationschema.save()

def fill_eventtimes(apps, date_from, date_to, fee, description):
    EventTimes = apps.get_model("crewdb", "EventTimes")
    eventtimes = EventTimes()
    eventtimes.date_from = date_from
    eventtimes.date_to = date_to
    eventtimes.fee = fee
    eventtimes.description = description
    eventtimes.save()

def fill_data(apps, schema_editor):
    fill_vatrate(apps, 0, "nach §19 Abs. 1 umsatzsteuerbefreit", "", "", 0)
    fill_vatrate(apps, 7, "Bescheid vom Finanzamt liegt vor", "", "", 0)
    fill_vatrate(apps, 19, "Bescheid vom Finanzamt liegt vor", "", "", 0)
    fill_vatrate(apps, 0, "nach §3 Nr.26 EStG umsatzsteuerbefreit", "Übungsleiterpauschale", \
      "Ich versichere, dass der hier angegebene Betrag zusammen mit\nEinkünften aus eventuellen weiteren Nebentätigkeiten nach § 3\nNr. 26 EStG den Gesamtjahreshöchstbetrag von 2400€ nicht\nüberschreitet.\n\nDiese Erklärung darf auf Anforderung dem Finanzamt vorgelegt werden.",\
        2400)
    fill_vatrate(apps, 0, "nach §3 Nr.26a EStG umsatzsteuerbefreit", "Ehrenamtspauschale", \
      "Ich versichere, dass der hier angegebene Betrag zusammen mit\nEinkünften aus eventuellen weiteren Nebentätigkeiten nach § 3\nNr. 26a EStG den Gesamtjahreshöchstbetrag von 720€ nicht\nüberschreitet.\n\nDiese Erklärung darf auf Anforderung dem Finanzamt vorgelegt werden.",\
        720)
    fill_ticket(apps, "XI/C", "all inclusive")
    fill_ticket(apps, "XI", "Zugang zu XI")
    fill_ticket(apps, "XII", "Zugang zu XII")
    fill_ticket(apps, "XIII", "Zugang zu XIII")
    fill_ticket(apps, "XIV", "Zugang zu XIV")
    fill_ticket(apps, "Artist", "Zugang zu XI")
    fill_ticket(apps, "Free", "keine Besonderheiten")
    fill_compensationschema(apps, "Einzelabrechnung", True)
    fill_compensationschema(apps, "Gruppenabrechnung", False)
    fill_eventtimes(apps, date(2015, 4, 12), date(2015, 4, 18), 3, "vor_aufbau")
    fill_eventtimes(apps, date(2015, 4, 19), date(2015, 4, 22), 3, "aufbau")
    fill_eventtimes(apps, date(2015, 4, 23), date(2015, 4, 27), 3, "festival")
    fill_eventtimes(apps, date(2015, 4, 28), date(2015, 5, 5), 3, "abbau")
    BillRecipient = apps.get_model("crewdb", "BillRecipient")
    billrecipient = BillRecipient()
    billrecipient.name = 'Event-Organisator'
    billrecipient.address = 'Partyort\n10331 Glücks-Stadt\nDeutschland\n\nUSt-ID-Nr.: DE222222222'
    billrecipient.save()

def add_group_permission(group, permission_codename):
    group.permissions.add(Permission.objects.get(codename=permission_codename))
    group.save()

def add_group_permissions(apps, schema_editor):
    #Group = apps.get_model('auth', 'Group')
    #Permission = apps.get_model('auth', 'Permission')
    group, created = Group.objects.get_or_create(name='crew_admin')   
    group.save()
    if created:
      add_group_permission(group, 'add_user')
      add_group_permission(group, 'change_user')
      add_group_permission(group, 'delete_user')
      add_group_permission(group, 'add_userextras')
      add_group_permission(group, 'change_userextras')
      add_group_permission(group, 'delete_userextras')
      add_group_permission(group, 'add_ticket')
      add_group_permission(group, 'change_ticket')
      add_group_permission(group, 'delete_ticket')
      add_group_permission(group, 'add_crew')
      add_group_permission(group, 'change_crew')
      add_group_permission(group, 'delete_crew')
      add_group_permission(group, 'add_member')
      add_group_permission(group, 'change_member')
      add_group_permission(group, 'delete_member')
      add_group_permission(group, 'add_provision')
      add_group_permission(group, 'change_provision')
      add_group_permission(group, 'delete_provision')
      add_group_permission(group, 'add_compensation')
      add_group_permission(group, 'change_compensation')
      add_group_permission(group, 'delete_compensation')
      add_group_permission(group, 'add_access')
      add_group_permission(group, 'change_access')
      add_group_permission(group, 'delete_access')
      add_group_permission(group, 'add_ticketadmin')
      add_group_permission(group, 'change_ticketadmin')
      add_group_permission(group, 'add_advance')
      add_group_permission(group, 'change_advance')
      add_group_permission(group, 'delete_advance')
      add_group_permission(group, 'add_worktime')
      add_group_permission(group, 'change_worktime')
      add_group_permission(group, 'delete_worktime')
      add_group_permission(group, 'add_eventtimes')
      add_group_permission(group, 'change_eventtimes')
      add_group_permission(group, 'add_company')
      add_group_permission(group, 'change_company')
      add_group_permission(group, 'delete_company')
      add_group_permission(group, 'add_service')
      add_group_permission(group, 'change_service')
      add_group_permission(group, 'delete_service')
      add_group_permission(group, 'add_billing')
      add_group_permission(group, 'change_billing')
      add_group_permission(group, 'add_accountingdone')
      add_group_permission(group, 'change_accountingdone')
      add_group_permission(group, 'delete_accountingdone')

    group, created = Group.objects.get_or_create(name='crew_editor')   
    if created:
      add_group_permission(group, 'change_crew')
      add_group_permission(group, 'add_member')
      add_group_permission(group, 'change_member')
      add_group_permission(group, 'delete_member')
      add_group_permission(group, 'add_provision')
      add_group_permission(group, 'change_provision')
      add_group_permission(group, 'delete_provision')
      add_group_permission(group, 'add_access')
      add_group_permission(group, 'change_access')
      add_group_permission(group, 'delete_access')
      add_group_permission(group, 'add_ticketadmin')
      add_group_permission(group, 'change_ticketadmin')
      add_group_permission(group, 'add_worktime')
      add_group_permission(group, 'change_worktime')
      add_group_permission(group, 'delete_worktime')
  
class Migration(migrations.Migration):

    dependencies = [
        ('crewdb', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_data),
        migrations.RunPython(add_group_permissions),
    ]
