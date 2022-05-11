import os
from telnetlib import STATUS
import requests
from dotenv import load_dotenv
import time

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
RETRY_TIME = 6

url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
#timestamp = 1647241610
current_timestamp = 147241610
payload = {'from_date': current_timestamp}
response = requests.get(url)
#time.sleep(RETRY_TIME)
homework_statuses = requests.get(url, headers=headers, params=payload)
homework_name = homework_statuses.json()['homeworks'][0]['status']
if homework_statuses.status_code == 200:
    print('OK!')
else:
    print('Boo!')
if homework_name in HOMEWORK_STATUSES:
    verdikt = HOMEWORK_STATUSES[homework_name]

print(type(homework_statuses))
