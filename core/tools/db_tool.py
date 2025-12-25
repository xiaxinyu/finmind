from persist.models import Transaction

def get_transaction_by_id(txn_id):
    return Transaction.objects.filter(id=txn_id).first()
