# -*- coding: utf-8 -*-
import scrapy
import redis
import threading
import json
from lxml import etree
from coco_spider.items import ChapterItem
from coco_spider.settings import DATABASES_CONFIG
import requests
import time

novel_queue_config=DATABASES_CONFIG["novel_queue_config"]
novel_redis_config=DATABASES_CONFIG["novel_redis_config"]

class ChaptersSpider(scrapy.Spider):
    name = 'chapters'
    allowed_domains = ['m.xs.la']
    def __init__(self,redis_key=None,*args, **kwargs):
        self.key=redis_key
        super(ChaptersSpider, self).__init__(*args, **kwargs)
        self.novel_queue_pool = redis.ConnectionPool(host=novel_queue_config["redis_url"],
                                                     port=novel_queue_config["redis_port"],
                                                     db=novel_queue_config["redis_db"])
        self.novel_redis_pool = redis.ConnectionPool(host=novel_redis_config["redis_url"],
                                                     port=novel_redis_config["redis_port"],
                                                     db=novel_redis_config["redis_db"])
        self.novel_queue = redis.Redis(connection_pool=self.novel_queue_pool)
        self.novel_redis = redis.Redis(connection_pool=self.novel_redis_pool)

    def get_chapterItem(self,data):
        try:
            chapterItem = ChapterItem()
            chapter_res = requests.get(data["chapter_url"])
            chapter_res.encoding = 'utf-8'
            chapter_text = chapter_res.text
            tree = etree.HTML(chapter_text)
            chapter_content = tree.xpath('//div[@id="chaptercontent"]/text()')
            chapter_content = "".join(chapter_content)
            chapterItem["novel_id"] = data["novel_id"]
            chapterItem["novel_type"] = data["novel_type"]
            chapterItem["chapter_title"] = data["chapter_title"]
            chapterItem["chapter_content"] = chapter_content
            if not chapter_content:
                #如果没访问到数据，反复调用
                chapterItem=self.get_chapterItem(data)
            return chapterItem
        except Exception as e:
            print("获取item报错:",e)

    def start_requests(self):
        #不断监听链表集合里面是否有key
        key=self.key
        data = json.loads(self.novel_queue.lpop(key).decode())
        yield scrapy.Request(url=data["chapter_url"],meta={
            "novel_id":data["novel_id"],
            "novel_type": data["novel_type"],
            "chapter_title":data["chapter_title"]
        },callback=self.parse_queue)

    def parse_queue(self, response):
        chapterItem = ChapterItem()
        body=response.body
        tree = etree.HTML(body)
        chapter_content = tree.xpath('//div[@id="chaptercontent"]/text()')
        chapter_content = "".join(chapter_content)
        chapterItem["novel_id"] = response.meta['novel_id']
        chapterItem["novel_type"] = response.meta['novel_type']
        chapterItem["chapter_title"] = response.meta['chapter_title']
        chapterItem["chapter_content"] = chapter_content
        if not chapter_content:
            # 如果没访问到数据，反复调用
            data={
                "novel_id":chapterItem["novel_id"],
                "novel_type":chapterItem["novel_type"],
                "chapter_title":chapterItem["chapter_title"],
                "chapter_url":response.url
            }
            chapterItem=self.get_chapterItem(data)
        yield chapterItem

        # 监测4号库队列的任务爬取情况,不断向队列中添加数据,所以不能做成for循环
        key = self.key
        print(self.novel_queue.llen(key))
        while self.novel_queue.llen(key)!=0:
            data=json.loads(self.novel_queue.lpop(key).decode())
            get_item=self.get_chapterItem(data)
            yield get_item  # 把接受的对象交给pipelines处理
        # else:
            # 释放掉5号库的key值(由于目标网站小说不断的更新,后面改成不释放以表示此爬取过了)
            # self.novel_redis.delete(key)
            # print("5号库释放key:",key)