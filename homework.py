import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filemode='w',
    filename='main.log',
    format='%(lineno)s, %(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """"Отправка сообщений"""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Получение api."""
    param = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=param)
        logging.info(type(homework_statuses.json()))
    except telegram.TelegramError as error:
        logging.error(f'Ошибка запроса к главному API {error}')
        raise telegram.TelegramError(
            f'Ошибка при запросе к основному API: {error}'
        )
    if homework_statuses.status_code != 200:
        status_code = homework_statuses.status_code
        logging.error(f'Ошибка {status_code}')
        raise telegram.TelegramError(f'Ошибка {status_code}')
    try:
        return homework_statuses.json()
    except ValueError:
        logging.error('Ошибка ответа json')
        raise ValueError('Ошибка ответа json')


def check_response(response):
    """"Проверка доступности переменных окружения"""
    if not response['homeworks']:
        logging.error(f'отсутствует ключ homeworks в ответе: {response}')
    homework = response.get('homeworks')
    logging.info(type(homework))
    if homework is None or not isinstance(homework, list):
        logging.error('Полученный ответ не соответствует ожидаемому')
        raise ValueError('В ответе нет списка homeworks')
    if not isinstance(homework, dict):
        logging.error(f'List {homework[0]} is empty')
    logging.info(homework)
    return homework


def parse_status(homework):
    """"Извлекает из информации о конкретной домашней работе статус."""
    homework_name = homework['homework_name']
    logging.info(homework['homework_name'])
    homework_status = homework['status']
    logging.info(homework_name)
    if not isinstance(homework, dict):
        message = ('Ошибка типа словаря')
        logging.error('Ошибка типа словаря')
        raise TypeError('В ответе нет списка homeworks')
    if homework_status not in HOMEWORK_STATUSES:
        message = f'Недокументированный статус: {homework_status}'
        raise KeyError(message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """"Проверяем токены"""
    if TELEGRAM_TOKEN or PRACTICUM_TOKEN or TELEGRAM_CHAT_ID is not None:
        return True
    else:
        logging.critical('Token error')
        return False


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 50 * 24 * 60 * 60)
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if len(response) != 0:
                homework = check_response(response)[0]
                message = parse_status(homework)
                send_message(bot, message)
                current_timestamp = response.get('current_date')
        except Exception as error:
            logging.error('Бот не смог отправить сообщение')
            message = f'Сбой в работе программы: {error}'
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
