import os
import django
import sys
from datetime import datetime

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finmind_site.settings')
django.setup()

from persist.models import ConsumeCategory

def fix_categories():
    categories_to_create = [
        {'id': 'A10001', 'name': '餐饮消费', 'txn_types': 'expense'}, # Dining
        {'id': 'B10001', 'name': '交通出行', 'txn_types': 'expense'}, # Transport
        {'id': 'C10001', 'name': '购物消费', 'txn_types': 'expense'}, # Shopping
        {'id': 'D10001', 'name': '数码电器', 'txn_types': 'expense'}, # Digital/Electronics
        {'id': 'J10001', 'name': '报销补助', 'txn_types': 'income'},  # Reimbursement
    ]

    for cat_data in categories_to_create:
        cat_id = cat_data['id']
        if not ConsumeCategory.objects.filter(id=cat_id).exists():
            print(f"Creating category: {cat_id} - {cat_data['name']}")
            ConsumeCategory.objects.create(
                id=cat_id,
                name=cat_data['name'],
                parentId=None,
                code=cat_id, # Usually code matches ID or similar
                level=1,
                txn_types=cat_data['txn_types'],
                sortNo=100,
                deleted=0,
                version=0,
                createTime=datetime.now(),
                updateTime=datetime.now()
            )
        else:
            print(f"Category {cat_id} already exists.")

if __name__ == '__main__':
    fix_categories()
