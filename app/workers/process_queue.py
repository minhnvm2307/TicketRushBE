import asyncio


async def process_queues_job():
    while True:
        await asyncio.sleep(60)
