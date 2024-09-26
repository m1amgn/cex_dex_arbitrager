import asyncio
from find_spread import find_spread


async def main():
    await find_spread("2")

if __name__ == "__main__":
    asyncio.run(main())
