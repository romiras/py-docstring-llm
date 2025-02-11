from os import environ
from time import sleep
import re
from mistralai import Mistral
import redis.asyncio as redis

class LlmClient:
    MODEL_NAME = "codestral-2405"
    REQUEST_DELAY_SECONDS = 0.5 # to prevent 429 Too Many Requests
    DOCUMENTATION_PROMPT = """
Write a comprehensive documentation for the following Python function, following the guidelines of PEP 257:

{function_code}

The documentation should include:
- A brief one-line summary of the function's purpose
- A detailed description of what the function does
- Descriptions of the function's parameters and their types
- Descriptions of the function's return value and its type
- Any relevant examples or usage notes

Documentation:
"""

    client: Mistral
    redis_client: redis.Redis

    def __init__(self, redis_client: redis.Redis) -> None:
        api_key = environ["MISTRAL_API_KEY"]
        if api_key is None:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        self.client = Mistral(api_key=api_key)
        self.redis_client = redis_client

    async def get_stub_summary(self, function_name: str, function_code: str) -> str:
        return function_name

    async def get_summary(self, function_name: str, function_code: str) -> str:
        summary = await self._cached_summary(function_name=function_name)
        if summary is not None:
            return summary

        prompt = self.DOCUMENTATION_PROMPT.format(function_code=function_code)
        sleep(self.REQUEST_DELAY_SECONDS)

        response = self.client.fim.complete(
            model=self.MODEL_NAME,
            prompt=prompt,
            temperature=0,
            top_p=1,
        )

        summary = response.choices[0].message.content.strip()
        await self._store_summary(function_name=function_name, summary=summary)

        return summary

    def sanitize_summary(self, text: str) -> str:
        """
        Removes the following lines from the input text:
        - Three consecutive backticks, optionally followed by "python"
        - Three consecutive doublequotes
        
        Args:
            text (str): The input text to be sanitized.
        
        Returns:
            str: The sanitized text.
        """
        # Remove lines with three consecutive backticks, optionally followed by "python"
        text = re.sub(r'^`{3}(?:python)?\s*\n', '', text, flags=re.MULTILINE)

        text = re.sub(r'^`{3}$', '', text, flags=re.MULTILINE)

        # Remove lines with `"""`
        text = re.sub(r'^"{3}\s*\n', '', text, flags=re.MULTILINE)

        return text

    async def _cached_summary(self, function_name: str) -> str | None:
        key_name = self._key_name(function_name)
        return await self.redis_client.get(name=key_name)

    async def _store_summary(self, function_name: str, summary: str) -> None:
        key_name = self._key_name(function_name)
        await self.redis_client.set(name=key_name, value=summary, ex=3600)

    def _key_name(self, function_name: str) -> str:
        return f"py-llm-doc:{function_name}"
