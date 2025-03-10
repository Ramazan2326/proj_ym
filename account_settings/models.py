from django.db import models


class Provider(models.Model):
    provider_name = models.CharField(max_length=255, blank=False, null=False)
    provider_logo = models.ImageField(upload_to='media/')

    class Meta:
        db_table = "providers"

    def __str__(self):
        return f'{self.provider_name}'
    
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     self.create_channels_from_settings()

    # def create_channels_from_settings(self):
    #     from messages_proccessing.models import Channel
    #     channels_data = self.get_available_channels()
    #     for channel in channels_data:
    #         Channel.objects.get_or_create(
    #             provider_id = self.provider_id,
    #             channel_name = channel.get("name"),
    #             defaults={"is_default": channel.get("is_default", False)}
    #         )
    

class AccountProvider(models.Model):
    from oauth_bru.models import Account
    from messages_proccessing.models import ProviderChannel
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='account_providers')  # Не даст удалить Account, так как на него ссылается AccountProvider
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, related_name='providers')
    last_datetime_sync_bru = models.DateTimeField(verbose_name='Дата последней синхронизации', auto_now=True)
    default_channel = models.ForeignKey(ProviderChannel, on_delete=models.SET_NULL, null=True)
    json_settings = models.JSONField()  # Подумать над аргументами

    class Meta:
        db_table = "accounts_providers"

    def __str__(self):
        return f'Интеграция {self.account.account} — {self.provider.provider_name}'
    
    def get_provider_token(self):
        return self.json_settings.get('Authorization', '')
    
    def get_available_channels(self):
        return self.json_settings.get('channels', [])
    
    def set_default_channel_id(self, channel_id):
        if channel_id in self.get_available_channels():
            self.default_channel = channel_id
            self.save()
        else:
            raise ValueError("Идентификатор канала не доступен для выбранного провайдера")
    
    def set_provider_token(self, token):
        if token in self.get_provider_token():
            self.provider_token = token
            self.save()
        else:
            raise ValueError("Выбранный провайдер не имеет токена")
