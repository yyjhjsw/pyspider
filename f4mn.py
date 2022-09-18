import aiofiles
import aiohttp
import asyncio
from lxml import etree
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"}

async def get_url(session,url):
    async with session.get(url,headers=headers) as resp:
        if resp.status==200:
            res = await resp.text()
            return res


async def htmlParsh(html):
    htmlPs = etree.HTML(html)
    chaTitles = htmlPs.xpath('//img[@class="item-img"]/@alt')
    chaUrls = htmlPs.xpath('//a[@class="item-link"]/@href')
    for i in chaUrls:
        print(i)
    nextPageUrl = htmlPs.xpath('//li[@class="page-item"]/a[@rel="next"]/@href')
    if not nextPageUrl:
        print("所有页面索引完毕！")
        return      
    else:
        await main(nextPageUrl[0])



async def main(offset):
    async with aiohttp.ClientSession() as session:
        html = await get_url(session,offset)
        await htmlParsh(html)

offset=f'https://www.f4mn.com/search.html?s=小热巴'
asyncio.run(main(offset))