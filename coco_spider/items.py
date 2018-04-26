# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NovelItem(scrapy.Item):
    '''本类是小说类'''
    novel_id = scrapy.Field()  # 小说id
    novel_url = scrapy.Field()  # 小说地址
    novel_img = scrapy.Field()  # 封面
    novel_title = scrapy.Field()  # 书名
    novel_author = scrapy.Field()  # 作者
    novel_type = scrapy.Field()  # 类型
    novel_intro = scrapy.Field()  # 介绍
    novel_chapters_url=scrapy.Field()  # 此小说下的章节url
    novel_chapter_titles= scrapy.Field()  # 此小说下章节的标题


class ChapterItem(scrapy.Item):
    novel_id = scrapy.Field()  # 小说id
    novel_type = scrapy.Field()  # 小说id
    chapter_title = scrapy.Field() #章节标题
    chapter_content = scrapy.Field() #章节内容
