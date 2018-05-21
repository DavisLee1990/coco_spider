# -*- coding: utf-8 -*-
import scrapy
import requests
from coco_spider.items import NovelItem
from scrapy.http import Request
from lxml import etree
import redis
import json
from urllib import parse
from coco_spider.settings import max_page

class NovelsSpider(scrapy.Spider):
    name = 'novels'
    allowed_domains = ['m.xs.la']
    def start_requests(self):
        #开始解析:发送一个请求
        url="https://m.xs.la/newclass/0/1.html"
        page_num=1#用于记录页数并且让其爬多少页
        yield Request(url,meta={"page_num":page_num},callback=self.parse_novels)

    def parse_novels(self, response):
        #解析所有小说页
        try:
            #一,把第一页的数据爬取下来.
            print("返回的地址:",response.url)
            page_num=response.meta['page_num']
            urls = response.xpath('//div[@class="hot_sale"]/a/@href').extract()#获取页面的所有小说地址
            # 测试,只有第一本的数据爬取
            # yield Request(url=parse.urljoin("https://m.xs.la", urls[0]),meta={'novel_url':urls[0]},callback=self.parse_novel)
            for i in urls:
                #爬取第一页
                yield Request(
                    url=parse.urljoin("https://m.xs.la",i),
                    meta={'novel_url':i},
                    callback=self.parse_novel)
            # 二,如果页面爬取完毕就进入下一页爬取
            next_page = response.xpath('//a[@id="nextPage"]/@href').extract()[0]
            # print(next_page)
            if next_page and page_num<max_page:
                #爬取设置的页数
                page_num+=1
                yield scrapy.Request(url=parse.urljoin("https://m.xs.la",next_page),meta={"page_num":page_num},callback=self.parse_novels)#递归下载
            else:
                return print("爬取结束,当前页数:",page_num)
        except Exception as e:
            print("所有小说方法报错:", e)

    def parse_novel(self, response):
        #此类是小说类,爬取小说的详情数据以及加入队列
        try:
            novelItem = NovelItem()
            novelItem["novel_url"] = response.meta['novel_url']
            novelItem["novel_img"] = response.xpath('//div[@class="synopsisArea_detail"]/img/@src').extract()[0]
            novelItem["novel_title"] = response.xpath('//span[@class="title"]/text()').extract()[0]
            novelItem["novel_author"] = response.xpath('//div[@class="synopsisArea_detail"]//p[@class="author"]/text()').extract()[0]
            novelItem["novel_type"] = response.xpath('//div[@class="synopsisArea_detail"]/p[@class="sort"]/text()').extract()[0]
            novelItem["novel_intro"] = response.xpath('//div[@id="breview"]').xpath('string(.)').extract()[0]
            # 获取全部章节目录
            to_chapter_list_url = response.xpath('//a[@id="AllChapterList2"]/@href').extract()# 得到全部章节链接
            """
            这里说一个BUG:
            发启请求url=parse.urljoin("https://m.xs.la",all_chapter_url[0])
            print(all_chapter_url[0])    得出来的地址是-->/248_248993/all.html
            print(url)  得出来的地址是-->https://m.xs.la/ /248_248993/all.html
            这里的urljoin出现一个小BUG,如上述所见.我们看到多了一条/.原因是all_chapter_url[0]的地址如:
            " /246_246383/all.html",前面是有一个空格的
            """
            # 访问全部章节页面
            chapter_list_res = requests.get(url=parse.urljoin("https://m.xs.la",to_chapter_list_url[0].strip()))
            chapter_list_res.encoding = 'utf-8'
            chapter_list_text = chapter_list_res.text
            tree = etree.HTML(chapter_list_text.encode("utf-8"))
            #解析得到全部章节的标题及url
            novelItem["novel_chapters_url"] = tree.xpath('//div[@id="chapterlist"]/p/a/@href')
            novelItem["novel_chapter_titles"] = tree.xpath('//div[@id="chapterlist"]/p/a/text()')
            yield novelItem  # 把接受的对象交给pipelines中的NovelPipeline处理
        except Exception as e:
            print("小说类报错:", e)

