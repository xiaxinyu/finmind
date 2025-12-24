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

class AppUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    display_name = models.CharField(max_length=128, null=True, blank=True)
    enabled = models.IntegerField(default=1)
    version = models.IntegerField(default=0)
    createUser = models.CharField(max_length=64, null=True, blank=True)
    createTime = models.DateTimeField(null=True, blank=True)
    updateUser = models.CharField(max_length=64, null=True, blank=True)
    updateTime = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "app_user"
        managed = False

class ConsumeCategory(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    parentId = models.CharField(max_length=64, null=True, blank=True)
    code = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=128)
    level = models.IntegerField(default=0)
    txn_types = models.CharField(max_length=256, default="expense")
    sortNo = models.IntegerField(default=0)
    deleted = models.IntegerField(default=0)
    version = models.IntegerField(default=0)
    createUser = models.CharField(max_length=64, null=True, blank=True)
    createTime = models.DateTimeField(null=True, blank=True)
    updateUser = models.CharField(max_length=64, null=True, blank=True)
    updateTime = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "consume_category"
        managed = False

class ConsumeRule(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    categoryId = models.CharField(max_length=64)
    pattern = models.CharField(max_length=256)
    patternType = models.CharField(max_length=32, default="contains")
    priority = models.IntegerField(default=100)
    active = models.IntegerField(default=1)
    bankCode = models.CharField(max_length=32, null=True, blank=True)
    cardTypeCode = models.CharField(max_length=32, null=True, blank=True)
    remark = models.CharField(max_length=256, null=True, blank=True)
    version = models.IntegerField(default=0)
    createUser = models.CharField(max_length=64, null=True, blank=True)
    createTime = models.DateTimeField(null=True, blank=True)
    updateUser = models.CharField(max_length=64, null=True, blank=True)
    updateTime = models.DateTimeField(null=True, blank=True)
    minAmount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    maxAmount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "consume_rule"
        managed = False

class ConsumeRuleTag(models.Model):
    rule_id = models.CharField(max_length=64)
    tag = models.CharField(max_length=255)
    class Meta:
        db_table = "consume_rule_tag"
        managed = False
