import json
import logging
import os
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

class Client:
    def __init__(self):
        pass
            
    def get_name(self, ip: str) -> str:
        clients = self.get_clients()
        try:
            name = clients[ip]
            return name
        except KeyError:
            logger.error(f'IP {ip} не зарегестрирован.')
        
    def get_clients(self, file_name: str ='clients.json') -> dict:
        try:
            with open(file_name, 'r') as file:
                clients = json.load(file)
                return clients
        except FileNotFoundError:
            logger.error(f'Файл с клиентами {file_name} не найден.')

    async def add_client(self, ip: str, name: str) -> None:
            clients = self.get_clients()
            clients[ip] = name
            with open('clients.json', 'w') as f:
                json.dump(clients, f, indent=4)
            logger.debug(f'Добавлен новый пользователь - ({ip} : {name}).')
            client_folder = f'messages/personal_messages/{ip}'
            if not os.path.exists(client_folder):
                os.makedirs(client_folder)