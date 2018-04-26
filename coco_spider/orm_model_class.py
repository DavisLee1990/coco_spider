# -*- coding:utf-8 -*-
# Author:Davis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean,Text
from sqlalchemy.orm import sessionmaker
from coco_spider.settings import DATABASES_CONFIG
mysql_config=DATABASES_CONFIG["mysql_config"]

# engine = create_engine("mysql+pymysql://root:123456@192.168.1.10/test?charset=utf8")会报错 Warning: (1366, "Incorrect string valu
engine = create_engine("mysql+mysqlconnector://%s:%s@%s/%s?charset=utf8"%(
    mysql_config["user"],
    mysql_config["pwd"],
    mysql_config["ip"],
    mysql_config["db"]
))
Base = declarative_base()  # 生成orm基类
Session_class=sessionmaker(bind=engine)
Session = Session_class()

class Novel(Base):
    # 小说类
    __tablename__ = 'novels'  # 表名
    novel_id = Column(Integer, primary_key=True, autoincrement=True)  # 小说id,主键且自增
    novel_title = Column(String(90))  # 小说名
    novel_img = Column(String(100))  # 小说图片地址
    novel_author = Column(String(45))  # 小说作者
    novel_status = Column(Boolean)  # 小说状态
    novel_type = Column(SmallInteger)  # 小说类型(会根据类型去找章节分表的库)
    novel_intro = Column(Text)  # 小说简介


class Chapters:
    # 章节表基类
    chapter_id = Column(Integer, primary_key=True, autoincrement=True)  # 小说id,主键且自增
    novel_id = Column(Integer)#小说的id
    chapter_title = Column(String(90))  # 章节名
    chapter_content = Column(Text)  # 章节内容


class Qihuan_chapters(Chapters, Base):
    __tablename__ = 'Qihuan_chapters'  # 玄幻/奇幻


class Wuxia_chapters(Chapters, Base):
    __tablename__ = 'Wuxia_chapters'  # 武侠/仙侠


class Doushi_chapters(Chapters, Base):
    __tablename__ = 'Doushi_chapters'  # 都市/言情


class Lishi_chapters(Chapters, Base):
    __tablename__ = 'Lishi_chapters'  # 历史/军事


class Kehuan_chapters(Chapters, Base):
    __tablename__ = 'Kehuan_chapters'  # 科幻/灵异


class Wangyou_chapters(Chapters, Base):
    __tablename__ = 'Wangyou_chapters'  # 网游/竞技


class Nvsheng_chapters(Chapters, Base):
    __tablename__ = 'Nvsheng_chapters'  # 女生频道

# Base.metadata.create_all(engine)  # 利用django创建表结构,先展示使用.创建表结构
