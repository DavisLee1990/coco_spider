# -*- coding:utf-8 -*-
#Author:Davis
from scrapy.cmdline import execute  #导入执行scrapy命令方法
import sys
import os
#给Python解释器，添加模块新路径 ,将main.py文件所在目录添加到Python解释器
sys.path.append(os.path.join(os.getcwd()))
def start_chapterSpider(key):
    str="redis_key=" + key
    execute(['scrapy', 'crawl','chapters','-a',str])  #chapters执行scrapy命令
