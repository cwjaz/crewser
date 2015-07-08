#!/bin/sh
if [ -f crewdb/migrations/0003* ]; then
	echo "there are some new migration files in crewdb/migrations/"
	echo "originally there are only two migration files expected there"
	echo "0001_initial.py  0002_fill_initial_data.py"
	echo "all others might cause some trouble - or not .)"
	echo
	echo "better do this by hand!"
	exit 1
fi

mv db.sqlite3 db.sqlite3_bak 2>/dev/null
./manage.py migrate crewdb 0001
./manage.py migrate
./manage.py createsuperuser
if [ -f tools/testdata.sql ]; then
	echo "adding initial testdata"
	cat tools/testdata.sql | sqlite3 db.sqlite3
	echo "done"
fi
