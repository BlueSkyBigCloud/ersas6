from prospects.models import Prospect
import string, random

def generate_unique_id():
    while True:
        cid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if not Prospect.objects.filter(company_id=cid).exists():
            return cid

for p in Prospect.objects.filter(company_id__isnull=True):
    p.company_id = generate_unique_id()
    p.save()