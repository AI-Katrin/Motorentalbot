import asyncio
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

async def test_proxy():
    proxy = "socks5://43.157.34.94:1777"
    connector = ProxyConnector.from_url(proxy)
    async with ClientSession(connector=connector) as session:
        async with session.get('https://api.ipify.org?format=json') as response:
            print(await response.text())

if __name__ == "__main__":
    asyncio.run(test_proxy())
