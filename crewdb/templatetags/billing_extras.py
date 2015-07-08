# -*- coding: utf-8 -*-
from django import template
from django.utils.translation import ugettext_lazy as _
import re
# import the logging library
import logging
# Get an instance of a logger, user with 'logger.debug(output)'
logger = logging.getLogger('crewdb.custom')

register = template.Library()

@register.filter
def format_money(value):
    if (value):
      return '%0.2f €' % (value)
    return ''

@register.filter
def calc_vat(brutto, netto):
    if (brutto and netto):
      return '%0.2f €' % (brutto - netto)
    return ''

@register.filter
def vat_rate_title(vat_rate):
    result_array = re.split('[\(\)]',vat_rate)
    if len(result_array) == 3:
      return result_array[1]
    return ""
