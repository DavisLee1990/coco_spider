# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import redis
import json
from coco_spider.orm_model_class import *
from urllib import parse

def trimNovel(str):
    #可抽取为工具类方法
    return str.replace('\r','').replace('\n','').replace('\t','').replace('\u3000\u3000','').replace('\xa0','').strip()
def trimChapter(str):
    #可抽取为工具类方法
    return str.replace('\r\n    \r\n','').replace('\t\r\n\t\r\n    \r\n','').replace('\u3000\u3000','\n').replace('\xa0',' ')


class NovelPipeline(object):
    #小说数据清洗
    def process_item(self, item, spider):
        try:
            if "novel_img" in item:
                #获取并提取数据
                item["novel_type"]=trimNovel(item["novel_type"]).replace("类别：","")
                item["novel_author"] = item["novel_author"].replace("作者：", "")
                item["novel_intro"] =trimNovel( item["novel_intro"])
                type_list=["玄幻奇幻","武侠仙侠","都市言情","历史军事","科幻灵异","网游竞技","女生频道"]
                item["novel_type"]=type_list.index(item["novel_type"])
        except Exception as e:
            print("NovelPipeline_Error:",e)
        finally:
            return item

class NovelSavePipeline(object):
    #此类是保存novel数据
    # 此类是做一个以novel_id为key的任务队列
    def __init__(self, addr1, port1, db1, *args, **kwargs):
        # 初始化一个redis连接池(该连接数据库为redis的5号数据库)
        super(NovelSavePipeline, self).__init__(*args, **kwargs)
        self.addr1 = addr1
        self.port1 = port1
        self.db1 = db1
        self.novel_queue_pool = redis.ConnectionPool(host=self.addr1, port=self.port1, db=self.db1)
        self.queue_conn = redis.Redis(connection_pool=self.novel_queue_pool)
    @classmethod
    def from_crawler(cls, crawler):
        redis_config = crawler.settings.get("DATABASES_CONFIG")["novel_redis_config"]
        return cls(
            addr1=redis_config["redis_url"],
            port1=redis_config["redis_port"],
            db1=redis_config["redis_db"]
        )
    def process_item(self, item, spider):
        try:
            #判断5号库是否有数据防止重复加入小说(由于网站不断更新小说在网络上)
            if "novel_img" in item:
                if self.queue_conn.exists(item["novel_url"]) != 1:
                    #不在库里面才加入
                    novel=Novel(
                        novel_img=item["novel_img"],
                        novel_title=item["novel_title"],
                        novel_type=item["novel_type"],
                        novel_author=item["novel_author"],
                        novel_intro=item["novel_intro"],
                        novel_status=0
                    )
                    Session.add(novel)
                    Session.commit()
                    item["novel_id"]=novel.novel_id
                    print("novel_id:",item["novel_id"])
        except Exception as e:
            print("NovelSavePipeline_Error:",e)
            Session.rollback()
        finally:
            return item


class NovelQueuePipleline(object):
    # 此类是做一个以novel_id为key的任务队列
    def __init__(self, addr1, port1, db1, *args, **kwargs):
        # 初始化一个redis连接池(该连接数据库为redis的5号数据库)
        super(NovelQueuePipleline, self).__init__(*args, **kwargs)
        self.addr1 = addr1
        self.port1 = port1
        self.db1 = db1
        self.novel_queue_pool = redis.ConnectionPool(host=self.addr1, port=self.port1, db=self.db1)
        self.queue_conn = redis.Redis(connection_pool=self.novel_queue_pool)
    @classmethod
    def from_crawler(cls, crawler):
        queue_config = crawler.settings.get("DATABASES_CONFIG")["novel_queue_config"]
        return cls(
            addr1=queue_config["redis_url"],
            port1=queue_config["redis_port"],
            db1=queue_config["redis_db"]
        )
    #加入任务队列(章节)
    def process_item(self, item, spider):
        try:
            if "novel_img" in item:
                # queue_conn = redis.Redis(connection_pool=self.novel_queue_pool)
                # for i in range(1,len(chapter_url)):
                # for i in range(1, 6):  # 测试只爬取5个章节

                    for i in range(1,len(item["novel_chapters_url"])):#由于第一章节是直达底部,所以不予以爬取
                        novel_data = {
                            "novel_id":item["novel_id"],
                            "novel_type": item["novel_type"],
                            "chapter_url": parse.urljoin("https://m.xs.la",item["novel_chapters_url"][i]),
                            "chapter_title":item["novel_chapter_titles"][i]
                        }
                        # 给4号库加入一个list类型的任务队列,key是小说的url,value就是此小说的章节队列
                        # print("加入队列:", novel_data)
                        self.queue_conn.rpush(item['novel_url'], json.dumps(novel_data))
        except Exception as e:
            print("NovelQueuePipleline_Error:",e)
        finally:
            return item


class ChapterPipeline(object):
    #章节数据清洗
    def process_item(self, item, spider):
        try:
            if "chapter_title" in item:
                item["chapter_content"]=trimChapter(item["chapter_content"])
                if item["chapter_content"].strip().startswith("正在手打中"):
                    item["chapter_content"]="源网站没有资源"
        except Exception as e:
            print("ChapterPipeline_Error:",e)
        finally:
            return item

class ChapterSavePipeline(object):
        # 章节保存类
    def process_item(self, item, spider):
        try:
            if "chapter_title" in item:
                chapter=None
                if item["novel_type"]==0:
                    chapter = Qihuan_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"]==1:
                    chapter = Wuxia_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"] == 2:
                    chapter = Doushi_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"] == 3:
                    chapter = Lishi_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"] == 4:
                    chapter = Kehuan_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"] == 5:
                    chapter = Wangyou_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                elif item["novel_type"] == 6:
                    chapter = Nvsheng_chapters(novel_id=item["novel_id"], chapter_title=item["chapter_title"],
                                              chapter_content=item["chapter_content"])
                print("加入数据库的内容:",item["chapter_content"])
                Session.add(chapter)
                Session.commit()
        except Exception as e:
            Session.rollback()
            print("ChapterSavePipeline_Error:",e)
        finally:
            return item

#
