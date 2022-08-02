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
        logging.info('���������� ���������..')
    except Exception('���� ��� �������� ���������'):
        raise MessageNotSent('���� ��� �������� ���������')
    else:
        logging.info('��������� ������� ����������.')


def get_api_answer(current_timestamp):
    """�������� ����� �� ���."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    logging.info('����������� ������ � API')
    if response.status_code == HTTPStatus.NOT_FOUND:
        raise HTTPStatusException('�������� �� ��������')
    elif response.status_code != HTTPStatus.OK:
        raise HTTPStatusException('�������� ����������')
    return response.json()


def check_response(response):
    """��������� ��� ������ � ���������� ���� �������� ������."""
    if not isinstance(response, dict):
        raise TypeError('������������ ����� �� API')
    homework = response.get('homeworks')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('����������� ��������� �����')
    if not isinstance(homework, list):
        raise TypeError('�������� ������ homeworks')
    return homework


def parse_status(homework):
    """��������� ���������� � ���������� �������� ������."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('����������� ��������� �����')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('����������� ��������� �����')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'��������� ������ �������� ������ "{homework_name}". {verdict}'


def check_tokens():
    """�������� ���������� �����."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """�������� ������ ������ ����."""
    if not check_tokens():
        logging.critical('������ ���������� ���������')
        sys.exit('������ ���������� ���������')
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
            message = f'���� � ������ ���������: {error}'
            logging.error(message)
            message_error = message
            if message_error != message:
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)
# ��� ������� ������� ���� � ���� ��� �������� �� 53-56 �������
# ��� �� �� ������ ����..?


if __name__ == '__main__':
    main()
