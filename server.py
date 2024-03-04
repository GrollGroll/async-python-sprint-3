import asyncio
import logging
import os
import sys
from asyncio.streams import StreamReader, StreamWriter

from chat import Chat
from client import Client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))

class Server:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port

    async def listen(self, reader: StreamReader) -> str:
        massage = b''
        break_symbol = '\n'
        while True:
            letter = await reader.read(1)
            if letter == break_symbol.encode():
                massage = massage.decode('utf-8').strip()
                logger.info(f'Принято сообщение: {massage}.')
                return massage
            
            massage += letter

    async def client_authorization(self, reader: StreamReader, writer: StreamWriter):
        address = writer.get_extra_info('peername')
        ip = address[0]
        logger.info(f'IP клиента: {ip}.')
        name = Client().get_name(ip)

        # Если такой IP уже зарегестрирован:
        if name:
            greetings = f'Hello, {name}!\n'
            writer.write(greetings.encode())
            return ip
             
        # Если новый пользователь или вход с нового устройства:
        else:
            clients = Client().get_clients()
            writer.write(b'1 - login; \n 2 - registration \n')
            await writer.drain()
            message = await self.listen(reader)
            if message == '1':
                writer.write(b'Your login: ')
                await writer.drain()
                name = await self.listen(reader)
                greetings = f'Hello, {name}! You login from new device!\n'
                writer.write(greetings.encode())
                await writer.drain()
                for ip in clients:
                    if name == clients[ip]:
                        return ip
            elif message == '2':
                while True:
                    writer.write(b'Your new login: ')
                    await writer.drain()
                    name = await self.listen(reader)
                    if name not in clients.values():
                        logger.debug(f'Принят новый login {name} на регистрацию с ip {ip}.')
                        await Client().add_client(ip=ip, name=name)
                        greetings = f'Hello, {name}! You have successfully registered! \n'
                        writer.write(greetings.encode())
                        await writer.drain()
                        return ip
                    else:
                        writer.write(b'A user with this login already exists!\n')
                        await writer.drain()

    async def show_menu(self, writer: StreamWriter):
        menu = b"1 - general chat; \n 2 - personal chats; \n 3 - new chat"
        writer.write(menu)
        await writer.drain()

    async def client_connected(self, reader: StreamReader, writer: StreamWriter):
        logger.info('Сервер запустился.')
        ip = await self.client_authorization(reader, writer)
        await self.show_menu(writer)
        while True:
            filename = None
            # Определяем какой чат открыть (общий или персональный) или создать:
            while not filename:
                message = await self.listen(reader)

                # Подключение к общему чату:
                if message == '1':
                    filename = 'messages/general_chat.txt'

                # Вывод списка персональных чатов:
                elif message == '2':
                    client_folder = f'messages/personal_messages/{ip}'
                    clients = Client().get_clients()
                    client_chats = os.listdir(client_folder)
                    if client_chats:
                        clients_list= []

                        for client_chat in client_chats:
                            addressee_ip = str(client_chat)[0:-4]
                            per_chat = f'{clients[addressee_ip]}\n'
                            writer.write(per_chat.encode())
                            clients_list.append(per_chat.strip())
                        # Подключение к персональному чату:
                        message = await self.listen(reader)
                        if message in clients_list:
                            for client_ip, name in clients.items():
                                if name == message:
                                    filename = f'{client_folder}/{client_ip}.txt'
                                    break
                        elif message == '/exit':
                            await self.show_menu(writer)
                        else:
                            warning = b'Please, choose the addressee from the list!\n'
                            writer.write(warning)
                            await writer.drain()
                            await self.show_menu(writer)
                    else:
                        warning = b"You don't have personal chats!\n"
                        writer.write(warning)
                        await writer.drain()
                        await self.show_menu(writer) 

                # Новый чат:
                elif message == '3':
                    # Выводим всех клиентов:
                    clients = Client().get_clients()
                    clients_list = [] # Список клиентов, который мы вывели для дальнейшей проверки
                    for ip in clients:
                        client = f'{clients[ip]}\n'
                        clients_list.append(client.strip())
                        writer.write(client.encode())
                        await writer.drain()

                    # Выбор нового клиента для переписки:
                    message = await self.listen(reader)
                    if message in clients_list:
                        client_folder = f'messages/personal_messages/{ip}'
                        for client_ip, name in clients.items():
                            if name == message:
                                new_chat_path = f'{client_folder}/{client_ip}.txt'
                                # Создаем файл с новым чатом:
                                if not os.path.exists(new_chat_path):                       
                                    open(new_chat_path, "w")
                                    filename = new_chat_path
                                    description = b'Write your massage: '
                                    writer.write(description)
                                    await writer.drain()
                                    break
                                else:
                                    warning = f'You are already in correspondence with {name}\n'
                                    writer.write(warning.encode())
                                    await writer.drain()
                                    await self.show_menu(writer)
                                    break
                    elif message == '/exit':
                        await self.show_menu(writer)
                    else:
                        warning = f'Client {message} not found.\n'
                        writer.write(warning.encode())
                        await writer.drain()
                        await self.show_menu(writer)

                else:
                    warning = b'Please, choose the number from menu!\n'
                    writer.write(warning)
                    await writer.drain()

            # Отправление сообщений в соответствующий чат и выход в меню через /exit:
            while True:
                await Chat().write_chat(writer, filename)
                message = await self.listen(reader)
                if message == '/exit':
                    await self.show_menu(writer)
                    break
                else:
                    await Chat().print_into_chat(message, ip, filename)
                

    async def start_our_server(self):
        srv = await asyncio.start_server(self.client_connected, self.host, self.port)

        async with srv:
            await srv.serve_forever()

if __name__ == '__main__':
    asyncio.run(Server().start_our_server())
