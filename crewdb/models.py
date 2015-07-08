# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.db.models import Sum
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator
import datetime

from django.core.exceptions import PermissionDenied, ValidationError

from django.forms.models import model_to_dict

# import the logging library
import logging
# Get an instance of a logger, user with 'logger.debug(output)'
logger = logging.getLogger('crewdb.custom')

# regular expression to validate phone numbers
PHONE_NUMBER_REGEX = regex=r'^\+?1?\d{9,15}$'

#---------------------------------------------------------------------------------------------------------------
#- system extension tables -------------------------------------------------------------------------------------
'''
extends the standard User - Entry with thing like a contact address
editors in our Database are Users
'''
class UserExtras(models.Model):
  def __str__(self):
    if self.address:
      return self.address
    return ""

  # - model fields ------------------------------------------------
  user = models.OneToOneField(User)
  phone_regex = RegexValidator(PHONE_NUMBER_REGEX, message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'))
  phone = models.CharField(max_length=13, validators=[phone_regex], null=True, blank=True, verbose_name=_('Phone')) # validators should be a list
  address = models.TextField(null=True, blank=True, verbose_name=_('Address'))
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------
#- some models which contain data used for billing via ajax requests, not key-related to other models ----------
'''
  model containing the bill-recipient address
'''
class BillRecipient(models.Model):
  def __str__(self):
    output = self.name
    return output

  # - model fields ------------------------------------------------
  name = models.CharField(max_length=200, unique=True, verbose_name=_('Name'))
  address = models.TextField(verbose_name=_('Address'))
  class Meta:
    ordering = ['name',]
    verbose_name = _('BillRecipient object')
    verbose_name_plural = _('BillRecipient objects')

  # - model functions ---------------------------------------------
  @classmethod
  def default_recipient(cls):
    try:
      # use first recipient as default one
      return BillRecipient.objects.all()[0]
    except:
      return
  @classmethod
  def default_recipient_local(cls):
    try:
      # use first recipient as default one
      return BillRecipient.objects.all()[0].name + "\n\n" +BillRecipient.objects.all()[0].address
    except:
      return

'''
  model containing the different event times and related fees
  to be used in precalculated member bills and css
'''
class EventTimes(models.Model):
  def __str__(self):
    output = "%s - %s: %s (%0.0f €/Tag)" % (str(self.date_from), str(self.date_to), self.description, self.fee)
    return output

  # - model validator ---------------------------------------------
  def clean(self):
    if self.date_from > self.date_to:
        raise ValidationError(_("Beginning of event has to be before end of event!"))

  # - model fields ------------------------------------------------
  date_from = models.DateField(default=timezone.now, verbose_name=_('From'))
  date_to = models.DateField(default=timezone.now, verbose_name=_('To'))
  fee = models.DecimalField(max_digits=3, decimal_places=0, default=0, validators=[MinValueValidator(Decimal('0.00'))], help_text=_('Amount of money for workers per day'), verbose_name=_('Fee'))
  description = models.CharField(max_length=200, unique=True,  help_text=_('Use short description (best one word)'), verbose_name=_('Description'))
  class Meta:
    ordering = ['date_from',]
    verbose_name = _('EventTimes object')
    verbose_name_plural = _('EventTimes objects')

'''
  Companys to be used for incoming receipts
  user's should be able to add / change Company but not to delete
'''
class Company(models.Model):
  def __str__(self):
    return str(self.name)

  # - model fields ------------------------------------------------
  name = models.CharField(max_length=200, unique=True, verbose_name=_('Name'))
  phone_regex = RegexValidator(PHONE_NUMBER_REGEX, message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'))
  phone = models.CharField(max_length=13, validators=[phone_regex], null=True, blank=True, verbose_name=_('Phone')) # validators should be a list
  email = models.EmailField(max_length=75, null=True, blank=True, verbose_name=_('Email'))
  address = models.TextField(null=True, blank=True, verbose_name=_('Address'))
  class Meta:
    ordering = ['name',]
    verbose_name = _('Company object')
    verbose_name_plural = _('Company objects')

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- real interconnected crewser tables --------------------------------------------------------------------------

'''
ticket/access-types with descriptions
'''
class Ticket(models.Model):
  def __str__(self):
    return self.type + ": " + self.description

  # - model fields ------------------------------------------------
  type = models.CharField(max_length=10, unique=True, verbose_name=_('Type'))
  description = models.CharField(max_length=200, null=True, verbose_name=_('Description'))
  class Meta:
    ordering = ['type',]
    verbose_name = _('Ticket object')
    verbose_name_plural = _('Ticket objects')

'''
crew contains the Crews which are to be maintained
'''
class Crew(models.Model):
  def __str__(self):
    return self.name

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.pk, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to this Crew anymore"),
                                    params={'crew': self.name})
    except AccountingDone.DoesNotExist:
      pass

  # - model fields ------------------------------------------------
  name = models.CharField(max_length=200, unique=True, verbose_name=_('Crew name'))
  # host contact (is django-user, crew_editor or crew_admin)
  # everybody can be the admin/editor of this crew, except real 'sysadmins'
  user = models.ForeignKey(User, limit_choices_to={'is_superuser': False}, null=True, blank=True, on_delete = models.SET_NULL, verbose_name=_('Host contact'))
  budget = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00'))], verbose_name=_('Budget'))
  budget_comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))
  can_use_supporter = models.BooleanField(default=False, verbose_name=_('Can use supporter'))
  class Meta:
    ordering = ['name',]
    verbose_name = _('Crew object')
    verbose_name_plural = _('Crew objects')

  # - model functions ---------------------------------------------
  def finalized(self):
    result = False
    try:
      result = AccountingDone.objects.get(crew=self.pk).finalized
    except:
      pass
    return result
  finalized.short_description = _('Finalized')

  def __tickets_by_type(self, ticket_type):
    result = {'ticket_type' : ticket_type.type, 'ticket_name' : str(ticket_type)}
    ticket_in = TicketAdmin.objects.filter(member__crew=self.pk, ticket_in=ticket_type).aggregate(Sum('amount'))['amount__sum'] or 0
    ticket_out = TicketAdmin.objects.filter(member__crew=self.pk, ticket_out=ticket_type).aggregate(Sum('amount'))['amount__sum'] or 0
    result['ticket_all'] = Access.objects.filter(crew=self.pk, ticket=ticket_type).aggregate(Sum('amount'))['amount__sum'] or 0
    result['lanyards_planned'] = Member.objects.filter(crew=self.pk, access=ticket_type).count()
    result['members_present'] = Member.objects.filter(crew=self.pk, access=ticket_type).aggregate(Sum('access_given'))['access_given__sum'] or 0
    result['ticket_available'] = result['ticket_all'] + ticket_in - ticket_out
    if result['ticket_available'] < 0 or result['ticket_all'] - result['members_present'] < 0 or result['ticket_all'] - result['lanyards_planned'] < 0:
      result['alert_class'] = "text-error"
    else:
      result['alert_class'] = ""
    return result

  def tickets(self):
    result = []
    for ticket_type in Ticket.objects.all():
      tickets = self.__tickets_by_type(ticket_type)
      if tickets['ticket_all'] + tickets['members_present'] + tickets['ticket_available'] + tickets['lanyards_planned'] != 0:
          result.append(tickets)
    return result
  tickets.short_description = _('Tickets')

  def accounting(self):
    accounting = Billing.objects.filter(member__crew=self.pk, storno=False).aggregate(Sum('netto'), Sum('brutto'))
    budget = self.budget
    if not budget:
      budget = 0
    accounting['budget_class'] = ""
    accounting['left_budget'] = float(budget) - float(accounting['brutto__sum'] or 0)
    if accounting['left_budget'] < 0:
      accounting['budget_class'] = "text-error"
    if accounting['brutto__sum']:
      accounting['brutto__sum'] = '%0.2f €' % (accounting['brutto__sum'])
    if accounting['netto__sum']:
      accounting['netto__sum'] = '%0.2f €' % (accounting['netto__sum'])
    if accounting['left_budget']:
      accounting['left_budget'] = '%0.2f €' % (accounting['left_budget'])
    advances = []
    adv = Advance.objects.filter(member__crew=self.pk, crew_advance=True, counterbalanced=False)
    for advance in adv:
      advances.append({'member' : advance.member.name, 'member_id' : advance.member.pk, 'amount' : '%0.2f €' % (advance.amount) })
    accounting['advances'] = advances
    accounting['advance_sum'] = adv.aggregate(Sum('amount'))['amount__sum'] or 0
    return accounting

  def __calc_bills(self, Billing_queryset):
    bills = []
    netto_sum = 0
    brutto_sum = 0
    for bill in Billing_queryset:
      bills.append({'bill_nr':bill.bill_nr, 'date':bill.date, 'netto':'%0.2f €' % (bill.netto),
                    'brutto':'%0.2f €' % (bill.brutto), 'storno': bill.storno, 'pk':bill.pk,
                    'member':bill.member_local.split(":")[0], 'member_pk':bill.member.pk})
      if not bill.storno:
        netto_sum += bill.netto
        brutto_sum += bill.brutto
    return {'bills':bills, 'netto':'%0.2f €' % (netto_sum), 'brutto': '%0.2f €' % (brutto_sum)}

  def billings(self):
    billings = {}
    billings['bills'] = self.__calc_bills(Billing.objects.filter(member__crew=self.pk, receipt=False))
    billings['receipts'] = self.__calc_bills(Billing.objects.filter(member__crew=self.pk, receipt=True))
    billings['finalized'] = False
    try:
      billings['finalized'] = self.accountingdone.finalized
    except:
      pass
    return billings
  billings.short_description = _('Billings')

  def number_of_members(self):
    return Member.objects.filter(crew__name=self.name).count()
  number_of_members.short_description = _('Number of Members')

'''
members of crews, crew_contact's are noted by boolean field
'''
class Member(models.Model):
  def __str__(self):
    return self.name + ": " + self.crew.name

  def __init__(self, *args, **kwargs):
    super(Member, self).__init__(*args, **kwargs)
    # remember previous access if already given out (to trace in TicketAdmin)
    if self.access_given:
      self._prev_access = self.access
    else:
      self._prev_access = None

  def save(self,*args,**kwargs):
    super(Member, self).save(*args, **kwargs)
    if self.access_given and self._prev_access and self.access != self._prev_access:
      # if access was already given and access is changed than add ticket-action
      ticket_admin = TicketAdmin()
      ticket_admin.member = self
      ticket_admin.amount = 1
      ticket_admin.ticket_in =  self._prev_access
      ticket_admin.ticket_out = self.access
      ticket_admin.save()
      self._prev_access = self.access

  # - model validator ---------------------------------------------
  def clean(self):
    if not hasattr(self, 'crew'):
      raise ValidationError({'crew': _('You must select a crew for every member')})
    if self.access_given and (not hasattr(self, 'access') or not self.access):
      raise ValidationError({'access': _('You must select a Access-Type to give a lanyard')})
    if self.access and self.access != self._prev_access:
      # on access-change, check if crew ticket-budget is big enough
      # usually this should be ensured by javascript in change_form.html
      ticket_all = Access.objects.filter(crew=self.crew, ticket=self.access).aggregate(Sum('amount'))['amount__sum'] or 0
      lanyards_planned = Member.objects.filter(crew=self.crew, access=self.access).count()
      if ticket_all - lanyards_planned < 0:
        raise ValidationError({'access': _('There are not enough tickets for the selected Access-Type')})

    try:
      if AccountingDone.objects.get(crew=self.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Members anymore"),
                                    params={'crew': self.crew.name})
    except AccountingDone.DoesNotExist:
      pass

  # - model fields ------------------------------------------------
  crew = models.ForeignKey(Crew) # remove if related Crew is removed
  name = models.CharField(max_length=200, verbose_name=_('Name'))
  phone_regex = RegexValidator(PHONE_NUMBER_REGEX, message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'))
  phone = models.CharField(max_length=13, validators=[phone_regex], null=True, blank=True, verbose_name=_('Phone')) # validators should be a list
  email = models.EmailField(max_length=75, null=True, blank=True, verbose_name=_('Email'))
  address = models.TextField(null=True, blank=True, verbose_name=_('Address'))
  crew_contact = models.BooleanField(default=False, verbose_name=_('Crew Contact'))
  access = models.ForeignKey(Ticket, null=True, blank=True, on_delete = models.SET_NULL, help_text=_('planned access only.'), verbose_name=_('Access'))
  access_given = models.BooleanField(default=False, help_text=_('lanyard given'), verbose_name=_('Access given'))

  class Meta:
    ordering = ['name',]
    verbose_name = _('Member object')
    verbose_name_plural = _('Member objects')

  # - model functions ---------------------------------------------
  def __calc_bills(self, Billing_queryset):
    bills = []
    netto_sum = 0
    brutto_sum = 0
    for bill in Billing_queryset:
      bills.append({'bill_nr':bill.bill_nr, 'date':bill.date, 'netto':"%0.2f €" % (bill.netto,), 'brutto':"%0.2f €" % (bill.brutto,), 'storno': bill.storno, 'pk':bill.pk})
      if not bill.storno:
        netto_sum += bill.netto
        brutto_sum += bill.brutto
    return {'bills':bills, 'netto':"%0.2f €" % (netto_sum,), 'brutto': "%0.2f €" % (brutto_sum,)}

  def billings(self):
    billings = {}
    billings['bills'] = self.__calc_bills(Billing.objects.filter(member=self.pk, receipt=False))
    billings['receipts'] = self.__calc_bills(Billing.objects.filter(member=self.pk, receipt=True))
    billings['finalized'] = False
    try:
      billings['finalized'] = self.crew.accountingdone.finalized
    except:
      pass
    return billings
  billings.short_description = _('Billings')

  # amount of tickets for member, all ticket transactions from TicketAdmin are used
  def tickets(self):
    result = ""       # return string
    oneticket = True  # true if member has only one ticket
    # try for all different ticket types
    for ticket_type in Ticket.objects.all():
      amount = 0
      # how often has the member received such tickets
      tickets_out = TicketAdmin.objects.filter(member=self.pk, ticket_out = ticket_type).aggregate(Sum('amount'))
      if tickets_out['amount__sum']:
        amount += tickets_out['amount__sum']
      # how often has the member given back such tickets
      tickets_in = TicketAdmin.objects.filter(member=self.pk, ticket_in = ticket_type).aggregate(Sum('amount'))
      if tickets_in['amount__sum']:
        amount -= tickets_in['amount__sum']
      # format output
      if not amount == 0:
        if oneticket:
          if amount == 1 and result == "":
            result = ticket_type.type       # only one ticket, no special formatting
          elif result != "":
            result = "1x " + result + "<br/>"   # found more tickets, change previous 'one-ticket' result
            oneticket = False
          else:
            oneticket = False
        if not oneticket:
          result += str(Decimal(amount)) + "x " + ticket_type.type + "<br/>"
    return result
  tickets.short_description = _('Tickets')

'''
provision amounts, before, during and after festival
'''
class Provision(models.Model):
  def __str__(self):
    return str(Decimal(self.before_number)) + ":" + str(Decimal(self.during_number)) + ":" + str(Decimal(self.after_number))

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.crew.name})
    except AccountingDone.DoesNotExist:
      pass

  # - model fields ------------------------------------------------
  before_number = models.DecimalField(max_digits=4, decimal_places=0, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name=_('Before Number'))
  before_voucher = models.BooleanField(default=False, verbose_name=_('Voucher'))
  before_issued = models.BooleanField(default=False, verbose_name=_('Issued'))
  during_number = models.DecimalField(max_digits=4, decimal_places=0, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name=_('During Number'))
  during_voucher = models.BooleanField(default=False, verbose_name=_('Voucher'))
  during_issued = models.BooleanField(default=False, verbose_name=_('Issued'))
  after_number = models.DecimalField(max_digits=4, decimal_places=0, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name=_('After Number'))
  after_voucher = models.BooleanField(default=False, verbose_name=_('Voucher'))
  after_issued = models.BooleanField(default=False, verbose_name=_('Issued'))
  crew = models.OneToOneField(Crew, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Crew'))

  class Meta:
    verbose_name = _('Provision object')
    verbose_name_plural = _('Provision objects')

'''
accounting done - Rechnungslegung erfolgt, wenn Eintrag dann keine weiteren Änderungen möglich
'''
class AccountingDone(models.Model):
  def __str__(self):
    return self.crew.name + ": " + str(self.finalized)

  # - model fields ------------------------------------------------
  comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))
  comment_process = models.TextField(null=True, blank=True, verbose_name=_('Comment Realization'))
  finalized = models.BooleanField(default=False, help_text=_('no crew (and related member/bill) change possibile after Finalization!'), verbose_name=_('Finalized'))
  crew = models.OneToOneField(Crew, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Crew'))

  class Meta:
    verbose_name = _('AccountingDone object')
    verbose_name_plural = _('AccountingDone objects')

'''
Compensation schmemas, currently only distinct names are given
'''
class CompensationSchema(models.Model):
  def __str__(self):
    return self.schema

  # - model fields ------------------------------------------------
  schema = models.CharField(max_length=200, unique=True, verbose_name=_('name'))
  individual_billing = models.BooleanField(default=False, help_text=_('If active, worktimes for crew members are considered'), verbose_name=_('individual billing'))

  class Meta:
    verbose_name = _('CompensationSchema object')
    verbose_name_plural = _('CompensationSchema objects')

  # - model functions ---------------------------------------------
  # just to have a function instead of a field in member changeform_view
  def get_individual_billing(self):
    return self.individual_billing
'''
Compensation for Crew, added if required, mainly for filtering, not yet used
'''
class Compensation(models.Model):
  def __str__(self):
    return "%s: %s" % (self.crew.name, self.schema)

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.crew.name})
    except AccountingDone.DoesNotExist:
      pass

  # - model fields ------------------------------------------------
  comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))
  crew = models.OneToOneField(Crew, verbose_name=_('Crew'))
  schema = models.ForeignKey(CompensationSchema, verbose_name=_('Compensation Schema'))

  class Meta:
    verbose_name = _('Compensation object')
    verbose_name_plural = _('Compensation objects')

'''
Access'es for Crew, added if required, multiple possible
'''
class Access(models.Model):
  def __str__(self):
    return "%s: %d x %s" % (self.crew.name, self.amount, self.ticket)

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.crew.name})
    except AccountingDone.DoesNotExist:
      pass
    if self.amount == 0:
      raise ValidationError({'amount': _('You must enter the amount of tickets (or ignore this ticket type)')})
    if hasattr(self,'ticket'):
      ticket_in = TicketAdmin.objects.filter(member__crew=self.crew, ticket_in=self.ticket).aggregate(Sum('amount'))['amount__sum'] or 0
      ticket_out = TicketAdmin.objects.filter(member__crew=self.crew, ticket_out=self.ticket).aggregate(Sum('amount'))['amount__sum'] or 0
      if (self.amount - ticket_out + ticket_in < 0):
        raise ValidationError({'amount': _("The budget can't be smaller than all given-out tickets!")})

  # - model fields ------------------------------------------------
  crew = models.ForeignKey(Crew, verbose_name=_('Crew'))
  ticket = models.ForeignKey(Ticket, verbose_name=_('Ticket'))
  amount = models.DecimalField(max_digits=4, decimal_places=0, default=1, validators=[MinValueValidator(Decimal('1'))], verbose_name=_('Number'))
  class Meta:
    unique_together = ('crew', 'ticket',)
    ordering = ['ticket__type',]
    verbose_name = _('Access object')
    verbose_name_plural = _('Access objects')

  # - model functions ---------------------------------------------
  # calculate available tickets depending on all TicketAdmin entries
  def tickets_available(self):
    result = self.amount
    tickets_out = TicketAdmin.objects.filter(member__crew=self.crew, ticket_out = self.ticket).aggregate(Sum('amount'))
    if tickets_out['amount__sum']:
      result -= tickets_out['amount__sum']
    tickets_in = TicketAdmin.objects.filter(member__crew=self.crew, ticket_in = self.ticket).aggregate(Sum('amount'))
    if tickets_in['amount__sum']:
      result += tickets_in['amount__sum']
    if result < 0:
      result = '<span class="text-error ticket_amount_negative">' + str(result) + '</span>'
    return result
  tickets_available.short_description = _('Tickets available')
  tickets_available.allow_tags = True

'''
Ticket transactions, tickets in and out by date
'''
class TicketAdmin(models.Model):
  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.member.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.member.crew.name})
    except AccountingDone.DoesNotExist:
      pass

    if not self.ticket_in and not self.ticket_out:
        raise ValidationError(_("You must select a least one incoming or outgoing Ticket-Type!"))
    if self.ticket_in == self.ticket_out:
        raise ValidationError(_("It makes no sense to change tickets of the same type!"))
    # check availability of outgoing tickets for new entries
    # usually this should be ensured by javascript in change_form.html
    if not (self.pk) and self.ticket_out:
      # check if enough tickets are available to give some out
      ticket_in = TicketAdmin.objects.filter(member__crew=self.member.crew, ticket_in=self.ticket_out).aggregate(Sum('amount'))['amount__sum'] or 0
      ticket_out = TicketAdmin.objects.filter(member__crew=self.member.crew, ticket_out=self.ticket_out).aggregate(Sum('amount'))['amount__sum'] or 0
      ticket_all = Access.objects.filter(crew=self.member.crew, ticket=self.ticket_out).aggregate(Sum('amount'))['amount__sum'] or 0
      if (ticket_all - ticket_out + ticket_in - self.amount < 0):
        raise ValidationError({'amount': _("Crew has not enough tickets left!")})
    # check availability of incoming ticket-type for new entries
    # usually this should be ensured by javascript in change_form.html
    if not (self.pk) and self.ticket_in:
      ticket_all = Access.objects.filter(crew=self.member.crew, ticket=self.ticket_in).aggregate(Sum('amount'))['amount__sum'] or 0
      if ticket_all == 0:
        raise ValidationError({'ticket_in': _("Crew has no tickets of this type!")})

  # - model fields ------------------------------------------------
  member = models.ForeignKey(Member, verbose_name=_('Crew Member'))
  amount = models.DecimalField(max_digits=4, decimal_places=0, default=1, validators=[MinValueValidator(Decimal('1'))], verbose_name=_('Amount'))
  ticket_in = models.ForeignKey('Ticket', related_name='ticket_in', default="", null=True, blank=True, verbose_name=_('Ticket to Host (in)'))
  ticket_out = models.ForeignKey('Ticket', related_name='ticket_out', default="", null=True, blank=True, verbose_name=_('Ticket to Member (out)'))
  date = models.DateTimeField(default=timezone.now, verbose_name=_('Date'))
  class Meta:
    ordering = ['date',]
    verbose_name = _('TicketAdmin object')
    verbose_name_plural = _('TicketAdmin objects')

  # - model functions ---------------------------------------------
  def __str__(self):
    output = str(self.date) + ": " + str(Decimal(self.amount)) + "x ("
    if self.ticket_in:
      output += self.ticket_in.type + ": " + self.ticket_in.description
    output += "==>"
    if self.ticket_out:
      output += self.ticket_out.type + ": " + self.ticket_out.description
    output += ")"
    return output

'''
Advance Money
'''
class Advance(models.Model):
  def __str__(self):
    output = str(self.date) + ": " + str(Decimal(self.amount))
    return output

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if hasattr(self.member, 'crew') and AccountingDone.objects.get(crew=self.member.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.member.crew.name})
    except AccountingDone.DoesNotExist:
      pass
    #if self.amount == 0:
      #raise ValidationError({'amount': _('No advance if no money involved!')})

  # - model fields ------------------------------------------------

  member = models.ForeignKey(Member, verbose_name=_('Crew Member'))
  amount = models.DecimalField(max_digits=7, decimal_places=0, default=0, validators=[MinValueValidator(Decimal('0.01'))], help_text=_('use dot instead of comma for decimals'), verbose_name=_('Money'))
  comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))
  date = models.DateTimeField(default=timezone.now, verbose_name=_('Date'))
  crew_advance = models.BooleanField(default=False, verbose_name=_('Advance for Crew'))
  counterbalanced = models.BooleanField(default=False, verbose_name=_('Counterbalanced'))
  class Meta:
    ordering = ['date',]
    verbose_name = _('Advance object')
    verbose_name_plural = _('Advance objects')

'''
registers the work-time for crew members, only relevant for crews with individual billing
'''
class WorkTime(models.Model):
  def __str__(self):
    output = str(self.member) + " " + str(self.days()) + " days"
    return output

  # - model validator ---------------------------------------------
  def clean(self):
    try:
      if AccountingDone.objects.get(crew=self.member.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.member.crew.name})
    except AccountingDone.DoesNotExist:
      pass
    try:
      if not self.member.crew.compensation.schema.individual_billing:
        raise ValidationError(_("Work Times should only be registered for Members of Crews with individual billing"))
    except:
      raise ValidationError(_("Work Times should only be registered for Members of Crews with individual billing"))
    if self.date_from > self.date_to:
      raise ValidationError(_("Beginning of work phase has to be before the end!"))

  # - model fields ------------------------------------------------
  member = models.ForeignKey(Member, verbose_name=_('Crew Member'))
  date_from = models.DateField(default=timezone.now, verbose_name=_('From'))
  date_to = models.DateField(default=timezone.now, verbose_name=_('To'))
  comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))
  class Meta:
    ordering = ['date_from',]
    verbose_name = _('WorkTime object')
    verbose_name_plural = _('WorkTime objects')


  # - model functions ---------------------------------------------
  def days(self):
    return (self.date_to-self.date_from).days + 1
  days.short_description = _('Days')

  # parser to split worktime into different segments depending on EventTimes for billing
  def __eventparser(self, date_from, date_to, resultList):
    # search eventTimes which are matching the starting date
    work_part_from = EventTimes.objects.filter(date_from__lte=date_from).order_by('date_from')  # event_start <= from
    work_part_from_valid = work_part_from.filter(date_to__gte=date_from).order_by('date_from')  # event_end > from
    work_part_to = EventTimes.objects.filter(date_to__gte=date_to).order_by('date_from')        # event_end >= to
    work_part_to_valid = work_part_to.filter(date_from__lte=date_to).order_by('date_from')      # event_start < to
    oneday = datetime.timedelta(1)
    # 'from' and 'to' during event:
    if work_part_from_valid and work_part_to_valid:
      if work_part_from_valid[0] == work_part_to_valid[0]: # same event, great
        resultList.append({'from':date_from, 'to':date_to, 'fee':work_part_from_valid[0].fee})
      else: # not the same event
        resultList.append({'from':date_from, 'to':work_part_from_valid[0].date_to, 'fee':work_part_from_valid[0].fee})
        return self.__eventparser(work_part_from_valid[0].date_to + oneday, date_to, resultList)
    # 'from' is during event, 'to' is not during event:
    elif work_part_from_valid:
      resultList.append({'from':date_from, 'to':work_part_from_valid[0].date_to, 'fee':work_part_from_valid[0].fee})
      return self.__eventparser(work_part_from_valid[0].date_to + oneday, date_to, resultList)
    # 'from' is not during event, 'to' is during event:
    elif work_part_to_valid:
      if work_part_from:  # 'from' is after event
        section = EventTimes.objects.filter(date_from__gt=date_from, date_from__lte=date_to).order_by('date_from')
        resultList.append({'from':date_from, 'to':section[0].date_from - oneday, 'fee':"XX"})
        return self.__eventparser(section[0].date_from, date_to, resultList)
      else: # 'from' is before event
        current_end_date = EventTimes.objects.all().order_by('date_from')[0].date_from - oneday
        resultList.append({'from':date_from, 'to':current_end_date, 'fee':"XX"})
        return self.__eventparser(EventTimes.objects.all().order_by('date_from')[0].date_from, date_to, resultList)
    # 'from' and 'to' are not during the event:
    else:
      if work_part_from or work_part_to:  # 'from' is after event or 'to' is before the event
        section = EventTimes.objects.filter(date_from__lt=date_to, date_to__gt=date_from).order_by('date_from')
        if (section):
          resultList.append({'from':date_from, 'to':section[0].date_from - oneday, 'fee':"XX"})
          return self.__eventparser(section[0].date_from, date_to, resultList)
        else:
          resultList.append({'from':date_from, 'to':date_to, 'fee':"XX"})
      else:
        current_end_date = EventTimes.objects.all().order_by('date_from')[0].date_from - oneday
        resultList.append({'from':date_from, 'to':current_end_date, 'fee':"XX"})
        return self.__eventparser(EventTimes.objects.all().order_by('date_from')[0].date_from, date_to, resultList)
    return resultList

  # use eventparser and return string for further usage in views.py (ajax request)
  def days_fee(self):
    resultList = self.__eventparser(self.date_from, self.date_to, [])
    result = []
    for entry in resultList:
      entry['days'] = str((entry['to']-entry['from']).days + 1)
      entry['to'] = str(entry['to'])
      entry['from'] = str(entry['from'])
      result.append(entry)
    return result
  days_fee.short_description = _('Days + Fee')

'''
  VAT - Value added tax
  Umsatzsteuer
'''
class VatRate(models.Model):
  '''
  will be intially filled with:
  0%  nach §19 Abs. 1 umsatzsteuerbefreit
  7%  Bescheid vom Finanzamt liegt vor
  19% Bescheid vom Finanzamt liegt vor
  '''
  def __str__(self):
    # str is used for calculations in billing change_form, beginning MUST be the rate
    text = str(Decimal(self.rate)) + "%, " + self.description
    if self.bill_title:
      text += " (" + self.bill_title + ")"
    return text

  # - model fields ------------------------------------------------
  rate = models.DecimalField(max_digits=2, decimal_places=0, validators=[MinValueValidator(Decimal('0'))], verbose_name=_('VAT rate %'))
  description = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Description'))
  bill_title = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Bill Title'))
  additional_bill_comment = models.TextField(null=True, blank=True, verbose_name=_('Additional Bill Comment'))
  max_netto = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], verbose_name=_('Maximal Netto'))

  class Meta:
    ordering = ['rate',]
    verbose_name = _('VatRate object')
    verbose_name_plural = _('VatRate objects')

  # - model functions ---------------------------------------------
  @classmethod
  def default_rate(cls):
    try:
      # use highest rate as default
      return VatRate.objects.order_by('-rate')[0]
    except:
      return

'''
  Service Cataloque
  Leistungskatalog
'''
class Service(models.Model):
  def __str__(self):
    text = self.service
    if self.vat_rate:
      text += " (" + self.vat_rate.bill_title + ")"
    return text

  # - model fields ------------------------------------------------
  service = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Service'))
  vat_rate = models.ForeignKey(VatRate, null=True, blank=True, help_text=_('If none selected, service available for all bills'), verbose_name=_('Allowed Vat-Rates'))

  class Meta:
    ordering = ['service',]
    verbose_name = _('Service object')
    verbose_name_plural = _('Service objects')


# http://stackoverflow.com/questions/1355150/django-when-saving-how-can-you-check-if-a-field-has-changed
class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])

'''
  Billing Table
  - jede Rechnung wird einem Member zugeordnet
  - bei direkten Auszahlungen ist der Member die Empfängeradresse
  - bei Quittungen ist die Ziel-Company die Empfängeradresse
  - alle Rechnungsfelder sind komplett editierbar und werden in der Rechnung gespeichert
    - also bspw. Adresse wird von Member übernommen, kann aber editiert werden und
      wird auf jeden Fall direkt im Billing gesichert
  - eine Änderung von Einträgen wird durch die Validation unterbunden!
'''
class Billing(models.Model, ModelDiffMixin):
  def __str__(self):
    return str(self.member) + " " + str(self.date) + " " + str(Decimal(self.brutto)) + "€"

  # - model validator ---------------------------------------------
  def clean(self):
    # Don't allow any change on existing entries - just to be save
    # this does also prevent including any related Billing information in AdminInlines
    if self.pk: # primary key exists == entry exists
      if self.get_field_diff('storno'):
        for key in self.diff:
          # reset all fields to previous value (except storno)
          if key != 'storno':
            setattr(self, key, self.diff[key][0])
        return
      else:
        raise PermissionDenied()

    if not hasattr(self, 'member') or not self.member:
      raise ValidationError({'member': _('You must select a member for every billing / receipt')})

    try:
      if AccountingDone.objects.get(crew=self.member.crew, finalized=True):
        raise ValidationError(_("Billing for Crew %(crew)s is finalized, you are not allowed to do any changes to Crew-Items anymore"),
                                    params={'crew': self.member.crew.name})
    except AccountingDone.DoesNotExist:
      pass

    if self.receipt and self.vat_rate.bill_title != "":
      raise ValidationError({'vat_rate': _('You have selected some invalid vat-rate!')})

    # check not required anymore - storno of bills is now possible
    #try:
      #latest = Billing.objects.latest('pk')
      #if (not latest.storno and self.receipt == latest.receipt and self.member == latest.member and
          #self.company == latest.company and self.invoicing_party == latest.invoicing_party and
          #self.tax_nr == latest.tax_nr and self.tax_id == latest.tax_id and
          #self.vat_id == latest.vat_id and self.netto == latest.netto and self.brutto == latest.brutto):
        #raise ValidationError(_('You try to submit same dataset twice! Please check and change before continuing!'))
    #except Billing.DoesNotExist:
      #pass
    
    # dependencies of vAT_Rate with VAT-Ids etc. are not checked anymore, too complex
    #if (not self.receipt and self.vat_rate.rate == 0 and self.vat_id == ""):
      #raise ValidationError({'vat_id': _('VAT-Rate 0%s requires a VAT ID.') % ('%')})
    #if (not self.receipt and self.vat_rate.rate == 7 and self.tax_nr == ""):
      #raise ValidationError({'tax_nr': _('VAT-Rate 7%s requires a Tax Number.') % ('%')})
    #if (not self.receipt and self.vat_rate.rate == 19 and self.tax_id == ""):
      #raise ValidationError({'tax_id': _('VAT-Rate 19%s requires a Tax ID.') % ('%')})
      
    if (not self.receipt and self.netto == 0):
      raise ValidationError({'netto': _('You should enter some value here!')})
    if (self.receipt and self.brutto == 0):
      raise ValidationError({'brutto': _('You should enter some value here!')})

    if (self.vat_rate.max_netto != 0 and self.netto > self.vat_rate.max_netto):
      raise ValidationError({'netto': _('Netto-Value to big for selected VAT-Rate (max %(max)d €)') % {'max': self.vat_rate.max_netto }})

    self.member_local = self.member.name + ": " + self.member.crew.name
    self.vat_rate_local = str(Decimal(self.vat_rate.rate)) + "%, " + self.vat_rate.description
    if self.vat_rate.bill_title:
      self.vat_rate_local += " (" + self.vat_rate.bill_title + ")"
    
    if (self.vat_rate.additional_bill_comment):
      self.comment = self.comment + "\n\n" + self.vat_rate.additional_bill_comment

  # - model functions ---------------------------------------------
  def default_bill_nr():
    try:
      num = Billing.objects.latest('pk').pk + 1
    except:
      num = 1
    try:
      return "%s-%05d" % (timezone.now().strftime('%Y-%m'), num)
    except:
      return 0

  def default_recipient():
    try:
      return BillRecipient.default_recipient()
    except:
      return 0

  def default_recipient_local():
    try:
      return BillRecipient.default_recipient_local()
    except:
      return 0

  def default_vat_rate():
    try:
      return VatRate.default_rate()
    except:
      return 0

  # - model fields ------------------------------------------------
  class Meta:
    verbose_name = _('Billing object')
    verbose_name_plural = _('Billing objects')

  # internal date of bill creation, not shown on bill
  date_internal = models.DateField(auto_now_add=True)
  # indicates if billing entry is bill or receipt
  receipt = models.BooleanField(default=False, verbose_name=_('Receipt'))

  # recipient, usually always the same
  recipient = models.ForeignKey(BillRecipient, default=default_recipient, null=True, on_delete = models.SET_NULL, verbose_name=_('Recipient'))
  # store recipient independent from other tables in local field
  recipient_local = models.TextField(default=default_recipient_local, verbose_name=_('Recipient'))

  # member for whom bill was created, foreignkey to member table
  # on_delete: delete member will try to remove the related billing rows as well, which fails with error
  #  this will prevent non-superusers from removing members with billings
  member = models.ForeignKey(Member, null=True, verbose_name=_('Crew Member'))
  # store member+crew name independent from other tables
  member_local = models.CharField(max_length=400, blank=True, verbose_name=_('Crew Member'))

  # company is only used for incoming bills to autofill the invoicing_party-field.
  # it is not required, as long as invoicing_party-field is filled
  company = models.ForeignKey('Company', null=True, blank=True, on_delete = models.SET_NULL, verbose_name=_('Company'))

  # Rechnungssteller
  invoicing_party = models.TextField(verbose_name=_('invoicing Party'))

  # für Rechnungen und Quittungen
  tax_nr = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Tax-Number'))
  bill_nr = models.CharField(max_length=200, default=default_bill_nr, verbose_name=_('Bill-Number'))

  # nur für Rechnungen, nicht für Quittungen
  vat_id = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('VAT ID'))
  tax_id = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Tax ID'))

  # Rechnungsdatum, muss nicht gleich dem internen Datum sein (date_internal)
  date = models.DateField(default=timezone.now, verbose_name=_('Datum'))

  # Leistung (bei Rechnungen als Katalog, eingebunden über Service, kopiert nach service_free)
  service = models.ManyToManyField(Service, null=True, blank=True, verbose_name=_('Service'))
  service_free = models.TextField(null=True, blank=True, verbose_name=_('Service'))

  comment = models.TextField(null=True, blank=True, verbose_name=_('Comment'))

  # wichtig bei Quittungen
  delivery_date = models.DateField(null=True, blank=True, default=timezone.now, verbose_name=_('Delivery date'))

  # bei Quittung (Company) wird brutto angegeben und netto berechnet,
  # bei Rechnung für Member umgekehrt - per javascript im frontend regeln!
  netto = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name=_('Netto'))
  brutto = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name=_('Brutto'))

  vat_rate = models.ForeignKey('VatRate', default=default_vat_rate, null=True, on_delete = models.SET_NULL, verbose_name=_('VAT Rate'))
  # store vat-rate indenpendent from other table
  vat_rate_local = models.CharField(max_length=250, blank=True, verbose_name=_('VAT Rate'))

  reverse_charge = models.BooleanField(default=False, verbose_name=_('Reverse Charge'))
  storno = models.BooleanField(default=False, verbose_name=_('Storno'))
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
