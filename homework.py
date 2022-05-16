import logging
import os
import time
from asyncio import exceptions
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from settings import (ENDPOINT, HEADERS, HOMEWORK_STATUSES, RETRY_TIME,
                      TIME_DELTA)

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filemode='w',
    filename='main.log',
    format='%(lineno)s, %(asctime)s, %(levelname)s, %(message)s'
)


def send_message(bot, message):
    """Отправка сообщений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except exceptions.SendMessageFailure:
        logging.error('Бот не смог отправить сообщение')


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
    if homework_statuses.status_code != HTTPStatus.OK:
        status_code = homework_statuses.status_code
        logging.error(f'Ошибка {status_code}')
        raise telegram.TelegramError(f'Ошибка {status_code}')
    try:
        return homework_statuses.json()
    except ValueError:
        logging.error('Ошибка ответа json')
        raise ValueError('Ошибка ответа json')


def check_response(response):
    """Проверка доступности переменных окружения."""
    if type(response) != dict:
        raise TypeError('Тип response не соответствует словарю')
    if 'homeworks' not in response:
        logging.error('Ключ homeworks отсутствоет в response')
    try:
        homework = response.get('homeworks')
    except Exception as error:
        logging.error(error)
    if type(homework) != list:
        raise TypeError('Тип response не соответствует списку')
    if homework is None:
        logging.error('Словарь homework пустой')
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    homework_name = homework.get('homework_name')
    logging.info(homework_name)
    homework_status = homework.get('status')
    logging.info(homework_status)
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
    """Проверяем токены."""
    return all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if check_tokens() is True:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time() - TIME_DELTA)
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
    else:
        exit()


if __name__ == '__main__':
    main()
