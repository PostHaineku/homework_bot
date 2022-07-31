from telegram import Bot
import requests
import os
from dotenv import load_dotenv
import time
import logging
from http import HTTPStatus
from exceptions import TokensException, HTTPStatusException

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='program.log',
    level=logging.DEBUG)


def send_message(bot, message):
    """отправляет сообщение в тг"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception('Сбой при отправке сообщения'):
        logging.error('Сбой при отправке сообщения')


def get_api_answer(current_timestamp):
    """получает ответ от апи"""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == HTTPStatus.NOT_FOUND:
        logging.error('Эндпоинт недоступен, пробуем подключиться')
        raise HTTPStatusException('Эндпоинт не отвечает')
    elif response.status_code != HTTPStatus.OK:
        logging.error('Эндпоинт недоступен')
        raise HTTPStatusException('Эндпоинт недоступен')
    else:
        return response.json()


def check_response(response):
    """проверяет тип данных и возвращает нашу домашнюю работу"""
    try:
        homework = response['homeworks']
        if not isinstance(homework, list):
            raise TypeError('Неверный формат homeworks')
        if 'homeworks' in response:
            homework = response['homeworks']
            return homework
        else:
            logging.error('Отсутствуют ожидаемые ключи')
            raise KeyError('Отсутствуют ожидаемые ключи')
    except response['homeworks'] is not list:
        raise TypeError('wtf')

# мне показалось, что ТЗ в этом спринте просто ужасно
# я вообще не понимаю все исключения, которые нужно отрабатывать
# можете, пожалуйста, дать мне какой-нибудь доп материал
# или что именно мне нужно повторить/посмотреть/почитать


def parse_status(homework):
    """Извлекает информацию о конкретной домашней работе"""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        logging.error('Ошибка статуса домашней работы')
        raise KeyError('Ошибка')


def check_tokens():
    """проверка наличия переменных среды"""
    # if 'PRACTICUM_TOKEN' and 'TELEGRAM_TOKEN'
    # and 'TELEGRAM_CHAT_ID' not in os.environ:
    #     logging.critical('Не хватает токенов в .env')
    #     return False
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False

# я искренне пытался сделать так, чтобы оно прошло тесты
# мой код работает,
# но как сделать по другому и чтобы прошло тесты - я без понятия


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is not True:
        logging.critical('Ошибка переменных окружения')
        raise TokensException('Ошибка переменных окружения')
    while True:
        try:
            current_timestamp = time.time()
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            send_message(bot, message)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            message_error = message
            if message_error != message:
                send_message(bot, message)
            message = f'Сбой в работе программы: {error}'
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
