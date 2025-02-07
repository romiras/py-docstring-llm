import ast
from .llm_client import LlmClient
import redis.asyncio as redis

class CodeParser:
    file_path: str
    llm_client: LlmClient

    def __init__(self, file_path: str, redis_client: redis.Redis) -> None:
        self.file_path = file_path
        self.llm_client = LlmClient(redis_client=redis_client)

    async def add_docstrings_to_file(self: str) -> None:
        with open(self.file_path, 'r') as file:
            source = file.read()

        tree = ast.parse(source)
        new_tree = await self.update_docstrings(tree)
        new_source = ast.unparse(new_tree)

        with open(self.file_path+"~new", 'w') as file:
            file.write(new_source)

    async def update_docstrings(self, tree: ast.Module) -> ast.Module:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node) is None:
                    # Generate a summary for the function using the codestral-latest LLM

                    # summary = await self.llm_client.get_stub_summary(function_name=node.name, function_code=ast.unparse(node))
                    summary = await self.llm_client.get_summary(function_name=node.name, function_code=ast.unparse(node))

                    # Add the summary as a docstring to the function definition
                    new_docstring = f'"""{self.llm_client.sanitize_summary(summary)}"""'

                    try:
                        parsed = ast.parse(ast.parse(new_docstring))
                        node.body.insert(0, parsed.body[0])
                    except SyntaxError as e:
                        print(f"Error: {e.msg} in {node.name}")

        return tree
