from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from dotenv import load_dotenv
from functools import wraps
from core.logger import logger

import urllib.parse, os, requests, json, datetime

load_dotenv()


logger.info('Info')

def store_token(user_id, token):
    cache.set(f'token_cache:{user_id}', token, timeout=3600)  # Закешировали на час

def get_token(user_id):
    return cache.get(f'token_cache:{user_id}')

def store_refresh_token(user_id, refresh_token):
    cache.set(f'refresh_token_cache:{user_id}', refresh_token, timeout=86400)  # Кэшируем рефреш_токен на 1 день

def get_refresh_token(user_id):
    return cache.get(f'refresh_token_cache:{user_id}')


def oauth_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('access_token'):
            logger.error('Токен авторизации не найден в сессии.')
            return HttpResponse('Токен авторизации не найден в сессии.', status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def redirect_to_bru(request):
    CLIENT_ID = os.getenv('CLIENT_ID')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    STATE = os.getenv('STATE')
    logger.info(f'Перенаправление на страницу авторизации. CLIENT_ID={CLIENT_ID}\n REDIRECT_URI={REDIRECT_URI}')
    auth_url = (
        f"https://id.business.ru/authorize?"
        f"client_id={CLIENT_ID}&"
        f"display=page&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope=tus_create_api_app&"
        f"response_type=code&"
        f"state={STATE}"
    )
    return redirect(auth_url)


def callback_oauth(request):
    code = request.GET.get('code')
    account_url = f'https://yourmailings.giliazev.ru/class365/settings?account=w626034'

    if not code:
        logger.error('Параметр "code" отсутствует в запросе.')
        return HttpResponse('Невозможно провести авторизацию пользователя', status=400)
    
    logger.info(f'Получен код авторизации: {code}')
    token_url = 'https://id.business.ru/token'
    token_payload = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.getenv('REDIRECT_URI')
    }

    try:
        logger.info('Отправляем запрос для получения токена.')
        response = requests.post(token_url, data=token_payload)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')

        if not (access_token and refresh_token):
            logger.error('Не удалось получить access_token или refresh_token.')
            return HttpResponse('Не удалось получить токены', status=400)

        logger.info(f'Получен access_token: {access_token}, refresh_token: {refresh_token}')
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token

        account_url = f'https://yourmailings.giliazev.ru/class365/settings?account=w626034'
        return redirect(account_url)
    except requests.exceptions.RequestException as e:
        logger.error(f'Ошибка при получении токена: {e}')
        return HttpResponse('Ошибка получения токена', status=500)
    

@oauth_required
def get_appid_secret(request):
    from oauth_bru.models import Account
    if not request.session.get('access_token'):
        logger.error('Токен авторизации не найден в сессии.')
        return HttpResponse('Токен авторизации не найден', status=401)
    
    request_url = "https://w626034.business.ru/api/rest/create_app_with_oauth2.json"
    headers = {
        "Authorization": f"Bearer {request.session.get('access_token')}"
    }
    logger.info('TEST MESSAGE', extra={'test_field': 'test_value', 'timestamp': datetime.datetime.now().isoformat()})

    try:
        logger.info('Отправляем запрос для создания приложения.')
        response = requests.post(request_url, headers=headers)
        response.raise_for_status()

        response_data = response.json()
        app_id__value = response_data.get('app_id')
        secret__value = response_data.get('secret')
        store_token(app_id__value, request.session.get('access_token'))
        store_refresh_token(app_id__value, request.session.get('refresh_token'))
        if not (app_id__value and secret__value):
            logger.error('Ответ сервера не содержит app_id или secret.')
            return HttpResponse("Ответ сервера не содержит app_id или secret", status=400)

        logger.info(f'Получены данные приложения: app_id={app_id__value}, secret={secret__value}')
        account, created = Account.objects.update_or_create(
            account='w626034',
            defaults={
                'app_id': app_id__value,
                'secret': secret__value,
            }
        )
        if created:
            request.session.headers.pop('Authorization', None)
            logger.info(f'Аккаунт успешно создан: {account}')
            return HttpResponse(f"Аккаунт успешно создан: {account}", status=201)
        else:
            logger.info(f'Данные аккаунта {account.account} обновились')
            return HttpResponse(f'Данные аккаунта {account.account} обновились', status=200)
    except requests.exceptions.RequestException as e:
        logger.error(f'Ошибка при создании приложения: {e}')
        return HttpResponse('Ошибка создания приложения', status=500)
    

@oauth_required
def checksms(request):
    from oauth_bru.models import Account
    try:
        account = Account.objects.get(account='w626034')

        logger.info(f'Выполняем запрос к эндпоинту "sms" для аккаунта {account.account}')
        result = account.request_bru(method='GET', endpoint='sms')

        logger.info(f'Получен результат запроса: {result}')
        return JsonResponse(result)

    except Account.DoesNotExist:
        logger.error('Аккаунт не найден в базе данных.')
        return HttpResponse('Аккаунт не найден', status=404)

    except Exception as e:
        logger.error(f'Ошибка при выполнении запроса: {e}')
        return HttpResponse(f'Ошибка: {e}', status=500)


# @csrf_exempt
# def webhook_view(request):
#     logger.info(f'Триггер на вьюху сработал, метод {request.method}, заголовки {request.headers}')
#     if request.method == 'POST':
#         try:
#             post_data = request.POST.dict()
#             changes = {}
#             data = {}
#             try:
#                 if post_data.get('changes'):
#                     changes = json.loads(post_data['changes'])
#                 if post_data.get('data'):
#                     data = json.loads(post_data['data'])
#             except json.JSONDecodeError as e:
#                 logger.error(f"Ошибка при парсинге JSON: {e}")
#             extra_info = {
#                 'app_id': post_data.get('app_id'),
#                 'model': post_data.get('model'),
#                 'action': post_data.get('action'),
#                 'changes': changes,
#                 'data': data,
#             }
#             logger.info("Регистратор вебхуков от БРУ выполнил свою работу", extra=extra_info)
#             body = json.loads(request.body)
#             logger.info(f"Request JSON body: {body}")
#         except json.JSONDecodeError:
#             logger.info(f"Request raw body: {request.body.decode('utf-8', errors='ignore')}")
#         logger.info(f"Request POST parameters: {request.POST.dict()}")
#     try:
#         client = Account.objects.get(account='w626034')
#         if not client:
#             logger.error('Client configuration not found')
#             return JsonResponse({'status': 'error', 'message': 'Не найдено клиентской конфигурации'}, status=400)
        
#         params = {
#             'app_id__whook': 733909,
#         }

#         params.pop('app_psw', None)

#         expected_app_psw = client.generate_app_psw(params)

#         if request.POST.get('app_psw') != expected_app_psw:
#             logger.info(f"Некорректная подпись, Полученная подпись: {request.POST.get('app_psw')}, Ожидаемая подпись: {expected_app_psw}\nПри этом: app_id = {client.app_id}, secret = {client.secret}")
#             return JsonResponse({'status': 'error', 'message': 'Invalid app_psw'}, status=401)
        
#         logger.info('Упавший в систему хук распознан')
#         return JsonResponse({'status': 'success', 'message': 'Упавший в систему хук распознан'})
#     except Exception as e:
#         logger.exception('В процессе обработки хука возникла непредвиденная ошибка')
#         return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)







    # client = Account.objects.get(account='w626034')
    # if not client:
    #     logger.error('Client configuration not found')
    #     return JsonResponse({'status': 'error', 'message': 'Не найдено клиентской конфигурации'}, status=400)
    # if client.check_notification(request):
    #     try:
    #         data = json.loads(request.body)
    #         logger.info(f'Received webhook data: {data}')
    #     except json.JSONDecodeError:
    #         data = request.POST
    #         logger.info(f'Received webhook data: {data}')
    #     return JsonResponse({'status': 'success', 'message': 'Notification processed successfully'})
    # else:
    #     logger.error('Invalid notification')
    #     return JsonResponse({'status': 'error', 'message': 'Invalid notification'}, status=401)
    # else:
    #     logger.error('Invalid HTTP method')
    #     return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
