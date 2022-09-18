from email import header
from signal import sigwait
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
    print(htmlPs)


async def main():
    offset = f'https://www.f4mn.com/search.html?s={input("请输入搜索关键字：")}'
    async with aiohttp.ClientSession() as session:
        html = await get_url(session,offset)
        await htmlParsh(html)


asyncio.run(main())