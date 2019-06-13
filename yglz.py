#!E:\Anaconda3 python
# -*- coding: utf-8 -*-
# @Time    : 2019/6/13 7:50
# @Author  : James_jia
# @Email   : 976033262@qq.com
# @File    : yglz.py
# @Software: PyCharm


from lxml import etree
from urllib.parse import quote
import requests
import pymongo


class Spider():
    """
    河北新闻网阳光理政 爬虫
    """
    def __init__(self):
        self.city = quote(input('你想要哪个城市的信息:'))  # 通过urllib.parse.quote()方法将城市名进行url编码
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        }
        self.url = 'http://yglz.tousu.hebnews.cn/l-----{}'.format(self.city)

    def get_max_page(self):
        """
        发现页面事件是aspx动态生成，分析其中的请求参数
        :max_page:通过先访问一次的方式，获取的事件的最大页数
        :viewstate:动态参数
        """
        rsp = requests.get(self.url, headers=self.headers)
        response = etree.HTML(rsp.text)
        max_page = response.xpath('//div[@class="pageindex"]/text()')[0].split('/')[1].split('页')[0]
        viewstate = response.xpath('//input[@type="hidden"]')
        data = {}  # 先创建data字典，方便接下来参数的加入
        for i in viewstate:
            data.update({i.get('name'): i.get('value')})
        for i in range(1, int(max_page)+1):
            data.update({
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__CALLBACKID': '__Page',
                '__CALLBACKPARAM': 'Load|*|{}'.format(i),
                'ctl00$ContentPlaceHolder1$depname': self.city,  # 城市这项务必需要写入，不然会出错，得不到想要的数据量
            })
            self.get_info(data)

    def get_info(self, data):
        """
        通过post方法获取动态信息，并用xpath匹配其中需要的部分
        :content:把获取到的数据写到一个字典里，方便写入mongo数据库
        """
        res = requests.post(self.url, data=data, headers=self.headers)
        response = etree.HTML(res.text)
        news_list = response.xpath('//div[@class="listcon"]')
        if news_list:
            for div in news_list:
                gov = div.xpath('./span[1]/p/a/text()')[0]
                kind = div.xpath('./span[2]/p/text()')[0].strip()
                title = div.xpath('./span[3]/p/a/text()')[0]
                rec_time = div.xpath('./span[4]/p/text()')[0].strip()
                end_time = div.xpath('./span[5]/p/text()')[0].strip()
                state = div.xpath('./span[6]/p/text()')[0].rstrip()
                content = {
                    '受理单位': gov,
                    '分类': kind,
                    '主题': title,
                    '受理时间': rec_time,
                    '办结时间': end_time,
                    '办理状态': state
                }
                self.write(content)

    def write(self, content):
        """
        把爬到的数据写入mongo数据库里
        """
        client = pymongo.MongoClient('localhost', 27017)
        db = client['content']['yglz']
        db.insert_one(content)


if __name__ == '__main__':
    a = Spider()
    a.get_max_page()