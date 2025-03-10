from core.logger import logger

import requests
import datetime

BASE_URI = 'https://online.sigmasms.ru/api'

def get_token(login, pwd):
    try:
        response = requests.post(
            f'{BASE_URI}/login',
            json = dict(
                username = login,
                password = pwd
            )
        )

        if response and response.status_code == 200:
            return response.json().get('token')

    except Exception as e:
        raise e

def send_sms(token, recipient, payload, type):
    '''
    отправка одного сообщения
    :param token: токен авторизации
    :return: id сообщения
    '''
    try:
        response = requests.post(
            f'{BASE_URI}/sendings',
             headers = dict(Authorization = token),
             json = dict(
                 recipient = recipient,
                 type = type,
                 payload = payload)
        )

        if response and response.status_code == 200:
            return response.json().get('id')
        return response.json().get('id')

    except Exception as e:
        raise e

def check_status(token, message_id):
    '''
    проверка статуса сообщения
    :param token: токен авторизации
    :param message_id: id отправленного сообщения
    :return: статус отправки сообщения
    '''
    response = requests.get(
        f'{BASE_URI}/sendings/{message_id}',
        headers = dict(Authorization = token)
    )

    if response and response.status_code == 200:
        data = response.json()
        logger.info(f"Response data: {data}")
        return response.json().get('state', {}).get('status')
