from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import re

class ReadWriteLock:
    def __init__(self):
        self._readers = 0
        self._writer_lock = asyncio.Lock()
        self._readers_lock = asyncio.Lock()
        self._no_readers = asyncio.Event()
        self._no_readers.set()

    async def acquire_read(self):
        async with self._readers_lock:
            self._readers += 1
            if self._readers == 1:
                await self._writer_lock.acquire()
            self._no_readers.clear()

    async def release_read(self):
        async with self._readers_lock:
            self._readers -= 1
            if self._readers == 0:
                self._writer_lock.release()
                self._no_readers.set()

    async def acquire_write(self):
        await self._writer_lock.acquire()
        await self._no_readers.wait()

    def release_write(self):
        self._writer_lock.release()


rw_lock = ReadWriteLock()

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Se quiser bloquear somente endpoints que escrevem CSV:
WRITE_PATHS = [
    r"/departments.*",
    r"/employees.*",
    r"/pay_rolls.*"
]

def is_write_request(request: Request):
    if request.method in WRITE_METHODS:
        return True

    path = request.url.path
    return any(re.match(pattern, path) for pattern in WRITE_PATHS)


class ConcurrencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if is_write_request(request):
            # Bloqueio exclusivo
            await rw_lock.acquire_write()
            try:
                response = await call_next(request)
            finally:
                rw_lock.release_write()
        else:
            # Leitura simultânea permitida
            await rw_lock.acquire_read()
            try:
                response = await call_next(request)
            finally:
                await rw_lock.release_read()

        return response
