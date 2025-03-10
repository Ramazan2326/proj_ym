# from urllib.parse import urlencode

# import requests, hashlib

# class BusinessRuService:
#     def __init__(self, account: str, app_id: int, secret: str):
#         """
#         Инициализация клиента сервиса БизнесРу
#         :account: название аккаунта
#         :app_id: идентификатор интеграции
#         :secret: секретный ключ интеграции
#         :request_uri: адрес, к которому делаются запросы
#         """
#         self.account = account
#         self.app_id = app_id
#         self.secret = secret
#         self.request_uri = 'https://{self.account}.business.ru/api/rest'
    
#     def __generate_password(self, params: dict, is_repair=False):
#         sorted_params = sorted(params.items())
#         params_string = urlencode(sorted_params)

#         concatenated_string = self.secret + params_string if is_repair == True else get_token(self.app_id) + self.secret + params_string

#         app_psw = hashlib.md5(concatenated_string.encode('utf-8')).hexdigest()

#         return app_psw



#     def sendRequest(self, method: str, model: str, params: list = []):
#         method = method.upper()
#         params.append(self.app_id)
#         sorted_params = dict(sorted(params.items))  # Сортирует массив заголовков по ключам (не значения)
#         if method == 'GET':
#             request = requests.get()
#         elif method == 'POST':
#             request = requests.post()
#         elif method == 'PUT':
#             request = requests.put()
#         elif method == 'PATCH':
#             request = requests.patch()
#         elif method == 'DELETE':
#             request = requests.delete()
#         else:
#             raise "Неверный HTTP-метод!"
    
#     def __request(self, method: str, model: str, params: list = []):
#         """
#         Позволяет выполнить запрос к API БизнесРу

#         :param method: метод запроса.
#         :param model: модель, к которой делается запрос.
#         :param params: список параметров, передаваемых в запросе.
#         """
#         result = ...


#     def __request_all(self, model: str, params: list = []):
#         """
#         Выполняет запрос всех записей конкретной модели

#         :param model: модель, записи который надо вывести.
#         :param params: список параметров, передаваемые в запросе.
#         :return: 
#         """
#         method = 'GET'

#         if (params['limit'] is None):
#             # max_limit = ...
#             pass

#         if (max_limit > 250):
#             pass

