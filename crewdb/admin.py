# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.contrib.admin.templatetags.admin_list import _boolean_icon

from crewdb.models import Member, Crew, UserExtras, Ticket, Provision, Compensation, TicketAdmin, Access, CompensationSchema, Advance, WorkTime, Billing, Company, EventTimes, Service, VatRate, AccountingDone, BillRecipient

from django.db.models.signals import post_save
from django.dispatch import receiver

from django import forms
from django.forms.models import BaseInlineFormSet
from django.core.urlresolvers import reverse

from suit.widgets import EnclosedInput, AutosizedTextarea

from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError

# import the logging library
import logging
# Get an instance of a logger, user with 'logger.debug(output)'
logger = logging.getLogger('crewdb.custom')

from django.conf.global_settings import TEMPLATE_LOADERS
#logger.debug(TEMPLATE_LOADERS)

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------
'''
set default values after user creation (staff, group)
https://stackoverflow.com/questions/8949303/how-to-assign-a-user-to-a-group-at-signup-using-django-userena
'''
@receiver(post_save, sender=User, dispatch_uid='crewser.crewdb.models.user_post_save_handler')
def user_post_save(sender, instance, created, **kwargs):
  ''' This method is executed whenever an user object is saved
  '''
  if created:
    try:
      instance.groups.add(Group.objects.get(name='crew_editor'))
      instance.is_staff = True
      instance.save()
    except Group.DoesNotExist:
      pass
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- standard inline-views for CrewAdmin-Page --------------------------------------------------------------------
class AccessInline(admin.TabularInline):
  model = Access
  fields = ('amount', 'ticket', 'tickets_available',)
  readonly_fields = ('tickets_available',) 
  extra = 0
  suit_classes = 'suit-tab suit-tab-provision'
  
  # only allow superuser and crewdb-admin to change some settings
  def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all()):
        return ['tickets_available']
    return ['amount', 'ticket', 'tickets_available']
  def has_add_permission(self, request, obj=None):
    return request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all())
  def has_delete_permission(self, request, obj=None):
    return request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all())

class ProvisionInline(admin.StackedInline):
  model = Provision
  fieldsets = (
    (None, {'fields': (('before_number', 'before_voucher', 'before_issued'),
                       ('during_number', 'during_voucher', 'during_issued'),
                       ('after_number', 'after_voucher', 'after_issued'),), 'classes': ('wide', 'extrapretty'),}),
  )
  suit_classes = 'suit-tab suit-tab-provision'

  # only allow superuser and crewdb-admin to change some settings
  def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all()):
        return []
    return ['before_number', 'before_voucher', 'before_issued', \
        'during_number', 'during_voucher', 'during_issued', \
        'after_number', 'after_voucher', 'after_issued']

class CompensationInline(admin.StackedInline):
  model = Compensation
  fieldsets = (
    (None, {'fields': (('schema', 'comment'),), 'classes': ('wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  extra = 0
  can_delete = False
  suit_classes = 'suit-tab suit-tab-billing'

class AccountingDoneInline(admin.StackedInline):
  model = AccountingDone
  fieldsets = (
    (None, {'fields': (('comment', 'comment_process'),('finalized')), 'classes': ('wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  extra = 0
  suit_classes = 'suit-tab suit-tab-billing'

  # - functions ---------------------------------------------------
  # accountingdone can't changed back in crew interface (go to settings for that)
  def get_readonly_fields(self, request, obj=None):
    if obj and AccountingDone.objects.filter(crew=obj.pk, finalized=True):
      return ['finalized',]
    return []

'''
special inline for ContactMembers
only display Crew Contacts, handled by 'get_queryset'
use special Formset to register initial values for undisplayed fields
  -  (added Crew Contacts must have boolean crew_contact set to true)
  -> they will be set via CrewAdmin save_formset
'''
class ContactMemberFormSet(BaseInlineFormSet):
  def __init__(self, *args, **kwargs):
    super(ContactMemberFormSet, self).__init__(*args, **kwargs)
    self.initial = [{'crew_contact': True}]

class ContactMemberInline(admin.StackedInline):
  model = Member
  formset = ContactMemberFormSet
  verbose_name = _("Crew Contact")
  verbose_name_plural = _("Crew Contacts")
  fieldsets = (
    (None, {'fields': (('edit_member', 'name', 'phone', 'email'),
                       ('address', 'crew_contact'),
                       ('access', 'access_given', 'tickets')), 'classes': ('wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  can_delete = False
  readonly_fields = ('edit_member', 'tickets',) 
  extra = 0
  suit_classes = 'suit-tab suit-tab-general'

  # - functions ---------------------------------------------------
  # return edit-member link
  def edit_member(self, obj):
    # if it's a new field, name not yet filled, link will not work
    if (obj.name == ""):
      return ""
    return _('<a href="{0}{1}" class="btn"><i class="icon-user"></i>Edit</a>').format(
      reverse('admin:crewdb_member_changelist',), obj.pk)
  edit_member.allow_tags = True
  edit_member.short_description = _('Member')

  # return ticket status but add link to change the tickets
  def tickets(self, obj):
    # if it's a new field, name not yet filled, link will not work
    if (obj.name == ""):
      return ""
    # get number of tickets from model
    result = obj.tickets()
    # if no tickets provide some value to add the link
    if result == "":
      result = "----"
    # create the change-ticket (change member) link
    return '<a href="{0}{1}">{2}</a>'.format(
      reverse('admin:crewdb_member_changelist',), obj.pk, result)
  tickets.allow_tags = True
  tickets.short_description = _('Tickets')

  # only display Crew Contacts
  def get_queryset(self, request):
    return Member.objects.filter(crew_contact = True)

'''
inline-view for Members of Crew
this will show all members, without the ones from ContactMemberInline
'''
class MemberInlineFormSet(BaseInlineFormSet):
  def clean(self):
    # ensure that all new expected lanyards of all members don't exceed the amount of available crew-tickets
    # usually this should be ensured by javascript in change_form.html
    tickets = {}
    index = 0

    # count all available tickets based on new changes (self.data contains all POST data)
    while self.data.get('access_set-' + str(index) + '-ticket'):
      if self.data.get('access_set-' + str(index) + '-DELETE') == 'on':
        # take care of to-be-removed ticket budgets
        tickets[self.data.get('access_set-' + str(index) + '-ticket')] = 0
      else:
        tickets[self.data.get('access_set-' + str(index) + '-ticket')] = self.data.get('access_set-' + str(index) + '-amount')
      index += 1
    
    # if new changes are not available, use stored data as reference instead
    # this happens when common users have some readonly ticket-budget
    if (index == 0 and self.cleaned_data[0].get('crew')):
      for access in Access.objects.filter(crew=self.cleaned_data[0].get('crew').pk):
        tickets[str(access.ticket.pk)] = access.amount

    #count all planned lanyards of contact members
    index = 0
    while self.data.get('member_set-' + str(index) + '-access'):
      if self.data.get('member_set-' + str(index) + '-access') in tickets:
        tickets[self.data.get('member_set-' + str(index) + '-access')] = int(tickets[self.data.get('member_set-' + str(index) + '-access')]) - 1
      else:
        raise ValidationError(_('There are not enough tickets for your access selections'))
      index += 1

    #count all planned lanyards of common members
    index = 0
    while self.data.get('member_set-2-' + str(index) + '-access'):
      if self.data.get('member_set-2-' + str(index) + '-access') in tickets:
        tickets[self.data.get('member_set-2-' + str(index) + '-access')] = int(tickets[self.data.get('member_set-2-' + str(index) + '-access')]) - 1
      else:
        raise ValidationError(_('There are not enough tickets for your access selections'))
      index += 1

    #if any ticket-value is below zero, reject cleaning
    for ticket in tickets:
      if int(tickets[ticket]) < 0:
        raise ValidationError(_('There are not enough tickets for your access selections'))

class MemberInline(admin.TabularInline):
  model = Member
  formset = MemberInlineFormSet
  fieldsets = (
    (None, {'fields': (('edit_member', 'name', 'phone', 'email', 'access', 'tickets'),), 'classes': ('wide', 'extrapretty'),}),
  )
  readonly_fields = ('edit_member', 'tickets',) 
  can_delete = False
  extra = 5
  suit_classes = 'suit-tab suit-tab-general'

  # - functions ---------------------------------------------------
  # return edit-member link
  def edit_member(self, obj):
    # if it's a new field, name not yet filled, link will not work
    if (obj.name == ""):
      return ""
    return _('<a href="{0}{1}" class="btn"><i class="icon-user"></i>Edit</a>').format(
      reverse('admin:crewdb_member_changelist',), obj.pk)
  edit_member.allow_tags = True
  edit_member.short_description = _('Member')

  # return ticket status but add link to change the tickets
  def tickets(self, obj):
    # if it's a new field, name not yet filled, link will not work
    if (obj.name == ""):
      return ""
    # get number of tickets from model
    result = obj.tickets()
    # if no tickets provide some value to add the link
    if result == "":
      result = "----"
    # create the change-ticket (change member) link
    return '<a href="{0}{1}">{2}</a>'.format(
      reverse('admin:crewdb_member_changelist',), obj.pk, result)
  tickets.allow_tags = True
  tickets.short_description = _('Tickets')

  # only display Crew Contacts
  def get_queryset(self, request):
    return Member.objects.filter(crew_contact = False)

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- CrewAdmin-Page ----------------------------------------------------------------------------------------------

# spezial filter to show crew by finalized status
class FinalizedListFilter(admin.SimpleListFilter):
    title = _('Status')
    parameter_name = '_finalized'

    def lookups(self, request, model_admin):
        return (('True', _('finalized')), ('False', _('not finalized')),)

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(accountingdone__finalized=True)
        if self.value() == 'False':
            return queryset.filter(Q(accountingdone=None)|Q(accountingdone__finalized=False))

class CrewAdminForm(forms.ModelForm):
  class Meta:
    widgets = {
      'budget': EnclosedInput(append='€'),
    }
class CrewAdmin(admin.ModelAdmin):
  class Media:
    css = { "all" : ("admin/css/crewadmin.css",) }  

  form = CrewAdminForm
  inlines = [ContactMemberInline, ProvisionInline, AccessInline, CompensationInline, AccountingDoneInline, MemberInline]
  
  fieldsets = (
    (None, {'fields': (('name', 'user'),
                       ('can_use_supporter',)), 'classes': ('suit-tab', 'suit-tab-general', 'wide', 'extrapretty'),}),
    (_('Budget'), {'fields': (('budget', 'budget_comment'),), 'classes': ('suit-tab', 'suit-tab-billing', 'wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }

  # - django-suit additionals -------------------------------------
  suit_form_includes = (
        ('admin/crewdb/crew/accounting_inline.html', 'middle', 'general'),
        ('admin/crewdb/crew/tickets_inline.html', 'middle', 'general'),
        ('admin/crewdb/billing/billing_inline.html', 'bottom', 'billing'),
  )
  suit_form_tabs = (('general', _('General')), ('provision', _('Provisions/Access')), ('billing', _('Accounting')))

  # - configurations for list-view --------------------------------
  list_display = ('name', 'user', 'can_use_supporter', '_finalized')
  list_display_links = ('name',)
  search_fields = ['name']
  actions = None

  # - functions ---------------------------------------------------
  def _finalized(self, obj):
    return _boolean_icon(obj.finalized())
  _finalized.short_description = _('Finalized')

  def response_change(self, request, obj):
    if "_addbill" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_crew=%s#bill" % obj.pk)
    if "_addreceipt" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_crew=%s#receipt" % obj.pk)
    return super(CrewAdmin, self).response_change(request, obj)

  def has_add_bill_permission(self):
    perm = self._request_user.has_perm('crewdb.add_billing')
    return perm

  # add extra-context to change view, required to display billings via admin/crewdb/crew/billing_inline.html
  def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    extra_context = extra_context or {}
    if (object_id):
      extra_context['billings'] = Crew.objects.get(pk=object_id).billings
      extra_context['tickets'] = Crew.objects.get(pk=object_id).tickets
      extra_context['accounting'] = Crew.objects.get(pk=object_id).accounting
    self._request_user = request.user
    extra_context['has_addbill_perm'] = self.has_add_bill_permission
    return super(CrewAdmin, self).changeform_view(request, object_id, form_url, extra_context)
  
  # limit standard view to not finalized crews
  def changelist_view(self, request, extra_context=None):
    if not request.META['QUERY_STRING'] and \
      not request.META.get('HTTP_REFERER', '').startswith(request.build_absolute_uri()):
      return HttpResponseRedirect(request.path + "?_finalized=False")
    return super(CrewAdmin,self).changelist_view(request, extra_context=extra_context)

  '''
  modify save_formset to use special default if inlines have them stored in formset.initial
  used to set crew_contact to true in ContactMemberInline (but not in MemberInline!)
  '''
  def save_formset(self, request, form, formset, change):
    if not hasattr(formset, 'initial') or formset.initial == None:
      return super(CrewAdmin, self).save_formset(request, form, formset, change)
    instances = formset.save(commit=False)
    for instance in instances:
      if not instance.pk:
        for values in formset.initial:
          for key, value in values.items():
            setattr(instance, key, value)
      instance.save()
    formset.save_m2m()
  '''
  access control
  http://www.b-list.org/weblog/2008/dec/24/admin/
  '''
  def admin_req(self, request):
    return request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all())
  # hide crew-admin filter on non crew-admin pages
  def get_list_filter(self, request):
      if not self.admin_req(request):
        return []
      return ['user', FinalizedListFilter]
  # prevent crew_editors to change special fields in Crew database
  def get_readonly_fields(self, request, obj=None):
      if not self.admin_req(request):
        return ['number_of_members', 'finalized', 'name', 'user', 'budget', 'budget_comment',]
      return ['number_of_members', 'finalized']
  # prevent crew_editors to change non-owned crews
  def get_queryset(self, request):
    if self.admin_req(request):
        return Crew.objects.all()
    return Crew.objects.filter(user=request.user)
  def has_change_permission(self, request, obj=None):
    has_class_permission = super(CrewAdmin, self).has_change_permission(request, obj)
    if not has_class_permission:
        return False
    if obj is not None and (not obj.user or request.user.id != obj.user.id) and not self.admin_req(request):
        return False
    return True
  
  # hide delete-action for non-admin users
  def has_delete_permission(self, request, obj=None):
    if self.admin_req(request):
      self.actions = []
    else:
      self.actions = None
    return self.admin_req(request)

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- standard inline-views for MemberAdmin-Page ------------------------------------------------------------------

# main admin for ticketadmin - only used to derive used inlines
class TicketAdminInline(admin.TabularInline):
  model = TicketAdmin
  verbose_name = _("Ticket Action")
  verbose_name_plural = _("Ticket Sending / Changing / Giving In+Out")
  extra = 0
  suit_classes = 'suit-tab suit-tab-general'

# ticketadmin view - read-only, no adding option
class TicketAdminViewInline(TicketAdminInline):
  fieldsets = (
    (None, {'fields': (('amount', 'ticket_out', 'ticket_in', 'date', ),), 'classes': ('wide', 'extrapretty'),}),
  )
  verbose_name_plural = _("Ticket Sending / Changing / Giving In+Out")
  readonly_fields = ('amount', 'ticket_out', 'ticket_in', 'date',)
  def has_add_permission(self, request, obj=None):
    return False
  def has_delete_permission(self, request, obj=None):
    return False

# ticketadmin add area - no change, no display of other entries
class TicketAdminAddInline(TicketAdminInline):
  fieldsets = (
    (None, {'fields': (('amount', 'ticket_out', 'ticket_in', ),), 'classes': ('wide', 'extrapretty'),}),
  )
  class Media:
    css = { "all" : ("admin/css/hide_headers.css",) }
  verbose_name_plural = ""
  def has_change_permission(self, request, obj=None):
    return False
  
# main admin for advanceadmin - only used to derive used inlines
class AdvanceAdminInlineForm(forms.ModelForm):
  class Meta:
    widgets = {
      'amount': EnclosedInput(append='€'),
    }
class AdvanceAdminInline(admin.StackedInline):
  model = Advance
  form = AdvanceAdminInlineForm
  verbose_name = _("Advance")
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  can_delete = False
  extra = 0
  suit_classes = 'suit-tab suit-tab-billing'

# advanceadmin view - read-only, no adding option
class AdvanceAdminViewInline(AdvanceAdminInline):
  fieldsets = (
    (None, {'fields': (('_amount', 'comment', 'date', 'counterbalanced'),('crew_advance',)), 'classes': ('wide', 'extrapretty'),}),
  )
  readonly_fields = ('_amount', 'comment', 'date', 'crew_advance',)
  def _amount(self, obj):
    return "%0.2f €" % (obj.amount,)
  _amount.short_description = _('Amount')

  def has_add_permission(self, request, obj=None):
    return False
  def has_delete_permission(self, request, obj=None):
    return False

# advanceadmin add area - no change, no display of other entries
class AdvanceAdminAddInline(AdvanceAdminInline):
  fieldsets = (
    (None, {'fields': (('amount', 'comment', ),('crew_advance',)), 'classes': ('wide', 'extrapretty'),}),
  )
  class Media:
    css = { "all" : ("admin/css/hide_headers.css",) }
  verbose_name_plural = ""
  def has_change_permission(self, request, obj=None):
    return False

class WorkTimeAdminInline(admin.StackedInline):
  class Media:
    css = { "all" : ("admin/css/calendar_events.css",) }
  model = WorkTime
  fieldsets = (
    (None, {'fields': (('date_from', 'date_to',),
                       ('comment',)), 'classes': ('wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  extra = 0
  suit_classes = 'suit-tab suit-tab-worktimes'
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- MemberAdmin-Page ----------------------------------------------------------------------------------------------
class MemberAdminForm(forms.ModelForm):
  class Meta:
    widgets = {
      'email': EnclosedInput(append='icon-envelope'),
    }
class MemberAdmin(admin.ModelAdmin):
  class Media:
    css = { "all" : ("admin/css/memberadmin.css",) }

  form = MemberAdminForm
  inlines = [TicketAdminViewInline, TicketAdminAddInline, AdvanceAdminViewInline, AdvanceAdminAddInline, WorkTimeAdminInline]

  fieldsets = (
    (None, {'fields': (('name', 'phone', 'email',),('address',),('access', 'access_given', 'tickets'),('crew', 'crew_id', 'crew_contact',)),
            'classes': ('suit-tab', 'suit-tab-general', 'wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }
  ## calculated fields must be readonly
  readonly_fields = ['tickets', '_access']

  # - django-suit additionals -------------------------------------
  suit_form_includes = (
        ('admin/crewdb/billing/billing_inline.html', 'bottom', 'billing'),
  )
  suit_form_tabs = (('general', _('General')), ('worktimes', _('Work Times')), ('billing', _('Billing')))

  # - configurations for list-view --------------------------------
  list_display = ['name', 'phone', 'email', '_access', 'tickets', 'crew_link']
  search_fields = ['name', 'email']
  list_filter = ('crew','crew_contact')
  list_display_links = ('name',)

  def _access(self, obj):
    if obj.access:
      return str(obj.access) + " " + _boolean_icon(obj.access_given)
    return ""
  _access.allow_tags = True
  _access.short_description = _('Access')

  def crew_id(self, obj):
    return "<span id='crew_id'>" + str(obj.crew.pk) + "</span>"
  crew_id.allow_tags = True

  # return ticket status
  def tickets(self, obj):
    if (obj.name == ""):
      return ""
    return obj.tickets().replace('<br/>', ', ')
  tickets.allow_tags = True
  tickets.short_description = _('Tickets')

  # - functions ---------------------------------------------------
  def get_readonly_fields(self, request, obj=None):
    readonly = ['tickets', '_access', 'crew_id']
    if request.user.is_superuser or not obj:
      return readonly
    if obj.access_given or TicketAdmin.objects.filter(member=obj.pk).count() or \
      Advance.objects.filter(member=obj.pk).count() or Billing.objects.filter(member=obj.pk).count(): 
      readonly.append('crew')
    return readonly
  
  def response_add(self, request, obj):
    if "_addbill" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_member=%s#bill" % obj.pk)
    if "_addreceipt" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_member=%s#receipt" % obj.pk)
    return super(MemberAdmin, self).response_add(request, obj)

  def response_change(self, request, obj):
    if "_addbill" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_member=%s#bill" % obj.pk)
    if "_addreceipt" in request.POST:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_add',) + 
                                  "?limit_member=%s#receipt" % obj.pk)
    return super(MemberAdmin, self).response_change(request, obj)

  def has_add_bill_permission(self):
    perm = self._request_user.has_perm('crewdb.add_billing')
    return perm
  
  def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
    extra_context = extra_context or {}
    if (object_id):
      extra_context['billings'] = Member.objects.get(pk=object_id).billings
      extra_context['individual_billing'] = False
      try:
        extra_context['individual_billing'] = Member.objects.get(pk=object_id).crew.compensation.schema.get_individual_billing
      except:
        pass
    self._request_user = request.user
    extra_context['has_addbill_perm'] = self.has_add_bill_permission
    
    return super(MemberAdmin, self).changeform_view(request, object_id, form_url, extra_context)
  
  '''
  add links to crew in member list-view page
  https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/
  '''
  def crew_link(self, obj):
    url = reverse('admin:crewdb_crew_changelist')
    return u'<a href="{0}{1}">{2}</a>'.format(
        url, obj.crew.pk, obj.crew)
  crew_link.allow_tags = True
  crew_link.short_description = _('Crew')

  '''
  access control
  http://www.b-list.org/weblog/2008/dec/24/admin/
  '''
  def admin_req(self, request):
    return request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all())
  # allow crew_editor to move members onlybetween his crews
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "crew":
      # check if param was given to request
      limit_crew = request.GET.get('limit_crew')
      if limit_crew:
        # then limit crew dropdown to requested crew
        if not 'initial' in kwargs:
          kwargs['initial'] = {}
        kwargs['initial'].update({'crew': Crew.objects.filter(name=limit_crew)})
        kwargs["queryset"] = Crew.objects.filter(name=limit_crew)
      # limit crews to those maintained by request user
      elif not self.admin_req(request):
        kwargs["queryset"] = Crew.objects.filter(user=request.user).filter(Q(accountingdone=None)|Q(accountingdone__finalized=False))
      else:
        kwargs["queryset"] = Crew.objects.filter(Q(accountingdone=None)|Q(accountingdone__finalized=False))
    return super(MemberAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
  #prevent crew_editors to change non-owned crews
  def get_queryset(self, request):
    if self.admin_req(request):
        return Member.objects.all()
    return Member.objects.filter(crew__user=request.user)
  def has_change_permission(self, request, obj=None):
    has_class_permission = super(MemberAdmin, self).has_change_permission(request, obj)
    if not has_class_permission:
        return False
    if obj is not None and (not obj.crew.user or request.user.id != obj.crew.user.id) and not self.admin_req(request):
        return False
    return True

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- inline-view of extended User elements (contact form) --------------------------------------------------------
class UserExtrasInline(admin.StackedInline):
  class Media:
    css = { "all" : ("admin/css/hide_admin_original.css",) }
  model = UserExtras
  verbose_name = _("Contact")
  verbose_name_plural = _("Information")
  can_delete = False
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- Modified User-Admin Interface, some fields collapsed and inline included ------------------------------------
class MyUserAdmin(UserAdmin):
  inlines = (UserExtrasInline, )
  fieldsets = (
      (None, {'fields': ('username', 'password')}),
      (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
      (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                      'groups', 'user_permissions'), 'classes': ['collapse']}),
      (_('Important dates'), {'fields': ('last_login', 'date_joined'), 'classes': ['collapse']}),
  )
  add_fieldsets = (
      (None, {
          'classes': ('wide',),
          'fields': ('username', 'first_name', 'last_name', 'email', 'password1', 'password2'),
      }),
  )
  filter_horizontal = ('groups', 'user_permissions',)

  # - configurations for list-view --------------------------------
  list_display = ('username', 'first_name', 'last_name', 'email')
  list_filter = ('groups',)
  search_fields = ('username', 'first_name', 'last_name', 'email')
  ordering = ('username',)

  # - functions ---------------------------------------------------
  # only allow superuser to change some settings
  def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser:
        return []
    return ['is_active', 'is_staff', 'is_superuser', 'user_permissions', 'last_login', 'date_joined']

  '''
  prevent non-superusers to change superuser settings
  '''
  def get_queryset(self, request):
    if request.user.is_superuser:
        return User.objects.all()
    return User.objects.filter(is_superuser=False)
  def has_change_permission(self, request, obj=None):
    has_class_permission = super(MyUserAdmin, self).has_change_permission(request, obj)
    if not has_class_permission:
        return False
    if obj is not None and not request.user.is_superuser and obj.is_superuser:
        return False
    return True

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- Admin-Page for worktimes ------------------------------------------------------------------------------------
class WorkTimeAdmin(admin.ModelAdmin):
  class Media:
    css = { "all" : ("admin/css/calendar_events.css",) }
  model = WorkTime

  fieldsets = (
    (None, {'fields': (('member',),
                       ('date_from', 'date_to',),
                       ('comment',)), 'classes': ('wide', 'extrapretty'),}),
  )
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }

  # - configurations for list-view --------------------------------
  list_display = ['member', 'date_from', 'date_to']
  search_fields = ['member__name']
  list_filter = ('member__crew__name',)

  # - functions ---------------------------------------------------
  '''
  access control
  http://www.b-list.org/weblog/2008/dec/24/admin/
  '''
  def admin_req(self, request):
    return request.user.is_superuser or (Group.objects.get(name='crew_admin') in request.user.groups.all())
  # allow crew_editor to move members onlybetween his crews
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "member":
      # check if param was given to request
      limit_member = request.GET.get('limit_member')
      if limit_member:
        # then limit member dropdown to requested member
        if not 'initial' in kwargs:
          kwargs['initial'] = {}
        kwargs['initial'].update({'member': Member.objects.filter(pk=limit_member)})
        kwargs["queryset"] = Member.objects.filter(pk=limit_member)
      # limit crews to those maintained by request user
      elif not self.admin_req(request):
        kwargs["queryset"] = Member.objects.filter(crew__user=request.user, crew__compensation__schema__individual_billing=True)
      else:
        kwargs["queryset"] = Member.objects.filter(crew__compensation__schema__individual_billing=True)
    return super(WorkTimeAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
  #prevent crew_editors to change non-owned crews
  def get_queryset(self, request):
    if self.admin_req(request):
        return WorkTime.objects.all()
    return WorkTime.objects.filter(member__crew__user=request.user)
  def has_change_permission(self, request, obj=None):
    has_class_permission = super(WorkTimeAdmin, self).has_change_permission(request, obj)
    if not has_class_permission:
        return False
    if obj is not None and (not obj.member.crew.user or request.user.id != obj.member.crew.user.id) and not self.admin_req(request):
        return False
    return True
#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------------------
#- Billing-Admin Page ------------------------------------------------------------------------------------------
class BillingAdminForm(forms.ModelForm):
  class Meta:
    widgets = {
      'netto': EnclosedInput(append='€'),
      'brutto': EnclosedInput(append='€'),
      'recipient_local': AutosizedTextarea,
      'invoicing_party': AutosizedTextarea,
      'service_free': AutosizedTextarea(attrs={'class': 'input-xlarge'}),
      'comment': AutosizedTextarea(attrs={'class': 'input-xlarge'}),
    }
class BillingAdmin(admin.ModelAdmin):
  class Media:
    css = { "all" : ("admin/css/billingadmin.css",) }
  form = BillingAdminForm
  model = Billing
  radio_fields = {"vat_rate": admin.VERTICAL,}
  filter_horizontal = ('service',)

  actions = None

  # - django-suit additionals -------------------------------------
  suit_form_tabs = (('bill', _('Bill')), ('receipt', _('Receipt')))

  # - configurations for list-view --------------------------------
  list_display = ['date', 'receipt', 'bill_nr', 'member_link', 'crew_link', 'storno']
  search_fields = ['member_local', 'bill_nr']
  list_filter = ('member__crew__name', 'receipt', 'storno')

  ''' display sequential number '''
  def seq_nr(self, obj):
    return obj.pk
  seq_nr.short_description = _('Seq No')

  '''
  add links to crew in member list-view page
  https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/
  '''
  def crew_link(self, obj):
    url = reverse('admin:crewdb_crew_changelist')
    return u'<a href="{0}{1}/#billing">{2}</a>'.format(
        url, obj.member.crew.pk, obj.member.crew.name)
  crew_link.allow_tags = True
  crew_link.short_description = _('Crew')

  '''
  add links to crew in member list-view page
  https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/
  '''
  def member_link(self, obj):
    url = reverse('admin:crewdb_member_changelist')
    return u'<a href="{0}{1}/#billing">{2}</a>'.format(
        url, obj.member.pk, obj.member.name)
  member_link.allow_tags = True
  member_link.short_description = _('Member')


  # - functions ---------------------------------------------------
  # if new billing was saved always redirect to view
  def response_add(self, request, obj, post_url_continue="../%s/"):
    if obj.receipt:
      return HttpResponseRedirect(reverse('admin:crewdb_billing_changelist',) + str(obj.pk) +
                                  "?" + request.GET.urlencode())
    else:
      # if it's a bill give param 'print' to open a print dialog (by javascript)
      return HttpResponseRedirect(reverse('admin:crewdb_billing_changelist',) + str(obj.pk) +
                                  "?print=now&" + request.GET.urlencode())

  # if counterbalance-checkbox was selected, change repeated advance-object
  def save_related(self, request, form, formsets, change):
    for key in request.POST.dict().keys():
      key_parts = key.split('_')
      if key_parts[0] == 'counterbalanced':
        adv = Advance.objects.get(pk=key_parts[1])
        adv.counterbalanced = True
        adv.save()
      if key_parts[0] == 'storno':
        if len(key_parts) == 2:
          bill = Billing.objects.get(pk=key_parts[1])
          bill.storno = True
          bill.save()
    return super(BillingAdmin, self).save_related(request, form, formsets, change)

  # evaluate parameters given to request (like limit_member, limit_crew)
  def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if db_field.name == "member":
      # check if param was given to request
      limit_member = request.GET.get('limit_member')
      if limit_member:
        # then limit member dropdown to requested member
        if not 'initial' in kwargs:
          kwargs['initial'] = {}
        kwargs['initial'].update({'member': Member.objects.filter(pk=limit_member)})
        kwargs["queryset"] = Member.objects.filter(pk=limit_member)
      limit_crew = request.GET.get('limit_crew')
      if limit_crew:
        # then limit member dropdown to requested crew
        if not 'initial' in kwargs:
          kwargs['initial'] = {}
        kwargs['initial'].update({'member': Member.objects.filter(crew=limit_crew)})
        kwargs["queryset"] = Member.objects.filter(crew=limit_crew)
    return super(BillingAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

  # hide delete-action for common users
  def has_delete_permission(self, request, obj=None):
    if request.user.is_superuser:
      self.actions = []
    else:
      self.actions = None
    return request.user.is_superuser

  # limit standard view to not finalized crews
  def changelist_view(self, request, extra_context=None):
    if not request.META['QUERY_STRING'] and \
      not request.META.get('HTTP_REFERER', '').startswith(request.build_absolute_uri()):
      return HttpResponseRedirect(request.path + "?storno__exact=0")
    return super(BillingAdmin,self).changelist_view(request, extra_context=extra_context)

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

class EventTimesAdminForm(forms.ModelForm):
  class Meta:
    widgets = {
      'fee': EnclosedInput(append='€'),
    }
class EventTimesAdmin(admin.ModelAdmin):
  fieldsets = (
    (None, {'fields': (('date_from', 'date_to',),
                       ('description',),
                       ('fee',)), 'classes': ('wide', 'extrapretty'),}),
  )

  form = EventTimesAdminForm

  def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser:
      return []
    return ['description',]

  # hide delete-action for common users
  def has_delete_permission(self, request, obj=None):
    if request.user.is_superuser:
      self.actions = []
    else:
      self.actions = None
    return request.user.is_superuser


class ServiceAdmin(admin.ModelAdmin):
  class Media:
    css = { "all" : ("admin/css/serviceadmin.css",) }
  model = Service
  formfield_overrides = {
    models.TextField: {'widget': forms.Textarea(attrs={'rows': 3,'cols': 40})},
  }


# register modified main admin modelforms
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
admin.site.register(Crew, CrewAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Billing, BillingAdmin)

# register Settings forms for crewser-admin
admin.site.register(Ticket)
admin.site.register(CompensationSchema)
admin.site.register(EventTimes, EventTimesAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(VatRate)
admin.site.register(Company)
admin.site.register(AccountingDone)

# register all other forms, not required, only available for superuser
admin.site.register(Provision)       # access via crew-inline
admin.site.register(Access)          # access via crew-inline
admin.site.register(Compensation)    # access via crew-inline
admin.site.register(TicketAdmin)     # access via member-inline
admin.site.register(Advance)         # access via member-inline
admin.site.register(WorkTime, WorkTimeAdmin)  # access via member-inline

# access only for admin, not required, only available for superuser
admin.site.register(BillRecipient)



# ---- copy pasted from https://djangosnippets.org/snippets/3009/
# this will give the admin a complete log, makes sense after removing user logs


from django.contrib import admin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.html import escape
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.auth.models import User

action_names = {
    ADDITION: 'Addition',
    CHANGE:   'Change',
    DELETION: 'Deletion',
}

class FilterBase(admin.SimpleListFilter):
    def queryset(self, request, queryset):
        if self.value():
            dictionary = dict(((self.parameter_name, self.value()),))
            return queryset.filter(**dictionary)

class ActionFilter(FilterBase):
    title = 'action'
    parameter_name = 'action_flag'
    def lookups(self, request, model_admin):
        return action_names.items()


class UserFilter(FilterBase):
    """Use this filter to only show current users, who appear in the log."""
    title = 'user'
    parameter_name = 'user_id'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username)
            for u in User.objects.filter(pk__in =
                LogEntry.objects.values_list('user_id').distinct())
        )

class AdminFilter(UserFilter):
    """Use this filter to only show current Superusers."""
    title = 'admin'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username) for u in User.objects.filter(is_superuser=True))

class StaffFilter(UserFilter):
    """Use this filter to only show current Staff members."""
    title = 'staff'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username) for u in User.objects.filter(is_staff=True))


class LogEntryAdmin(admin.ModelAdmin):
    actions = None

    date_hierarchy = 'action_time'

    readonly_fields = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'action_description',
        'change_message',
    ]

    list_filter = [
        UserFilter,
        ActionFilter,
        'content_type',
        # 'user',
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]


    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'action_description',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        ct = obj.content_type
        repr_ = escape(obj.object_repr)
        try:
            href = reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id])
            link = u'<a href="%s">%s</a>' % (href, repr_)
        except NoReverseMatch:
            link = repr_
        return link if obj.action_flag != DELETION else repr_
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'

    def get_queryset(self, request):
        return super(LogEntryAdmin, self).get_queryset(request) \
            .prefetch_related('content_type')

    def action_description(self, obj):
        return action_names[obj.action_flag]
    action_description.short_description = 'Action'


admin.site.register(LogEntry, LogEntryAdmin)