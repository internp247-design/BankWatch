import os
import sys
import django

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BankWatch.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

# Login with existing test user
client = Client()
client.login(username='totals_test', password='testpass')

# Get results page
response = client.get('/analyzer/rules/apply/results/?show_changed=1')
html = response.content.decode('utf-8')

# Find the totals section
import re
totals_match = re.search(r'Summary: Total Amount by Rule.*?</div>\s*</div>', html, re.DOTALL)
if totals_match:
    print("=== TOTALS SECTION FOUND ===")
    totals_html = totals_match.group(0)
    # Print first 500 chars
    print(totals_html[:800])
    print("\n=== LOOKING FOR RULE NAME ===")
    # Extract rule names from the totals section
    rule_names = re.findall(r'<p class="mb-1 text-muted small">(.*?)</p>', totals_html)
    print(f"Rule names found: {rule_names}")
else:
    print("Totals section not found")
    # Try to find what's actually in the page
    if 'Summary' in html:
        idx = html.find('Summary')
        print(f"Found 'Summary' at index {idx}")
        print(f"Context: {html[max(0,idx-100):idx+500]}")
