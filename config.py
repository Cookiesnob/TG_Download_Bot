config={
    'inquiry_mode': False,     #False 为轮询  True 为 webhook 若为True需要填写5,6,7项，否则不用
    'API_TOKEN': '',           #机器人token
    'aria2': [],               #['ip',port,'secret']
    'admin': ,                 #tg id
    'onedrive':,               #rclone onedrive名字
    'googledrive': ,           #rclone googledrive名字
    #webhook 所需项
    'WEBHOOK_URL' : "https://bot.honus.top/webhook",  #url  https://url/path
    'WEBAPP_HOST' : 'localhost',                      # or ip
    'WEBAPP_PORT' : 9999
}