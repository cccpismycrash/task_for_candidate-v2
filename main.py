import asyncio
import logging
from aiogram import Bot
from config_reader import config
from aiogram.types import FSInputFile
from aiogram.types import InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from processing import make_pic
from database.models import add_column
from database.models import init_models

TEST_GROUP_ID = config.GROUP_ID

logging.basicConfig(level=logging.INFO)


async def send_gragh(text):
    async with Bot(token=config.BOT_TOKEN.get_secret_value()) as bot:
        await bot.send_media_group(chat_id=TEST_GROUP_ID, media=[InputMediaPhoto(type='photo', media=FSInputFile('result.png'), caption=text)])

async def main():
    await init_models()
    datestr, target_value = make_pic()
    text_for_post = f'Доля акций эмитентов, входящих в базу расчёта индекса IMOEX на {datestr} составляет {target_value}%'
    await add_column(act_time=datestr, text=text_for_post, value=target_value)
    await send_gragh(text_for_post)


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    # scheduler.add_job(main, 'interval', seconds=3)
    scheduler.add_job(main, 'cron', day_of_week='mon-fri', hour=12, minute=00, end_date='2025-10-13')

    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
