from django.db import models


class BruWhook(models.Model):
    app_id = models.IntegerField(null=False)
    action = models.CharField(max_length=255, null=False)

    employee_ref = models.CharField(max_length=255, null=True, blank=True)
    whook_id = models.IntegerField(null=False)
    phone = models.CharField(max_length=255, null=True, blank=True)
    message = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    sms_id = models.CharField(max_length=255, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    organization_id = models.IntegerField(null=True, blank=True)
    partner_id = models.CharField(max_length=255, null=True, blank=True)
    partner_employee_id = models.CharField(max_length=255, null=True, blank=True)
    responsible_employee_id = models.CharField(max_length=255, null=True, blank=True)
    deal_id = models.CharField(max_length=255, null=True, blank=True)
    status_id = models.CharField(max_length=255, null=True, blank=True)
    sms_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    social_type = models.CharField(max_length=255, null=True, blank=True)

    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        db_table = "bru_whooks"

    def __str__(self):
        return f'{self.model} — {self.action}'
