import logging,hashlib,aiohttp,re,asyncio,threading
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher, filters
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook,start_polling
from aiogram.utils import executor
from aiogram.types import ChatActions,ParseMode
from sqlite import db
from aria2 import aria2
from time import sleep
from typing import List
from config import config
import math

logging.basicConfig(level=logging.INFO,
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(lineno)d - %(module)s - %(message)s')

API_TOKEN = config.get('API_TOKEN')
#PROXY_URL ='socks5://127.0.0.1:7890'

# webhook settings
WEBHOOK_URL = config.get('WEBHOOK_URL')
WEBAPP_HOST = config.get('WEBAPP_HOST')
WEBAPP_PORT = config.get('WEBAPP_PORT')


#bot = Bot(token=API_TOKEN, proxy = PROXY_URL)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

#初始化数据库
sql=db()
sql.main()

#初始化aria2
aria2=aria2(config.get('aria2')[0],config.get('aria2')[1],config.get('aria2')[2])

#设置管理员
admin=config.get('admin')
sql.register(admin)
sql.author(admin,1)

#设置刷新窗口
flash={}
tmp={}

#设置允许用户清单
user_id_required=sql.get_user_list(1)
user_id_required.append(admin)

@dp.message_handler(commands=['start'])
async def start(message:types.message):
    await bot.send_message(message.chat.id,'欢迎使用TG下载机器人 请输入 /help 查看帮助')

@dp.message_handler(commands=['bind'])
async def bind(message:types.message):
    username=message['from'].username
    id=message.chat.id
    all_user=sql.get_all_user()
    rem=''
    for key in all_user:
        if id==key[0]:
            if key[1]==0:
                await bot.send_message(message.chat.id,'未通过审核,已重新申请')
                rem='之前未通过申请'
            elif key[1]==-1:
                await bot.send_message(message.chat.id,'请等待审核')
                return
            elif key[1]==1:
                await bot.send_message(message.chat.id,'用户已绑定')
                return
    sql.register(id)
    await bot.send_message(message.chat.id,'请等待审核')
    remark=message.text.lstrip('/bind')
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    text_and_data = (
    ('通过', 'yes'),
    ('拒绝', 'no'),)
    #('取消','cancel'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    await bot.send_message(admin,'用户: {username}\nid: {id}\n备注: {remark}{rem}'.format(username=username,id=id,remark=remark,rem=rem),reply_markup=keyboard_markup)

@dp.message_handler(commands=['link'])
async def link(message:types.message):
    magnet_pat=r'(magnet:\?xt=urn:btih:[a-zA-Z0-9]*)'
    http_pat=r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\()-?=%.]+"
    id=message.chat.id
    if login_need(id):
        return
    if 'http' in message.text:
        urls=re.findall(http_pat, message.text)
        urls,key=sql.judgment_download(urls,id)
        if urls==[] and (key!='copy' ):
            await bot.send_message(id,'请勿重复发送链接')
            return
        data=aria2.download(urls)
        i=0
        for key,value in data.items():
            sql.record_url_gid(id,urls[i],key,value,0)
            i+=1
        await bot.send_message(id,'开始下载,可通过 /status 查看状态')
    if 'magnet' in message.text:
        urls=re.findall(magnet_pat,message.text)
        i=0
        for i in range(len(urls)):
            urls[i]=urls[i]+'.child'
        urls,key=sql.judgment_download(urls,id)
        i=0
        for i in range(len(urls)):
            urls[i]=urls[i].rstrip('.child')
        if urls==[] and (key!='copy' ):
            await bot.send_message(id,'请勿重复发送链接')
            return
        data=aria2.download(urls)
        i=0
        for key,value in data.items():
            sql.record_url_gid(id,urls[i],key,value,0)
            until_update(id,urls[i],key)
            i+=1
        await bot.send_message(id,'开始下载,可通过 /status 查看状态')


@dp.message_handler(commands=['status'])
async def status(message:types.message):
    id=message.chat.id
    if login_need(id):
        return
    datas=sql.get_download_by_id(id)
    gid=[]
    for data in datas:
        gid.append(data[0])
    global tmp
    tmp[id]=gid
    msg=await bot.send_message(id,'等待更新状态。。。')
    try:
        data=flash[id]
        data[2].cancel()
        await bot.delete_message(data[0],data[1])
    except:
        pass
    task = asyncio.create_task(update(gids=gid,msg=msg))
    flash[id]=[msg.chat.id,msg.message_id,task]
    #展示内容
    #name,进度,状态,速度,取消链接

    #内存,cpu,硬盘

@dp.message_handler(commands=['cancel'])
async def cancel(message:types.message):
    id=message.chat.id
    if login_need(id):
        return
    gid=message.text.lstrip('/cancel').strip()
    gid=[gid]
    if sql.judgment_remove(id,gid[0]):
        try:
            flag=aria2.remove(gid)[0]
        except:
            flag=False
        if flag:
            await bot.send_message(id,'取消成功')
            print(flash)
            data=flash[id]
            data[2].cancel()
            await bot.delete_message(data[0],data[1])
            global tmp
            value=[]
            for key,value in tmp.items():
                if key==id:
                    value.remove(gid[0])
                    break
            if value==[]:
                return
            msg=await bot.send_message(id,'更新状态。。。')
            task = asyncio.create_task(update(gids=value,msg=msg))
            flash[id]=[msg.chat.id,msg.message_id,task]
            return
        await bot.send_message(id,'取消失败，文件不存在或重试')
        return
    await bot.send_message(id,'取消成功')

@dp.message_handler(commands=['help'])
async def start(message:types.message):
    await bot.send_message(message.chat.id,'''
全部参数
/start 欢迎使用
/bind 绑定用户,可在指令后添加备注方便验证
/link 指令后加下载链接,支持类型(http(s),magnet),仅通过验证用户可使用
/status 查看下载状态,仅通过验证用户可使用
/cancel 指令后加GID取消下载,仅通过验证用户可使用
/help 查看帮助指令
''')

@dp.callback_query_handler(text='no')
@dp.callback_query_handler(text='yes')
#@dp.callback_query_handler(text='cancel')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    data = query
    pat=r'id: (\d+)'
    id=re.search(pat,data.message.text).group(1)
    if data.data == 'yes':
        sql.author(int(id),1)
        text = f'你通过了\n{data.message.text}'
        await bot.send_message(id, '用户已绑定')
        user_id_required.append(int(id))
    elif  data.data == 'no':
        sql.author(int(id),0)
        text = f'你拒绝了\n{data.message.text}'
        await bot.send_message(id, '你未通过审核')
    elif data.data == 'cancel':
        text = f'你忽略了\n{data.message.text}'
        await bot.delete_message(data.message.chat.id,data.message.message_id)
    else:
        text = f'Unexpected callback data {answer_data!r}!'
    await bot.send_message(admin, text)
    await bot.delete_message(data.message.chat.id,data.message.message_id)

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

@new_thread
def until_update(id:int,link:str,gid:int):
    sql=db()
    sql.main()
    while True:
        newgid=aria2.followed_by_ids(gid)
        if newgid !=[]:
            break
        sleep(5)
    name=aria2.get_downloads(newgid)[0][1]
    sql.record_url_gid(id,link+'.child',newgid[0],name,0)

#根据需要更新下载信息
async def update(gids:List=[],msg=[]):
    if gids==[]:
        await bot.send_message(msg.chat.id,'没有下载任务')
        return
    flag=[0 for _ in range(len(gids))]
    while True:
        datas=aria2.get_downloads(gids)
        if datas==[]:
            break
        text=''
        i=0
        for data in datas:
            gid=data[0]
            name=data[1]
            speed=converbit(data[2])+'/s'
            completed=converbit(data[3])
            total=converbit(data[4])
            status=data[5][0].upper()+data[5][1:].lower()
            progress=str(get_progress_bar(data[3],data[4]))
            if completed==total:
                sql.update_status(gid,100)
                flag[i]=1
            if flag[i]==1:
                progress=str(get_progress_bar(data[4],data[4]))
                text+=f'<b>Name</b> : <b>{name}</b>\n<b>Status</b> : <b>{status}</b>\n<b>Speed</b> : <b>{speed}</b>\n<b>Downloaded</b> : <b>{total} of {total}</b>\n<b>Progress</b> : <b>{progress}</b>\n<b>Gid</b>: <b><code>{gid}</code></b>\n\n'
            else:
                text+=f'<b>Name</b> : <b>{name}</b>\n<b>Status</b> : <b>{status}</b>\n<b>Speed</b> : <b>{speed}</b>\n<b>Downloaded</b> : <b>{completed} of {total}</b>\n<b>Progress</b> : <b>{progress}</b>\n<b>Gid</b>: <b><code>{gid}</code></b>\n\n'
            i+=1
        await bot.edit_message_text(text,parse_mode='HTML',chat_id=msg.chat.id,message_id=msg.message_id)
        if list(set(flag))==[1]:
            await bot.send_message(msg.chat.id,'所有下载任务已完成')
            break
        sleep(2)

def converbit(length):
    lis=['B','KB','MB','GB','TB']
    index=0
    while length>=1024:
        length/=1024
        index+=1
    return str(round(length,2))+' '+lis[index]

def login_need(id):
    if id in user_id_required:
        return False
    return True

def get_progress_bar(num ,total):
    if total==0:
        return get_progress_bar(0,1)
    rate = num / total
    rate_num = int(rate * 100)
    r = '\r[%s%s] %d %%' % ("⚫"*math.floor(rate_num/10), "⚪"*math.ceil((100-rate_num)/10),rate*100)
    return r

if __name__ == '__main__':
    #executor.start_polling(dp, skip_updates=True)
    start_webhook(
        dispatcher=dp,
        webhook_path='/'+'/'.join(WEBHOOK_URL.split('/')[3:]),
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )