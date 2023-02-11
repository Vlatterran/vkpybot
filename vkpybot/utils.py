import argparse

import aiohttp


async def get(url, params):
    async with aiohttp.ClientSession() as session:
        # proxy='http://proxy.server:3128'
        async with session.get(url, params=params) as resp:
            return await resp.json()


# Source: https://stackoverflow.com/a/53284255
class StoreDict(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        kv = {}
        if not isinstance(values, (list,)):
            values = (values,)
        for value in values:
            n, v = value.split('=')
            kv[n] = v
        setattr(namespace, self.dest, kv)
