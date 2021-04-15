import sqlite3
import os
import logging
from typing import List
logging.basicConfig(level=logging.WARNING,
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(lineno)d - %(module)s - %(message)s')
logger = logging.getLogger('__name__')

class db:
    def __init__(self):
        try:
            os.path.isfile("tg.db")
        except:
            with open('tg.db' ) as f:
                pass
        self.con = sqlite3.connect('tg.db')
        self.c = self.con.cursor()

    #创建用户表
    def create_user(self):
        try:
            self.c.execute('''CREATE TABLE USER
                (ID INT PRIMARY KEY     NOT NULL,
                FLAG        BOOLEAN   NOT NULL);''')
            logger.info("User table created successfully")
        except sqlite3.OperationalError:
            logger.info('User table exists')

    #创建数据表
    def create_data(self):
        try:
            self.c.execute('''CREATE TABLE DOWNLOAD
            (ID INT NOT NULL,
            LINK TEXT NOT NULL,
            GID TEXT NOT NULL,
            NAME TEXT NOT NULL,
            COMPLETED INT NOT NULL);''')
            logger.info("Download Table created successfully")
        except sqlite3.OperationalError:
            pass
            #self.c.execute('UPDATE DOWNLOAD SET COMPLETED= 0 WHERE COMPLETED !=100')

    #提交
    def commit(fun):
        def com(*args, **kwargs):
            fun(*args, **kwargs)
            args[0].con.commit()
        return com

    #新用户注册
    @commit
    def register(self,id):
        try:
            self.c.execute('INSERT INTO USER(ID,FLAG) VALUES(?,-1)',(id,))
        except:
            logger.info('Id exists')

    #设置权限
    @commit
    def author(self,id,flag):
        self.c.execute('UPDATE USER SET FLAG = ? WHERE ID=?',(flag,id,))


    #根据参数获取用户 -1为未审核，0未审核不通过，1为审核通过
    def get_user_list(self,flag):
        return [key[0] for key in self.c.execute('SELECT ID FROM USER WHERE FLAG=?',(flag,))]

    #获取全部用户
    def get_all_user(self):
        return self.c.execute('SELECT * FROM USER')

    #记录下载链接与gid
    @commit
    def record_url_gid(self,id:int,link:str,gid:int,name:str,completed:int):
        self.c.execute('INSERT INTO DOWNLOAD(ID,LINK,GID,NAME,COMPLETED) VALUES(?,?,?,?,?) ',(id,link,gid,name,completed,))

    #判断下载链接,如果是该用户下载,则提示已添加,不是该用户则复制一份信息
    def judgment_download(self,urls:List,id:int):
        data=urls[:]
        op=''
        for url in urls:
            res=[key for key in self.c.execute('SELECT ID,GID,NAME,COMPLETED FROM DOWNLOAD WHERE LINK= ?',(url,))]
            if res == []:
                continue
            flag=True
            for re in res:
                key=re
                if id in re:
                    try:
                        data.remove(url)
                    except:
                        pass
                    flag=False
                    break
            if flag:
                gid=key[1]
                name=key[2]
                completed=key[3]
                self.record_url_gid(id,url,gid,name,completed)
                data.remove(url)
                op='copy'
        return data,op

    #更新下载状态
    @commit
    def update_status(self,gid,completed):
        return self.c.execute('UPDATE DOWNLOAD SET COMPLETED=? WHERE GID=?',(completed,gid,))

    #判断是否删除
    def judgment_remove(self,id,gid:str):
        print(gid)
        data=list(set([key[0] for key in self.c.execute('SELECT ID FROM DOWNLOAD WHERE GID=?',(gid,))]))
        try:
            data.remove(id)
        except:
            pass
        if data!=[]:
            self.remove_by_id(id,gid)
            return False
        if data==[]:
            self.remove(gid)
        return True

    #删除文件，实际只删除ID
    @commit
    def remove_by_id(self,id:int,gid:str):
        return self.c.execute('DELETE FROM DOWNLOAD WHERE GID=? AND ID=?',(gid,id,))

    #删除文件
    @commit
    def remove(self,gid):
        return self.c.execute('DELETE FROM DOWNLOAD WHERE GID=?',(gid,))

    #获取记录
    def get_download_by_id(self,id):
        res=self.c.execute('SELECT GID FROM DOWNLOAD WHERE ID=?',(id,))
        return res


    #获取全部 测试用
    def get_all(self):
        # self.c.execute('SELECT ID FROM USER')
        # res=[key[0] for key in self.c]
        # data=self.c.execute('SELECT * FROM DOWNLOAD').fetchall()
        datas=self.c.execute('SELECT * FROM DOWNLOAD').fetchall()
        for data in datas:
            print(data)

    #关闭
    def close(self):
        self.con.close()

    @commit
    def main(self):
        self.create_user()
        self.create_data()


if __name__=="__main__":
    sql=db()
    sql.main()
    sql.get_all()
    sql.close()