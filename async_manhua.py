# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 15:36:40 2021

@author: yin
"""

import asyncio
import aiohttp
import aiofiles
from lxml import etree
from asyncio.exceptions import TimeoutError
import requests
import time
import os
import re
from fake_useragent import UserAgent
from functools import wraps
from asyncio.proactor_events import _ProactorBasePipeTransport


def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
            
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise

    return wrapper


_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(
    _ProactorBasePipeTransport.__del__)
ua = UserAgent()
headers = {'User-Agent': ua.random}



class manhuadb:
    def __init__(self):
        self.index_num = 1
        self.index_dict = {}
        self.base_url = 'https://www.manhuadb.com'
        self.total_num = 0

    async def get_url(self, url):
        async with aiohttp.ClientSession() as client:
            res = await client.get(url, headers=headers)
            return await res.text()

    async def page_num_parse(self, html):
        html_parse = etree.HTML(html)
        search_num_url = html_parse.xpath('//div[@class="form-inline"]/a[@title="最后一页"]/@href')[0]
        search_num = search_num_url.split('=')[-1]
        # base_url = 'https://www.manhuadb.com'
        demo_url = html_parse.xpath('//div[@class="form-inline"]/a[@title="第一页"]/@href')[0] + '&p='
        arr = []
        for num in range(1, int(search_num) + 1):
            full_url = self.base_url + demo_url + str(num)
            arr.append(full_url)
        return arr

    async def parse_html(self, html):
        # 解析搜索到的结果
        search_result_url = []
        html_parse = etree.HTML(html)
        search_result_title = html_parse.xpath('//div[contains(@class,"comicbook-index")]/a/@title')
        search_result_demo_url = html_parse.xpath('//div[contains(@class,"comicbook-index")]/a/@href')
        for i in search_result_demo_url:
            full_url = self.base_url + i
            search_result_url.append(full_url)
        for k, v in dict(zip(search_result_title, search_result_url)).items():
            print(f'{self.index_num},{k}:{v}')
            self.index_dict[self.index_num] = v
            self.index_num += 1

    async def comic_parse(self, comic_html):
        version_parse = etree.HTML(comic_html)
        version = version_parse.xpath('//ul[contains(@id,"myTab")]/li[@class="nav-item"]/a/span/text()')
        version_id = version_parse.xpath('//ul[contains(@id,"myTab")]/li[@class="nav-item"]/a/@href')
        version_f_id = []
        for v_id in version_id:
            version_f_id.append(v_id[1:])
        version_dict = dict(zip(version, version_f_id))
        v_name = version_parse.xpath('//div[contains(@class,"comic-info")]/h1/text()')[0]
        print(f'你选择的漫画【{v_name}】有以下版本可以选择：')
        for version_title in version:
            print(f'{version_dict[version_title]}=>{version_title}')
        print('*' * 74)
        select_ver_num = (input('请输入版本序号：'))
        version_url = version_parse.xpath(f'//div[@id="{select_ver_num}"]//li/a/@href')
        if not version_url:
            print(f'==>【{v_name}】已下架，请搜索其他资源！')
            print('-' * 74)
            await self.main()
        else:
            final_url = 'https://www.manhuadb.com' + version_url[0]
            return final_url

    async def cha_url_parse(self, c_html):
        c_url_list = []
        c_parse = etree.HTML(c_html)
        c_urls = c_parse.xpath('//ol[contains(@class,"links-of-books")]/li/a/@href')
        for url in c_urls:
            c_full_url = self.base_url + url
            c_url_list.append(c_full_url)

        return c_url_list

    async def page_s(self, c_url):
        async with aiohttp.ClientSession() as client:
            async with client.get(c_url, headers=headers) as resp:
                if resp.status == 200:
                    p_html = await resp.text()
                    comic_name_re = re.compile('<h1 class="h2 text-center mt-3 ccdiv-m"><a href=".*?">(.*?)</a></h1>',
                                               re.S)
                    comic_name = re.findall(comic_name_re, p_html)[0]
                    title_recompile = re.compile(
                        '<a href="/manhua/.*?">(.*?)</a> / 第 <span class="c_nav_page">\d+</span> 页・共 \d+ 页')
                    page_num_recompile = re.compile(
                        '<a href="/manhua/.*?">.*?</a> / 第 <span class="c_nav_page">\d+</span> 页・共 (\d+) 页')

                    title = re.findall(title_recompile, p_html)[0]
                    page_num = re.findall(page_num_recompile, p_html)[0]
                    tasks = []
                    for num in range(1, int(page_num) + 1):
                        c_p_url = f'{c_url[:-5]}p{num}{c_url[-5:]}'
                        c_p_html = await self.get_url(c_p_url)
                        img_name_re = re.compile(
                            '<img class="img-fluid show-pic" src="https://i\d+.manhuadb.com/.*?/.*?/.*?/(.*?)" />',
                            re.S)
                        img_name = re.findall(img_name_re, c_p_html)[0]
                        pic_recompile = re.compile('<img class="img-fluid show-pic" src="(.*?)" />', re.S)
                        src = re.findall(pic_recompile, c_p_html)[0]
                        img_c = await self.img_parse(src)
                        task = asyncio.create_task(self.write_img(comic_name, title, img_name, img_c))
                        tasks.append(task)
                    await asyncio.wait(tasks)

    async def write_img(self, comic_name, title, img_name, img_c):
        if not os.path.exists(comic_name + '/' + title):
            os.makedirs(comic_name + '/' + title)
            async with aiofiles.open(comic_name + '/' + title + '/' + img_name, 'wb') as f:
                print('正在下载：' + title + '/' + img_name)
                await f.write(img_c)
        else:
            if os.path.exists(comic_name + '/' + title + '/' + img_name):
                print(f'{img_name}已存在，忽略下载！！！')
            else:
                async with aiofiles.open(comic_name + '/' + title + '/' + img_name, 'wb') as f:
                    print('正在下载：' + title + '/' + img_name)
                    await f.write(img_c)
        self.total_num += 1

    async def img_parse(self, img_url):
        async with aiohttp.ClientSession() as client:
            async with client.get(img_url, headers=headers) as resp:
                if resp.status == 200:
                    img_content = await resp.read()
                    return img_content

    async def main(self):
        offset = f'https://www.manhuadb.com/search?q={input("请输入漫画名/作者:")}'
        html_s = await self.get_url(offset)
        all_search_url = await self.page_num_parse(html_s)
        print('搜索到以下结果：')
        print('*' * 74)
        for url in all_search_url:
            search_page_html = await self.get_url(url)
            await self.parse_html(search_page_html)
        print('*' * 74)
        select_num = int(input('请输入要下载的漫画序号：'))
        start_time = time.time()
        print('资源序号已选择，开始解析！')
        for k, v in self.index_dict.items():
            if select_num == k:
                select_comic_html = await self.get_url(v)
                comic_url = await self.comic_parse(select_comic_html)
                comic_html = await self.get_url(comic_url)
                url_list = await self.cha_url_parse(comic_html)
                print('URL解析完毕，获取所有漫画页面资源中···！')
                tasks = [asyncio.create_task(self.page_s(url)) for url in url_list]
                print('漫画图片获取成功，开始下载···')
                print('*' * 74)
                await asyncio.wait(tasks)
        end_time = time.time()
        print(f'下载完成！！！本次下载漫画图片{self.total_num}张，共耗时：{end_time - start_time}秒。')


spy = manhuadb()

print('=====程序开始执行=====')
asyncio.run(spy.main())
