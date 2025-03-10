from django.db import models


class ProviderChannel(models.Model):
    from account_settings.models import Provider
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)

    class Meta:
        db_table = "providers_channels"

    def __str__(self):
        return f'{self.provider} — {self.channel}'


class Channel(models.Model):
    class ChannelType(models.TextChoices):
        whatsapp = 'WhatsApp'
        cascade = 'Cascade'
        viber = 'Viber'
        sms = 'SMS'
        vk = 'VK'
    channel_type = models.CharField(choices=ChannelType.choices, null=False, blank=False)

    class Meta:
        db_table = "channels"

    def __str__(self):
        return f'{self.channel_type}'


class Rule(models.Model):
    class Condition(models.TextChoices):
        lt = 'Строго меньше'
        lte = 'Меньше или равно'
        e = 'Равно'
        gte = 'Больше или равно'
        gt = 'Строго больше'
    account_provider = models.ForeignKey('account_settings.AccountProvider', on_delete=models.CASCADE, related_name='rules')
    provider_channel = models.ForeignKey(ProviderChannel, on_delete=models.SET_NULL, null=True, related_name='rules')
    rank = models.IntegerField(null=False)
    keyword = models.CharField(max_length=255)
    message_len = models.IntegerField(null=False)
    condition = models.CharField(choices=Condition.choices, null=False, blank=False)
    edited_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateField(auto_now=True)  # Подумать над auto_now 
    is_keyword_register_sensitive = models.BooleanField(default=False, null=False)


    class Meta:
        db_table = "rules"

    def __str__(self):
        return f'Правило с фразой: {self.keyword}'


class Message(models.Model):
    account_provider = models.ForeignKey('account_settings.AccountProvider', on_delete=models.CASCADE, related_name='messages')
    rule = models.ForeignKey(Rule, on_delete=models.SET_NULL, null=True)
    provider_channel = models.ForeignKey(ProviderChannel, on_delete=models.SET_NULL, null=True)
    content = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    received_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255)
    status_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "messages"

    def __str__(self):
        return f'Сообщение про: {self.content[:10]}...'
