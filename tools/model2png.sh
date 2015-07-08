#!/bin/sh
# generates png image from db-schema

# aptitude install python-django-extensions pygraphviz
# ( Achtung: kein python3 )

python manage.py graph_models crewdb -g -o crewdb.png
