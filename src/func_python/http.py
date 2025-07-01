# ASGI main
import asyncio
import logging
import os
import signal
import hypercorn.config
import hypercorn.asyncio

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LISTEN_ADDRESS = "[::]:8080"

logging.basicConfig(level=DEFAULT_LOG_LEVEL)


def serve(f):
    """serve a function f by wrapping it in an ASGI web application
    and starting.  The function can be either a constructor for a functon
    instance (named "new") or a simple ASGI handler function (named "handle").
    """
    logging.debug("func runtime creating function instance")

    if f.__name__ == 'new':
        return ASGIApplication(f()).serve()
    elif f.__name__ == 'handle':
        try:
            return ASGIApplication(DefaultFunction(f)).serve()
        except Exception as e:
            logging.error(f"Server failed to start: {e}")
            raise
    else:
        raise ValueError("function must be either be a constructor 'new' or a "
                         "handler function 'handle'.")


class DefaultFunction:
    """DefaultFunction is used when the provided functon is not a constructor
    for a Function instance, but rather a simple handler function"""

    def __init__(self, handler):
        self.handle = handler

    async def handle(self, scope, receive, send):
        # delegate to the handler implementation provided during construction.
        await self.handle(scope, receive, send)


class ASGIApplication():
    def __init__(self, f):
        self.f = f
        self.stop_event = asyncio.Event()
        if hasattr(self.f, "handle") is not True:
            raise AttributeError("Function must implement a 'handle' method.")

        # Inform the user via logs that defaults will be used for health
        # endpoints if no matchin methods were provided.
        if hasattr(self.f, "alive") is not True:
            logging.info(
                "function does not implement 'alive'. Using default "
                "implementation for liveness checks."
            )

        if hasattr(self.f, "ready") is not True:
            logging.info(
                "function does not implement 'ready'. Using default "
                "implementation for readiness checks."
            )

    def serve(self):
        """serve serving this ASGIhandler, delegating implementation of
           methods as necessary to the wrapped Function instance"""
        cfg = hypercorn.config.Config()
        cfg.bind = [os.getenv('LISTEN_ADDRESS', DEFAULT_LISTEN_ADDRESS)]

        logging.debug(f"function starting on {cfg.bind}")
        return asyncio.run(self._serve(cfg))

    async def _serve(self, cfg):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self._handle_signal)
        loop.add_signal_handler(signal.SIGTERM, self._handle_signal)

        await hypercorn.asyncio.serve(self, cfg)

    def _handle_signal(self):
        logging.info("Signal received: initiating shutdown")
        self.stop_event.set()

    async def on_start(self):
        """on_start handles the ASGI server start event, delegating control
           to the internal Function instance if it has a "start" method."""
        if hasattr(self.f, "start"):
            self.f.start(os.environ.copy())
        else:
            logging.info("function does not implement 'start'. Skipping.")

    async def on_stop(self):
        if hasattr(self.f, "stop"):
            self.f.stop()
        else:
            logging.info("function does not implement 'stop'. Skipping.")
        self.stop_event.set()

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await self.on_start()
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await self.on_stop()
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
                else:
                    break

        # Assert request is HTTP
        if scope["type"] != "http":
            await send_exception(send, 400,
                                 "Functions currently only support ASGI/HTTP "
                                 f"connections. Got {scope['type']}"
                                 )
            return

        # Route request
        try:
            if scope['path'] == '/health/liveness':
                await self.handle_liveness(scope, receive, send)
            elif scope['path'] == '/health/readiness':
                await self.handle_readiness(scope, receive, send)
            else:
                await self.f.handle(scope, receive, send)
        except Exception as e:
            await send_exception(send, 500, f"Error: {e}")

    async def handle_liveness(self, scope, receive, send):
        alive = True
        message = "OK"
        if hasattr(self.f, "alive"):
            result = self.f.alive()
            # The message return is optional
            if isinstance(result, tuple):
                alive, message = result
            else:
                alive = result

        if alive:
            await send({'type': 'http.response.start', 'status': 200,
                        'headers': [[b'content-type', b'text/plain']]})
        else:
            await send({'type': 'http.response.start', 'status': 500,
                        'headers': [[b'content-type', b'text/plain']]})

        await send({'type': 'http.response.body',
                    'body': f'{message}'.encode('utf-8'),
                    })

    async def handle_readiness(self, scope, receive, send):
        ready = True
        message = "OK"
        if hasattr(self.f, "ready"):
            result = self.f.ready()
            # The message return is optional
            if isinstance(result, tuple):
                ready, message = result
            else:
                ready = result

        if ready:
            await send({'type': 'http.response.start', 'status': 200,
                        'headers': [[b'content-type', b'text/plain']]})
        else:
            await send({'type': 'http.response.start', 'status': 500,
                        'headers': [[b'content-type', b'text/plain']]})

        await send({'type': 'http.response.body',
                    'body': f'{message}'.encode('utf-8'),
                    })


async def send_exception(send, code, message):
    await send({
        'type': 'http.response.start', 'status': code,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body', 'body': message,
    })
