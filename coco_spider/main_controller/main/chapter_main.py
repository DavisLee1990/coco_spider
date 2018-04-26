# -*- coding:utf-8 -*-
#Author:Davis
from coco_spider.main_controller.spider_order import chapter_order
from coco_spider.settings import DATABASES_CONFIG,MAX_PROCESS
import redis
import threading

novel_queue_config=DATABASES_CONFIG["novel_queue_config"]
novel_redis_config=DATABASES_CONFIG["novel_redis_config"]
from  multiprocessing import Process,Pool


class RedisPool:
    def __init__(self):
        self.novel_queue_pool = redis.ConnectionPool(host=novel_queue_config["redis_url"], port=novel_queue_config["redis_port"], db=novel_queue_config["redis_db"])
        self.novel_redis_pool = redis.ConnectionPool(host=novel_redis_config["redis_url"], port=novel_redis_config["redis_port"], db=novel_redis_config["redis_db"])
#
def start_chapterController():
    redisPool=RedisPool()
    novel_queue = redis.Redis(connection_pool=redisPool.novel_queue_pool)
    novel_redis = redis.Redis(connection_pool=redisPool.novel_redis_pool)
    if __name__ == '__main__':
        pool = Pool(processes=MAX_PROCESS)  # 启动5个进程池,同时允许5个进程爬取章节
        while True:
            # 不断循环查看novel_queue(4号库)里面是否加入新的任务队列(当任务完成,没有value的key会自动删除)
            keys = novel_queue.keys()
            if keys:
                # 当一个key的任务队列pop完,key既会消失.所以这里如果有key执行继续执行,没有就继续监听
                for i in keys:
                    key = i.decode()
                    if novel_redis.exists(key)!=1:
                        # 会去5号库查看是否有key值,存在表示这个队列正在被其他任务所执行
                        # 如果不存在就开启进程执行章节队列爬取章节内容(线程池控制执行进程的个数)
                        # 开启一本小说的章节爬虫(小说线程个数由线程池控制)

                        #因为是分布式,这里一定要先把key的坑占到.不然这个任务可能会被别人领取而产生报错
                        novel_redis.set(key, "True")
                        pool.apply_async(func=chapter_order.start_chapterSpider,args=(key,))
start_chapterController()