"""
WSGI config for crewser project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crewser.settings")

# http://stackoverflow.com/questions/17165169/django-wsgi-python-encoding
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
