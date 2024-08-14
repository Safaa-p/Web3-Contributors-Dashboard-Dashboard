from django.db import models

class Treasury_guild(models.Model):
    id = models.AutoField(primary_key=True)
    completed_at = models.DateTimeField()
    wallet_owner = models.CharField(max_length=255)
    group = models.CharField(max_length=255)
    task_labels = models.CharField(max_length=255)
    task_name = models.CharField(max_length=255)
    rewarded = models.BooleanField(default=False)
    ada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mins = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    agix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet_address = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=255)
    subgroup = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'Treasury Guild Data'

    def __str__(self):
        return self.wallet_owner
