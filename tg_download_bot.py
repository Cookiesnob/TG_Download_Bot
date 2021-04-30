import logging,hashlib,aiohttp,re,asyncio,threading
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher, filters
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook,start_polling
from aiogram.utils import executor
from aiogram.types import ChatActions,ParseMode
from aria2 import aria2
from time import sleep
from typing import List
from config import config
import math

logging.basicConfig(level=logging.INFO,
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(lineno)d - %(module)s - %(message)s')

logger = logging.getLogger('__name__')

inquiry_mode=config.get('inquiry_mode',False)

API_TOKEN = config.get('API_TOKEN')
PROXY_URL ='socks5://127.0.0.1:7890'

# webhook settings
if inquiry_mode:
    WEBHOOK_URL = config.get('WEBHOOK_URL')
    WEBAPP_HOST = config.get('WEBAPP_HOST')
    WEBAPP_PORT = config.get('WEBAPP_PORT')


bot = Bot(token=API_TOKEN, proxy = PROXY_URL)
#bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

#初始化aria2
aria2=aria2(config.get('aria2')[0],config.get('aria2')[1],config.get('aria2')[2])

#设置刷新窗口
flash={}
tmp={}


@dp.message_handler(commands=['start'])
async def start(message:types.message):
    await bot.send_message(message.chat.id,'欢迎使用TG下载机器人 请输入 /help 查看帮助')

@dp.message_handler(commands=['complete'])
async def complete(message:types.message):
    id=message.chat.id
    try:
        data=flash['complete']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg,statu='Complete'))
    flash['complete']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['running'])
async def running(message:types.message):
    id=message.chat.id
    try:
        data=flash['running']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg,statu='Active'))
    flash['running']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['stopping'])
async def stopping(message:types.message):
    id=message.chat.id
    try:
        data=flash['stopping']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg,statu='Paused'))
    flash['stopping']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['waiting'])
async def waiting(message:types.message):
    id=message.chat.id
    try:
        data=flash['waiting']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg,statu='Waiting'))
    flash['waiting']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['error'])
async def waiting(message:types.message):
    id=message.chat.id
    try:
        data=flash['error']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg,statu='Error'))
    flash['error']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['status'])
async def waiting(message:types.message):
    id=message.chat.id
    try:
        data=flash['status']
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    msg=await bot.send_message(id,'等待更新状态。。。')
    task = asyncio.create_task(update(msg=msg))
    flash['status']=[msg.chat.id,msg.message_id,task]

@dp.message_handler(commands=['trans'])
async def trans(message:types.message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    text_and_data = (
    ('OneDrive', 'od'),
    ('GoogleDive', 'gd'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    await message.reply("请选择转存网盘:", reply_markup=keyboard_markup)


@dp.message_handler(commands=['cancel'])
async def cancel(message:types.message):
    id=message.chat.id
    gid=message.text.lstrip('/cancel').strip()

    flag=aria2.remove(gid)
    if flag:
        await bot.send_message(id,'取消成功')
        await self.status(message)
    await bot.send_message(id,'取消失败，文件不存在或重试')
    return

@dp.message_handler(commands=['help'])
async def start(message:types.message):
    await bot.send_message(message.chat.id,'''
支持直接发送链接与torrent文件,支持(http(s),magnet)

全部参数
/complete 获取下载完成列表
/running 获取下载中列表
/stopping 获取停止列表
/waiting 获取等待列表
/error 获取下载错误列表

/pause 指令加GID暂停下载
/resume 指令加GID重启下载
/cancel 指令后加GID取消下载
/trans 转存文件，支持OD,GD
/help 查看帮助指令
''')

@dp.message_handler()
async def link(message:types.message):
    magnet_pat=r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*)'
    http_pat=r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\()-?=%.]+"
    id=message.chat.id
    if 'http' in message.text:
        urls=re.findall(http_pat, message.text)
        if urls==[]:
            return
        data=aria2.add(urls)
        await bot.send_message(id,'开始下载,可通过 /status 查看状态')
    if 'magnet' in message.text:
        urls=re.findall(magnet_pat,message.text)
        data=aria2.download(urls)
        await bot.send_message(id,'开始下载,可通过 /status 查看状态')

@dp.callback_query_handler(text='od')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    data = query
    gid=data.message.reply_to_message.text.lstrip('/trans').strip()
    res=aria2.get(gid)
    if res=='failed':
        await bot.send_message(query.from_user.id, '未找到指定GID，请检查输入值')
        return
    name=res[1]
    status=res[2]
    if status!='Complete':
        await bot.send_message(query.from_user.id, f'{name} 未完成下载,转存失败')
        return
    await bot.send_message(query.from_user.id, f'准备转存 {name}')



async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    sql.close()
    await bot.delete_webhook()
    logging.warning('Bye!')

def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


#根据需要更新下载信息
async def update(msg=[],statu=[]):
    while True:
        datas=aria2.get()
        if datas==[]:
            await bot.send_message(msg.chat.id,'暂时没有任务哦,请添加任务')
            break
        text=''
        i=0
        for data in datas:
            gid=data[0]
            name=data[1]
            status=data[2]
            if not statu==[]:
                if not status==statu:
                    continue
            speed=data[3]
            completed=data[4]
            total=data[5]
            progress=data[6]
            progress=str(get_progress_bar(progress[0],progress[1]))
            if completed==total:
                progress=str(get_progress_bar(1,1))
                text+=f'<b>Name</b> : <b>{name}</b>\n<b>Status</b> : <b>{status}</b>\n<b>Speed</b> : <b>{speed}</b>\n<b>Downloaded</b> : <b>{total} of {total}</b>\n<b>Progress</b> : <b>{progress}</b>\n<b>Gid</b>: <b><code>{gid}</code></b>\n\n'
            else:
                text+=f'<b>Name</b> : <b>{name}</b>\n<b>Status</b> : <b>{status}</b>\n<b>Speed</b> : <b>{speed}</b>\n<b>Downloaded</b> : <b>{completed} of {total}</b>\n<b>Progress</b> : <b>{progress}</b>\n<b>Gid</b>: <b><code>{gid}</code></b>\n\n'
            i+=1
        if text=='':
            await bot.edit_message_text('没有任务哦！',parse_mode='HTML',chat_id=msg.chat.id,message_id=msg.message_id)
        await bot.edit_message_text(text,parse_mode='HTML',chat_id=msg.chat.id,message_id=msg.message_id)
        sleep(2)



def get_progress_bar(num ,total):
    if total==0:
        return get_progress_bar(0,1)
    rate = num / total
    rate_num = int(rate * 100)
    r = '\r[%s%s] %d %%' % ("⚫"*math.floor(rate_num/10), "⚪"*math.ceil((100-rate_num)/10),rate*100)
    return r

if __name__ == '__main__':
    if inquiry_mode:
        start_webhook(
        dispatcher=dp,
        webhook_path='/'+'/'.join(WEBHOOK_URL.split('/')[3:]),
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,)
    else:
        executor.start_polling(dp, skip_updates=True)
