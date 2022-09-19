import aiofiles
import aiohttp
import asyncio
from lxml import etree
import uvloop
import re
import os

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"}

async def get_url(session,url):
    async with session.get(url,headers=headers) as resp:
        if resp.status==200:
            res = await resp.text()
            return res


async def htmlParsh(sem,session,html):
    async with sem:
        htmlPs = etree.HTML(html)
        # chaTitles = htmlPs.xpath('//img[@class="item-img"]/@alt')
        chaUrls = htmlPs.xpath('//a[@class="item-link"]/@href')
        tasks = []
        for url in chaUrls:
            task = asyncio.create_task(imgParse(session,url))
            tasks.append(task)
        nextPageUrl = htmlPs.xpath('//li[@class="page-item"]/a[@rel="next"]/@href')
        if not nextPageUrl:
            await asyncio.wait(tasks)
            print("所有页面索引完毕！")    
            return      
        else:
            await main(nextPageUrl[0])

async def imgParse(session,url):
    imgHtml = await get_url(session,url)
    htmlPs = etree.HTML(imgHtml)
    iTitle = htmlPs.xpath('//h1[@class="post-title"]/text()')[0]
    imgUrls = htmlPs.xpath('//div[@data-fancybox="gallery"]/img/@data-src')
    tasks=[]
    for url in imgUrls:
        urlSplit = url.split("/")
        imgName = urlSplit[-1]
        imgContent = await getImg(session,url)
        task = asyncio.create_task(writeImg(iTitle,imgName,imgContent),name=f'{iTitle}-{imgName}')
        tasks.append(task)
    await asyncio.wait(tasks)


async def writeImg(ititle,imgname,imgcontent):
    downloadPath ="/home/yin/download/pyspider"
    if not os.path.exists(downloadPath + '/' + keyword + '/' + ititle):
        os.makedirs(downloadPath + '/' + keyword + '/' + ititle)
        async with aiofiles.open(downloadPath + '/' + keyword + '/' + ititle + '/' + imgname, 'wb') as f:
            print('正在下载：' + ititle + '/' + imgname)
            await f.write(imgcontent)
    else:
        if os.path.exists(downloadPath + '/' + keyword + '/' + ititle + '/' + imgname):
            print(f'{imgname}已存在，忽略下载！！！')
        else:
            async with aiofiles.open(downloadPath + '/' + keyword + '/' + ititle + '/' + imgname, 'wb') as f:
                print('正在下载：' + ititle + '/' + imgname)
                await f.write(imgcontent)


async def getImg(session,imgurl):
    async with session.get(imgurl,headers=headers) as resp:
        if resp.status == 200:
            imgContent = await resp.read()
            return imgContent




async def main(offset):
    sem = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        html = await get_url(session,offset)
        await htmlParsh(sem,session,html)


keyword = input("请输入要搜索的关键字:")
offset=f'https://www.f4mn.com/search.html?s={keyword}'
asyncio.run(main(offset))