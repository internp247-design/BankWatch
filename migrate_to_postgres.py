#!/usr/bin/env python
import os
import django
import json

# Setup Django with SQLite temporarily
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')

# Change to SQLite for export
from django.conf import settings
original_db = settings.DATABASES['default'].copy()
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(settings.BASE_DIR, 'db.sqlite3'),
}

django.setup()

# Export data from SQLite
from django.core.management import call_command
from io import StringIO

print("Exporting data from SQLite...")
output = StringIO()
try:
    call_command('dumpdata', 'auth', 'analyzer', 'users', stdout=output)
    data = output.getvalue()
    with open('backup.json', 'w') as f:
        f.write(data)
    print(f"✅ Data exported successfully! ({len(data)} bytes)")
except Exception as e:
    print(f"❌ Export error: {e}")
    exit(1)

# Restore PostgreSQL config
settings.DATABASES['default'] = original_db
from django.db import connections
connections.close_all()

print("\nLoading data into PostgreSQL...")
try:
    call_command('loaddata', 'backup.json')
    print("✅ Data loaded successfully into PostgreSQL!")
except Exception as e:
    print(f"❌ Load error: {e}")
    exit(1)

print("\n✅ Migration complete! Your data is now in PostgreSQL.")
