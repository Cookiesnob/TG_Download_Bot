import aria2p
from typing import List
from time import sleep

class aria2:
    def __init__(self, host:str, port:int, secret:str):
        self.aria2 = aria2p.API(
            aria2p.Client(
                host=host,
                port=port,
                secret=secret
            )
        )

    #获取下载信息
    def get_downloads(self,gids:List=''):
        data=[]
        try:
            downloads = self.aria2.get_downloads(gids)
        except:
            return []
        for download in downloads:
            data.append((download.gid,download.name,download.download_speed,download.completed_length,download.total_length,download.status))
        return data

    #添加下载
    def download(self , urls:List):
        data={}
        for url in urls:
            downloads = self.aria2.add(url)
            for download in downloads:
                data[download.gid]=download.name
        return data

    #删除下载
    def remove(self,gids:List):
        downloads=self.aria2.get_downloads(gids)
        return self.aria2.remove(downloads,force=True,files=True,clean=True)

    #获取种子链接的父ID
    def followed_by_ids(self,gid):
        download=self.aria2.get_download(gid)
        return download.followed_by_ids