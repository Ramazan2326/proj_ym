from django.db import models
from django.http.request import HttpRequest
from urllib.parse import urlencode
from typing import Union, Optional, Dict, Any
from core.logger import logger
from oauth_bru.views import get_token, store_token

import requests, hashlib, logging


class Account(models.Model):
    account = models.CharField(max_length=255, blank=False, unique=True)
    app_id = models.IntegerField(null=False)
    secret = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "accounts"

    def __str__(self):
        return self.account
    
    @property
    def request_uri(self):
        return f'https://{self.account}.business.ru/api/rest/'
    
    def check_notification(self, request: HttpRequest) -> bool:
        logger.info(f"Содержимое POST-запроса: {request.POST}")
        logger.info(f"Из запроса: {request.POST.get('app_id')}, по факту: {self.app_id}")
        result = self._check_n(request, self.app_id, self.secret)
        logger.info(f"Результат проверки уведомлении: {result}")
        return result
    
    def _check_n(self, request: HttpRequest, app_id: int, secret: str) -> bool:
        logger.info(f"Зашли в check_n")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request body: {request.body}")
        params = {}
        if 'app_psw' not in request.POST:
            logger.error(f"В ПОСТЕ нет app_psw")
            return False
        if 'app_id' not in request.POST or request.POST['app_id'] != str(app_id):
            logger.error(f"В ПОСТЕ нет app_id / либо app_id не валиден")
            return False
        params['app_id'] = request.POST['app_id']
        logger.info(f"Добвален параметр app_id в заголовки запроса")
        if 'model' in request.POST:
            params['model'] = request.POST['model']
        if 'action' in request.POST:
            params['action'] = request.POST['action']
        if 'changes' in request.POST:
            params['changes'] = request.POST['changes']
        if 'data' in request.POST:
            params['data'] = request.POST['data']
        if hashlib.md5(f'{secret}{urlencode(params)}'.encode()).hexdigest() != request.POST['app_psw']:
            return False
        return True

    def send_notification_system(self, employees: Union[str, list], header: str, message: str, document_id: Optional[int] = None, model_name: Optional[str] = None, action: Optional[str] = None, seconds: int = 0) -> Dict[str, Any]:
        data = {
            'employee_ids': employees,
            'header': header,
            'message': message
        }
        if document_id:
            data['document_id'] = document_id
        if model_name:
            data['model_name'] = model_name
        if action:
            data['action'] = action
        if seconds:
            data['seconds'] = seconds
        logging.info('Уведомление успешно отправлено на обработку')
        return self.request('POST', 'notifications', data)

    def request_bru(self, method, endpoint, params=None, headers=None):
        if not params:
            params = {}
        if not headers:
            headers = {}

        self.repair_token()
        
        params['app_id'] = self.app_id
        params['app_psw'] = self.generate_app_psw(params)
        headers['Authorization'] = f'Bearer {get_token(self.app_id)}'
        print(headers['Authorization'])
        url = f'{self.request_uri}{endpoint}.json'

        logger.info(f'Выполняем запрос: {method} {url}, Параметры: {params}')

        try:
            response = requests.request(method, url, params=params, headers=headers)
            response.raise_for_status()
            logger.info(f'Получен ответ: {response.status_code}, {response.text}')
            if response.status_code == 401:
                logger.warning('Токен недействителен. Попытка восстановления.')
                if self.repair_token():
                    logger.info('Токен успешно восстановлен. Повторяем запрос.')
                    return self.request_bru(method, endpoint, params)
                else:
                    logger.error('Не удалось восстановить токен.')
                    raise ValueError('Не удалось восстановить токен')
            
            response_data = response.json()
            logger.info(f'Проверка ответа сервера.')
            result = self.verify_response(response_data)
            logger.info(f'Запрос выполнен успешно. Результат: {result}')
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f'Ошибка при работе с API: {e}')
            raise

    
    def generate_app_psw(self, params: dict, is_repair=False):
        logger.debug(f'Генерация app_psw. Параметры: {params}')

        sorted_params = sorted(params.items())
        params_str = urlencode(sorted_params)

        logger.debug(f'Отсортированные параметры: {sorted_params}')
        logger.debug(f'URL-кодированная строка параметров: {params_str}')

        if is_repair:
            concatenated_string = self.secret + params_str
        else:
            concatenated_string = get_token(self.app_id) + self.secret + params_str
        
        app_psw = hashlib.md5(concatenated_string.encode('utf-8')).hexdigest()

        logger.debug(f'Токен: {get_token(self.app_id)}')
        logger.debug(f'Секретный ключ: {self.secret[:5]}...')
        logger.debug(f'Сгенерирован app_psw: {app_psw}')

        return app_psw
    

    def repair_token(self):
        """
        Восстанавливает токен через запрос repair.
        """
        params = {'app_id': self.app_id}
        params['app_psw'] = self.generate_app_psw(params, is_repair=True)

        url = f'{self.request_uri}repair.json'

        logger.warning('Попытка восстановления токена.')

        try:
            logger.info(f'Отправляем запрос repair: {url}, Параметры: {params}')
            response = requests.get(url, params=params)
            logger.info(f'Получен ответ: {response.status_code}, {response.text}')
            response.raise_for_status()

            response_data = response.json()
            logger.info(f'JSON-ответ: {response_data}')
            # Проверяем наличие token и app_psw в ответе
            if 'token' not in response_data or 'app_psw' not in response_data:
                logger.error('Ответ не содержит полей "token" или "app_psw".')
                raise ValueError('Ответ не содержит полей "token" или "app_psw"')

            # Проверяем подпись (без учета токена)
            # data_copy = response_data.copy()
            # del data_copy['app_psw']
            # result_json = json.dumps(data_copy, separators=(',', ':'))
            # expected_app_psw = hashlib.md5((self.secret + result_json).encode()).hexdigest()
            # logger.debug(f'Ожидаемая подпись: {expected_app_psw}, Полученная подпись: {response_data["app_psw"]}')
            # if expected_app_psw != response_data['app_psw']:
            #     logger.error('Неверная подпись ответа (app_psw).')
            #     raise ValueError('Неверная подпись ответа (app_psw) при восстановлении токена')

            # Обновляем токен
            store_token(self.app_id, response_data['token'])
            self.save()
            logger.info(f'Токен успешно восстановлен. Новый токен: {get_token(self.app_id)}')
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f'Ошибка восстановления токена: {e}')
            return False

    def verify_response(self, response_data):
        if 'token' not in response_data or 'app_psw' not in response_data:
            raise ValueError('Ответ не содержит полей "app_psw" или "token"')
        data_copy = response_data.copy()
        del data_copy['app_psw']

        # result_json = json.dumps(data_copy, separators=(',', ';'))
        # expected_app_psw = hashlib.md5((self.token + self.secret + result_json).encode()).hexdigest()
        # if expected_app_psw != response_data['app_psw']:
        #     raise ValueError('Неверная подпись ответа (app_psw)')

        store_token(self.app_id, response_data['token'])
        self.save()

        del data_copy['token']
        return data_copy
