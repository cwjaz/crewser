# crewser

This is a django-project to maintain crews and members of an event and keep track of used tickets and budgets. You can find a test-installation at http://crewser.dance<br/>


You can use one of the following pre-configured accounts to access the system:<br/>
<ul>
  <li>username: admin<br/>password: crewseradmin<br/>role: admin == installer of the system</li>
  <li>username: test<br/>password: test<br/>role: event maintainer, organizes database editors and can change budget</li>
  <li>username: test2<br/>password: test2<br/>role: event editor, can add members and give them tickets</li>
</ul>
Be aware that the system database is resetted to it's predefined status every hour - if above passwords don't work, try it later.

## installation
you should use python above 3.4 and you can use a virtualenv to run crewser. These are the required python-packages:<br/>
<br/>
(env_3.4)rene@computer ~/crewser $ pip freeze<br/>
Django==1.7.7<br/>
autopep8==1.1<br/>
django-debug-panel==0.8.0<br/>
django-debug-toolbar==1.2.2<br/>
django-extensions==1.5.0<br/>
django-suit==0.2.12<br/>
pep8==1.6.1<br/>
pytz==2015.2<br/>
simplejson==3.6.5<br/>
six==1.9.0<br/>
sqlparse==0.1.14<br/>

After preparing the environment you can run crewser just by activating the virtualenv and starting the runserver with "./manage.py runserver". If you like, you can use wsgi to run crewser, wsgi might have to be compiled on your machine to work flawlessly with the selected python-version.
