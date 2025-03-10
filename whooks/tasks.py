from celery import shared_task
from datetime import datetime
from whooks.models import BruWhook
from messages_proccessing.models import Message, Channel, Rule
from account_settings.models import AccountProvider
from sdk.sigmasms import get_token, send_sms, check_status
from core.logger import logger
from dotenv import load_dotenv

import requests, time, os, traceback

load_dotenv()


@shared_task
def consumer(data):
    time.sleep(10)
    SIGMA_LOGIN = os.getenv('SIGMA_LOGIN')
    SIGMA_PASSWORD = os.getenv('SIGMA_PASSWORD')

    try:
        account_provider = AccountProvider.objects.get(account_id__account='w626034')
        # rules = Rule.objects.filter(channel_id__provider_id=account_provider.provider_id)
        rules = Rule.objects.filter(provider_channel_id__provider_id=account_provider.provider_id)
        selected_rule = None
        for rule in rules:
            whook_msg = data.get("message")
            len_whook_msg = len(whook_msg)
            logger.info(f'Перебираем правило: {rule}, {rule.condition}, {rule.message_len}, {len_whook_msg}')
            if (
                (rule.condition == 'Строго меньше' and len_whook_msg < rule.message_len) or
                (rule.condition == 'Меньше или равно' and len_whook_msg <= rule.message_len) or
                (rule.condition == 'Равно' and len_whook_msg == rule.message_len) or
                (rule.condition == 'Больше или равно' and len_whook_msg >= rule.message_len) or
                (rule.condition == 'Строго больше' and len_whook_msg > rule.message_len) 
            ) and rule.keyword in whook_msg:
                selected_rule = rule
                break  # Взяли первое подходящее правило
        logger.info(f'Правило выбрано: {selected_rule}')
        if selected_rule:
            # channel = selected_rule.channel_id.channel_name if selected_rule.channel_id else None
            # channel = selected_rule.provider_channel.channel_id.channel_type if selected_rule.provider_channel.channel_id else None
            channel = selected_rule.provider_channel.channel.channel_type
            if channel:
                message = Message.objects.create(
                    content = whook_msg,
                    status = 'initial',
                    account_provider = account_provider,
                    provider_channel = selected_rule.provider_channel,
                    rule = selected_rule
                )
                logger.info(f'Сообщение создано: {message}')
            else:
                logger.info(f'Не создано сообщение')

        logger.info(f'Запуск задачи обработки хука: {data}')


        sigma_token = get_token(SIGMA_LOGIN, SIGMA_PASSWORD)
        recipient = '+79177895885'
        payload = dict(
            sender = 'B-Media',
            text = data.get('message')
        )
        message_id = send_sms(sigma_token, recipient, payload, type='sms')
        time.sleep(20)
        status = check_status(sigma_token, message_id)
        logger.info(f"От провайдера: {status}, запрос к message_id: {message_id}")

        BruWhook.objects.create(
            app_id = '626034',
            action=data.get("action"),
            employee_ref=data.get("responsible_employee_id"),
            whook_id=data.get("id"),
            phone=data.get("phone"),
            message=data.get("message"),
            date=modify_date(data),
            sms_id=data.get("sms_id"),
            sender=data.get("sender"),
            organization_id=data.get("organization_id"),
            partner_id=data.get("partner_id"),
            partner_employee_id=data.get("partner_employee_id"),
            responsible_employee_id=data.get("responsible_employee_id"),
            deal_id=data.get("deal_id"),
            status_id=data.get("status_id"),
            sms_cost=data.get("sms_cost"),
            social_type=data.get("social_type"),
        )
        logger.info(f'Записали вебхук в бд. Сейчас будем отправлять провайдеру.')
    
        # response = requests.post(
        #     'https://online.sigmasms.ru/api/sendings',
        #     headers = {
        #         'Content-Type': 'application/json',
        #         'Authorization': 'Bearer d4bb29cf8f4f2d501c0c77cbe29fb2c972b611e853b5b2ad6c8b2bb8fd1dc78f'
        #     },
        #     json = dict(
        #         recipient = '+79177895885',
        #         type = 'sms',
        #         payload = dict(
        #             sender = 'B-Media',
        #             text = data.get('message')
        #             )
        #         )
        #     )

        # logger.info(f'Вебхук {data} успешно обработан консьюмером: {status}')
        return {'status': 'success'}
    except Exception as error:
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'data': data,
        }
        logger.error(f'Ошибка обработки хука: {error_info}')
        return {'status': 'error', 'error_details': error_info}


@shared_task
def check_missing_whooks():
    try:
        logger.info("Проверка пропавших хуков")

        response = requests.get()
        whooks = response.json()

        for whook in whooks:
            consumer.delay(whook)

        logger.info(f"Найдено и обработано {len(whooks)} потерянных хуков")
    except Exception as error:
        logger.error(f"Ошибка при проверке потеряшек: {error}")


def modify_date(data):
    date_str = data.get("date")
    
    if not date_str:
        logger.warning("Поле 'date' отсутствует в данных")
        return None

    try:
        # Проверяем, содержит ли строка часовой пояс (например, "MSK")
        if " " in date_str and date_str.split()[-1].isalpha():  # Если последняя часть строки — буквенная (например, "MSK")
            # Удаляем аббревиатуру часового пояса
            date_str_without_tz = " ".join(date_str.split()[:-1])
            date_obj = datetime.strptime(date_str_without_tz, "%d.%m.%Y %H:%M:%S.%f")
        else:
            # Парсим строку без изменений
            date_obj = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S.%f")

        return date_obj

    except ValueError as e:
        logger.error(f"Неверный формат даты: {date_str}. Ошибка: {e}")
        return None