"""示例 stdio MCP 服务，提供可发现、可调用的加法工具。"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("CLI Demo")


@server.tool()
def add(a: int, b: int) -> int:
    """返回两个整数的和。"""
    return a + b


if __name__ == "__main__":
    server.run(transport="stdio")
