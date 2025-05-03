import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_system.settings')
django.setup()

# Now run the add_sample_data.py script with UTF-8 encoding
exec(open('add_sample_data.py', encoding='utf-8').read())
