import asyncio
import logging
import sys
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime

from client import Client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

class Chat:
    def __init__(self):
        pass
           
    async def write_chat(self, writer: StreamWriter, filename: str, str_amount: int=20) -> None:
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()[-str_amount:]
                for line in lines:
                    if not line:
                        break
                    writer.write(line.encode())
                    await writer.drain()
        except FileNotFoundError:
            logger.error(f'Файл с общим чатом {filename} не найден.')

    async def print_into_chat(self, message, ip, filename: str):
        name = Client().get_name(ip)
        time = datetime.now()
        time = time.strftime('%H:%M %m-%d')
        format_message = f'{name}: {message}    {time}\n'
        with open(filename, 'a') as file:
            file.write(format_message)
