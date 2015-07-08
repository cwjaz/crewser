from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from crewdb.models import Member, Company, WorkTime, EventTimes, Crew, Billing, Advance
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
import simplejson

# import the logging library
import logging
# Get an instance of a logger, user with 'logger.debug(output)'
logger = logging.getLogger('crewdb.custom')

'''
ajax: return all relevant member fields
'''
@login_required
def member_data(request):
  member_id = None
  if request.method == 'GET':
    member_id = request.GET['member_id']

  if member_id:
    member = Member.objects.get(id=int(member_id))
    obj = {}
    for key in member.__dict__:
      if not key.startswith('_'):
        obj[key] = member.__dict__[key]
    try:
      individual_billing = Member.objects.get(id=int(member_id)).crew.compensation.schema.individual_billing
    except:
      individual_billing = False
    if (individual_billing):
      result = []
      for worktimes in WorkTime.objects.filter(member=int(member_id)):
        result.append(worktimes.days_fee())
      obj['worktimes'] = result
    result = []
    for bills in Billing.objects.filter(member=int(member_id), receipt = False, storno = False):
      bill_obj = {}
      bill_obj['id'] = bills.pk
      bill_obj['message'] = (_('Bill found from %s (bill-date %s):') % (bills.date_internal, bills.date))
      bill_obj['amount'] = ('Netto %0.2f€ / Brutto %0.2f€' % (bills.netto, bills.brutto))
      result.append(bill_obj)
    if result:
      obj['bills'] = result

    # search for all advances paid to member
    result = []
    for advance in Advance.objects.filter(member=int(member_id), crew_advance=False, counterbalanced=False):
      advance_obj = {}
      advance_obj['id'] = advance.pk
      advance_obj['message'] = (_('Advance found from %s:') % (advance.date))
      advance_obj['amount'] = ('%0.2f€' % (advance.amount))
      if advance.comment:
        advance_obj['comment'] = ('(%s)' % (advance.comment))
      result.append(advance_obj)
    if result:
      obj['advance'] = result

    # search for all crew-advances paid to any member of the crew of this member
    result = []
    for advance in Advance.objects.filter(member__crew=Member.objects.get(pk=int(member_id)).crew, crew_advance=True, counterbalanced=False):
      advance_obj = {}
      advance_obj['id'] = advance.pk
      advance_obj['message'] = (_('Crew-Advance found, Member %s, %s:') % (advance.member.name, advance.date))
      advance_obj['amount'] = ('%0.2f€' % (advance.amount))
      if advance.comment:
        advance_obj['comment'] = ('(%s)' % (advance.comment))
      result.append(advance_obj)
    if result:
      obj['crew_advance'] = result
    return HttpResponse(simplejson.dumps(obj), content_type='application/json')

  return HttpResponse(member_id)

'''
ajax: return company information
'''
@login_required
def company_data(request):
  company_id = None
  if request.method == 'GET':
    company_id = request.GET['company_id']

  if company_id:
    company = Company.objects.get(id=int(company_id))
    logger.debug(company.address)
    obj = {}
    for key in company.__dict__:
      if not key.startswith('_'):
        obj[key] = company.__dict__[key]
    return HttpResponse(simplejson.dumps(obj), content_type='application/json')

  return HttpResponse(company_id)

'''
ajax: return event-data to render calendar
'''
@login_required
def event_data(request):
  if request.method == 'GET':
    event_times = EventTimes.objects.all()
    returnList = []
    for event in event_times:
      obj = {}
      for key in event.__dict__:
        if not key.startswith('_'):
          obj[key] = event.__dict__[key]
      obj['date_from'] = str(obj['date_from'])
      obj['date_to'] = str(obj['date_to'])
      returnList.append(obj)
    return HttpResponse(simplejson.dumps(returnList), content_type='application/json')

  return HttpResponse()

'''
ajax: return crew information
'''
@login_required
def crew_data(request):
  crew_id = None
  if request.method == 'GET':
    crew_id = request.GET['crew_id']

  if crew_id:
    obj = {}
    obj['individual_billing'] = False
    try:
      obj['individual_billing'] = Crew.objects.get(id=int(crew_id)).compensation.schema.individual_billing
    except:
      pass
    obj['finalized'] = False
    try:
      obj['finalized'] = Crew.objects.get(id=int(crew_id)).accountingdone.finalized
    except:
      pass
    obj['tickets'] = False
    try:
      obj['tickets'] = Crew.objects.get(id=int(crew_id)).tickets()
    except:
      pass
    return HttpResponse(simplejson.dumps(obj), content_type='application/json')
  return HttpResponse(crew_id)
