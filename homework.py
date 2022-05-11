import logging
import os
from telegram import Bot
from telegram.ext import Updater, Filters, MessageHandler
import time
import telegram

from dotenv import load_dotenv
import requests

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
current_timestamp = 147241610

logging.basicConfig(
    level=logging.DEBUG,
    filemode='w',
    filename='main.log',
    format='%(lineno)s, %(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


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
        logging.info(type(homework_statuses.json()))
        return homework_statuses.json()
    except ValueError:
        logging.error('Ошибка ответа json')
        raise ValueError('Ошибка ответа json')


def check_response(response):
    if not response['homeworks']:
        error = f'отсутствует ключ homeworks в ответе: {response}'
    homework = response.get('homeworks')
    #homework = homework.json()
    logging.info(type(homework))
    if homework is None or not isinstance(homework, list):
        logging.error('Полученный ответ не соответствует ожидаемому')
        raise ValueError('В ответе нет списка homeworks')
    logging.info('Status of homework update')
    if not isinstance(homework, dict):
        error = f'List {homework[0]} is empty'
    logging.info(homework)
    return homework


def parse_status(homework):
    homework_name = homework['homework_name']
    logging.info(homework['homework_name'])
    homework_status = homework['status']
    logging.info(homework_name)
    if not isinstance(homework, dict):
       message = 'Ошибка типа словаря'
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
        return False


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    #current_timestamp = 147241610
    current_timestamp = int(time.time() - 50 * 24 * 60 * 60)
    check_tokens()
    status = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.info(type(response))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            time.sleep(RETRY_TIME)
        try:
            if check_response(response):
                homework = check_response(response)
                message = parse_status(homework)
                print('work well')
                if message != status:
                    send_message(bot, message)
                    status = message
        #except Exception as error:
        #    message = f'Сбой в работе программы2: {error}'
        #    if message != status:
        #        send_message(bot, message)
        #        status = message
        #        print(status)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
