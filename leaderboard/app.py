import asyncio
from typing import AsyncGenerator, List

import strawberry
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from strawberry.asgi import GraphQL
import uvicorn
from pathlib import Path


import strawberry
import asyncio
import asyncio.subprocess as subprocess
from asyncio import streams
from typing import Any, AsyncGenerator, AsyncIterator, Coroutine, Optional


async def wait_for_call(coro: Coroutine[Any, Any, bytes]) -> Optional[bytes]:
    """
    wait_for_call calls the supplied coroutine in a wait_for block.

    This mitigates cases where the coroutine doesn't yield until it has
    completed its task. In this case, reading a line from a StreamReader; if
    there are no `\n` line chars in the stream the function will never exit
    """
    try:
        return await asyncio.wait_for(coro(), timeout=0.1)
    except asyncio.TimeoutError:
        pass


async def lines(stream: streams.StreamReader) -> AsyncIterator[str]:
    """
    lines reads all lines from the provided stream, decoding them as UTF-8
    strings.
    """
    while True:
        b = await wait_for_call(stream.readline)
        if b:
            yield b.decode("UTF-8").rstrip()
        else:
            break


async def exec_proc(port: int) -> subprocess.Process:
    """
    exec_proc starts a sub process and returns the handle to it.
    """
    return await asyncio.create_subprocess_exec(
        "nc",
        "localhost",
        f"{port}",
        stdout=subprocess.PIPE,
    )


async def tail(proc: subprocess.Process) -> AsyncGenerator[str, None]:
    """
    tail reads from stdout until the process finishes
    """
    # Note: race conditions are possible here since we're in a subprocess. In
    # this case the process can finish between the loop predicate and the call
    # to read a line from stdout. This is a good example of why you need to
    # be defensive by using asyncio.wait_for in wait_for_call().
    while proc.returncode is None:
        async for l in lines(proc.stdout):
            yield l
    else:
        # read anything left on the pipe after the process has finished
        async for l in lines(proc.stdout):
            yield l
    print("Process finished")

@strawberry.type
class User:
    name: str
    age: int

@strawberry.type
class NewScore:
    id: int
    score: int
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)

    @strawberry.subscription
    async def newScore(self, target: int = 100) -> AsyncGenerator[List[NewScore], None]:
        for i in range(target):
            random_leaderboard = [
                NewScore(id=j, score=j, name="Patrick " + str(i))
                for j in range(target)
            ]
            yield random_leaderboard
            await asyncio.sleep(0.5)

    @strawberry.subscription
    async def run_command(self, port: int = 9999) -> AsyncGenerator[str, None]:
        proc = await exec_proc(port)
        return tail(proc)


schema = strawberry.Schema(query=Query, subscription=Subscription)

graphql_app = GraphQL(schema)

app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

# Add static file
static_path = Path(__file__).parent / "static"
# Mount static files index
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

# main
if __name__ == "__main__":
    uvicorn.run("leaderboard.app:app", host="0.0.0.0", port=8000, debug=True, reload=True, workers=2)
