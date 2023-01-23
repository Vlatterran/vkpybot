import aiohttp


async def get(url, params):
    async with aiohttp.ClientSession() as session:
        # proxy='http://proxy.server:3128'
        async with session.get(url, params=params) as resp:
            return await resp.json()


