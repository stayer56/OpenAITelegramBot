import os
import json
import asyncio
import aiohttp
import logging
from openai import OpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка API-ключей из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Токен Telegram-бота
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ключ OpenAI API

async def aiSend(text):
    """
    Отправляет запрос к OpenAI API и возвращает ответ.
    :param text: Текст сообщения от пользователя.
    :return: Ответ от OpenAI.
    """
    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key=OPENAI_API_KEY,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": text}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса."

async def getUpdateBot(offset):
    """
    Получает обновления от Telegram бота.
    :param offset: Смещение для получения новых сообщений.
    :return: JSON с обновлениями.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
        return None

async def sendMessageBot(chat_id, message):
    """
    Отправляет сообщение в Telegram.
    :param chat_id: ID чата, куда отправить сообщение.
    :param message: Текст сообщения.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return None


async def main():
    """
    Основная функция для обработки обновлений и ответов.
    """

    offset = 0  # Начальное смещение для получения обновлений
    while True:
        try:
            updates = await getUpdateBot(offset)
            if updates and updates.get("ok"):
                for update in updates["result"]:
                    message_update = update.get("message", {})
                    if "text" in message_update:
                        text = message_update["text"]
                        chat_id = message_update["chat"]["id"]

                        response = await aiSend(text)
                        await sendMessageBot(chat_id, response)

                        offset = update["update_id"] + 1

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Произошла ошибка: {e}")
            await asyncio.sleep(5)  # Пауза при ошибке

if __name__ == "__main__":
    asyncio.run(main())
