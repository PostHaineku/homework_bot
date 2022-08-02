# -*- coding: cp1251 -*-
import logging
import sys
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import HTTPStatusException, MessageNotSent

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': '������ ���������: �������� �� �����������. ���!',
    'reviewing': '������ ����� �� �������� ���������.',
    'rejected': '������ ���������: � �������� ���� ���������.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='program.log',
    level=logging.DEBUG)


def send_message(bot, message):
    """���������� ��������� � ��."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Sending message..')
    except Exception('Failed to send message'):
        raise MessageNotSent('Failed to send message')
    else:
        logging.info('Message sent successfully.')


def get_api_answer(current_timestamp):
    """�������� ����� �� ���."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    logging.info('Requesting API access')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPStatusException('Endpoint is not avalible')
    elif response.status_code != HTTPStatus.OK:
        raise HTTPStatusException('Endpoint not responding')
    return response.json()
# � �����, ���������� ���� � ������ timestamp=0
# � ������� �������� �������� ���������� �� 56 �������
# �� ������ ��� 54 ������� �� �����, �� ��� ��� �� �������� �������


def check_response(response):
    """��������� ��� ������ � ���������� ���� �������� ������."""
    if not isinstance(response, dict):
        raise TypeError('Incorrect API response')
    homework = response.get('homeworks')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('Missing expected keys')
    if not isinstance(homework, list):
        raise TypeError('Invalid homeworks format')
    return homework


def parse_status(homework):
    """��������� ���������� � ���������� �������� ������."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('Missing expected keys')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Missing expected keys')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Homework verification status changed "{homework_name}". {verdict}'


def check_tokens():
    """�������� ���������� �����."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """�������� ������ ������ ����."""
    if not check_tokens():
        logging.critical('Environment variables error')
        sys.exit('Environment variables error')
    bot = Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            current_timestamp = time.time()
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            send_message(bot, message)
            current_timestamp = response.get('current_date')

        except Exception as error:
            message = f'Program crash: {error}'
            logging.error(message)
            message_error = message
            if message_error != message:
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
