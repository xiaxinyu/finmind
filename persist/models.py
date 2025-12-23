from django.db import models

class Credit(models.Model):
    source = models.CharField(max_length=64)
    transaction_date = models.DateTimeField()
    bookkeeping_date = models.DateTimeField()
    card_id = models.CharField(max_length=64)
    transaction_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_currency = models.CharField(max_length=16)
    balance_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_desc = models.TextField()
    payment_type_id = models.CharField(max_length=32)
    payment_type_name = models.CharField(max_length=64)
    card_type_id = models.IntegerField(default=1)
    card_type_name = models.CharField(max_length=64, default="Credit Card")
    deleted = models.IntegerField(default=0)
    consumption_name = models.CharField(max_length=64)
    consumption_id = models.IntegerField()
    consume_name = models.CharField(max_length=64)
    consume_id = models.CharField(max_length=64)
    keyword = models.CharField(max_length=128)
    demoarea = models.CharField(max_length=128)
    recordid = models.CharField(max_length=64, default="no record id")
    version = models.IntegerField(default=0)
    createuser = models.CharField(max_length=64, default="system")
    createtime = models.DateTimeField(auto_now_add=True)
    updateuser = models.CharField(max_length=64, default="system")
    updatetime = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CREDIT"

