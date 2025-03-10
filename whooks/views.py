from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from whooks.tasks import consumer
from core.logger import logger

import json


"""
Применяю декоратор для отключения защиты 
«Cross Site Request Forgery», поскольку доверяю БРУ
(то бишь от межсетевой подделки запросов). Без 
декоратора фреймворк отклоняет запросы по этому урлу
с ошибкой 403
"""
@csrf_exempt
def webhook_view(request):
    if request.method == 'POST':
        post_data = request.POST.dict()

        try:
            data = json.loads(post_data.get('data', '{}'))
            changes = json.loads(post_data.get('changes', '{}'))['0']  # Здесь надо подумать над нулем
            data = {**changes, **data}  # Поля changes, которых нет в data, добавляю в data
            logger.info(f"Распарсенные данные: {data}\nРаспарсенные изменения: {changes}")

            consumer.delay(data)  # ТУТ Я ПЕРЕДАЮ ХУК В КОНСЬЮМЕР СЕЛЕРИ

            extra_info = {
                'app_id': post_data.get('app_id'),
                'model': post_data.get('model'),
                'action': post_data.get('action'),
                'changes': changes,
                'data': data,
            }
            
            # logger.info("Регистратор вебхуков от БРУ выполнил свою работу", extra=extra_info)
            return JsonResponse({"status": "success"})
        except json.JSONDecodeError as error:
            logger.error(f'Ошибка парсинга JSON: {error}')
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
