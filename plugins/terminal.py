import asyncio
from fastmcp.server import FastMCP


def setup(server: FastMCP) -> None:
    @server.tool(name="terminal", description="Run a shell command on the host")
    async def terminal(cmd: str) -> str:
        """Execute a command on the host system and return its output."""
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()
