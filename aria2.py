import aria2p
from typing import List
from time import sleep
import logging

logging.basicConfig(level=logging.INFO,
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(lineno)d - %(module)s - %(message)s')

logger = logging.getLogger('__name__')

class aria2:
    def __init__(self, host:str, port:int, secret:str):
        self.aria2 = aria2p.API(
            aria2p.Client(
                host=host,
                port=port,
                secret=secret
            )
        )


    def get(self,gids=''):
        #获取下载信息
        #参数
        #gids 可以为单str，也可以为list
        #返回
        #gid   文件唯一标识
        #name  文件名称
        #status 下载状态
        #download_speed 下载速度
        #completed_length 完成长度
        #total_length  全部长度
        #gid为单str返回[]
        #gid为list返回[()]
        flag=0
        data=[]
        if not isinstance(gids,list) and gids!='':
            tmp=[]
            tmp.append(gids)
            gids=tmp
            flag=1
        try:
            downloads = self.aria2.get_downloads(gids)
        except:
            return 'failed'
        for download in downloads:
            gid=download.gid
            name=download.name
            download_speed=self.converbit(download.download_speed)
            completed_length=self.converbit(download.completed_length)
            total_length=self.converbit(download.total_length)
            status=download.status[0].upper()+download.status[1:].lower()
            progress=[download.completed_length,download.total_length]
            data.append((gid,name,status,download_speed,completed_length,total_length,progress))
        if flag:
            return data[0]
        return data

    def add(self,urls):
        #添加下载
        #参数
        #urls str or list
        #返回
        #bool
        if not isinstance(urls,list):
            try:
                downloads = self.aria2.add(urls)
                logger.info('add download '+urls+' success')
            except:
                logger.info('add download failed')
                return False
        else:
            for url in urls:
                try:
                    downloads = self.aria2.add(url)
                    logger.info('add download '+url+' success')
                except:
                    logger.info('add download failed')
            return True

    def remove(self,gid):
        #删除下载
        #参数
        #gids str
        #返回
        #bool
        gid=[gid]
        try:
            downloads=self.aria2.get_downloads(gid)
            logger.info('remove '+downloads[0].name+' success')
        except:
            logger.info('remove download failed')
            return False
        return self.aria2.remove(downloads,force=True,files=True,clean=True)[0]


    def followed_by_ids(self,gid):
        #获取种子链接的父ID
        #参数
        #gid str
        #返回
        #gid
        download=self.aria2.get_download(gid)
        return download.followed_by_ids

    def retry(self,gid):
        #从下载失败的地方重试
        #参数
        #gid str
        #返回
        #bool
        gid=[gid]
        try:
            download=self.aria2.get_downloads(gid)
        except:
            logger.info('retry download failed')
            return False
        print(download[0].name)
        return self.aria2.retry_downloads(download,clean=True)[0]

    def pause(self,gid):
        #暂停下载
        #参数
        #gid str
        #返回
        #bool

        gid=[gid]
        try:
            download=self.aria2.get_downloads(gid)
        except:
            logger.info('pause failed')
            return False
        logger.info('pause '+download[0].name+' success')
        return self.aria2.pause(download,True)[0]

    def resume(self,gid):
        #开始下载
        #参数
        #gid str
        #返回
        #bool

        gid=[gid]
        try:
            download=self.aria2.get_downloads(gid)
        except:
            logger.info('resume failed')
            return False
        logger.info('resume '+download[0].name+' success')
        return self.aria2.resume(download)[0]



    def converbit(self,length):
        #转换单位
        #参数
        #length B
        #返回
        #B,KB,MB,GB,TB

        lis=['B','KB','MB','GB','TB']
        index=0
        while length>=1024:
            length/=1024
            index+=1
        return str(round(length,2))+' '+lis[index]