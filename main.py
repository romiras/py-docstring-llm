import os
from sys import argv
import asyncio
import redis.asyncio as redis
from code_parser import CodeParser

async def main(file_path: str) -> None:
    redis_client = setup_redis()
    await redis_client.ping()

    parser = CodeParser(file_path=file_path, redis_client=redis_client)
    await parser.add_docstrings_to_file()
    print(f'Docstrings added to {file_path}')

def setup_redis() -> redis.Redis:
    redis_url = 'redis://localhost:6379/0' # os.getenv('REDIS_URL', 'Redis URL')
    return redis.from_url(redis_url, decode_responses=True)

if __name__ == "__main__":
    file_path = argv[1]
    if not os.path.exists(file_path):
        print(f'File {file_path} does not exist.')
        exit(code=1)

    asyncio.run(main(file_path=file_path))
