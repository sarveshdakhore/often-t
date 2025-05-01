from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("often")


@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


@mcp.resource("greetings://{name}")
def get_greeting(name: str) -> str:
    """
    Get a greeting message.
    """
    return f"Hello, {name}!"






if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
