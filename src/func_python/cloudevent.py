import asyncio
import logging
import os
import signal
import hypercorn.config
import hypercorn.asyncio

from cloudevents.http import from_http, CloudEvent
from cloudevents.conversion import to_structured, to_binary
from cloudevents.exceptions import MissingRequiredFields, InvalidRequiredFields

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
    """ ASGIApplication is a wrapper around a Function instance which 
    exposes it as an ASGI Application. 
    """
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

        logging.info(f"function starting on {cfg.bind}")
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
            logging.debug("function does not implement 'start'. Skipping.")

    async def on_stop(self):
        if hasattr(self.f, "stop"):
            self.f.stop()
        else:
            logging.debug("function does not implement 'stop'. Skipping.")
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
                # CloudEvents Middleware
                # Currently the http and cloudevents middleware implementations
                # are identical with the exception of this section which
                # reads the request as a CloudEvent and adds it to the scope,
                # and sends a response CloudEvent if returned.
                # Should this implementation prove adequate, we can combine
                # into a single middleware with a swithch to enable this
                # interstitial encode/decode, and thus avoid the approx. 200
                # lines of shared server boilerplate.
                #
                try:
                    # Decode the event and make it available in the scope
                    scope["event"] = await decode_event(scope, receive)
                    # Wrap the sender in a CloudEventSender
                    send = CloudEventSender(send)
                    # Delegate processing to user's Function
                    await self.f.handle(scope, receive, send)
                except (MissingRequiredFields, InvalidRequiredFields) as e:
                    # Log the non-CloudEvent request for debugging
                    logging.warning(f"Received non-CloudEvent request: {scope['method']} {scope['path']}")
                    headers_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in scope.get('headers', [])}
                    logging.debug(f"Request headers: {headers_dict}")
                    
                    # Return 400 Bad Request for non-CloudEvent requests
                    await send({
                        'type': 'http.response.start',
                        'status': 400,
                        'headers': [[b'content-type', b'text/plain']]
                    })
                    await send({
                        'type': 'http.response.body',
                        'body': b'Bad Request: This endpoint expects CloudEvent requests. '
                    })
                    return
        except Exception as e:
            # For other unexpected errors, try to send a CloudEvent error response
            # But check if send is already a CloudEventSender
            if hasattr(send, 'structured'):
                await send_exception_cloudevent(send, 500, f"Error: {e}")
            else:
                # Fallback to plain HTTP error
                logging.error(f"Unexpected error: {e}")
                await send_exception(send, 500, f"Internal Server Error: {e}".encode())

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


async def decode_event(scope, receive):
    body = await receive_body(receive)
    headers = {
        k.decode("utf-8").lower(): v.decode("utf-8")
        for k, v in scope.get("headers", [])
    }
    return from_http(headers, body)


async def receive_body(receive):
    """For CloudEvents: receive the body and return it as bytes"""
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body


async def send_exception(send, code, message):
    await send({
        'type': 'http.response.start', 'status': code,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body', 'body': message,
    })


async def send_exception_cloudevent(send, status, message):
    attributes = {
        "type": "dev.functions.error",
        "source": "/cloudevent/error",
    }
    data = {"message": message}

    # Check if send is a CloudEventSender with structured method
    if hasattr(send, 'structured'):
        await send.structured(CloudEvent(attributes, data), status)
    else:
        # Fallback to plain HTTP error response if send is not a CloudEventSender
        logging.warning("send_exception_cloudevent called with non-CloudEventSender, falling back to HTTP response")
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [[b'content-type', b'application/json']]
        })
        import json
        error_body = json.dumps({"error": {"message": message, "type": "dev.functions.error"}})
        await send({
            'type': 'http.response.body',
            'body': error_body.encode()
        })


class CloudEventSender:
    """A sender which supports CloudEvents"""

    def __init__(self, send):
        self._send = send

    async def __call__(self, event, status: int = 200):
        """default send assumes a strcutred event"""
        await self.structured(event, status)

    async def structured(self, event, status=200):
        """send as a structured cloudevent"""
        headers, body = to_structured(event)
        await self._send_encoded_cloudevent(headers, body, status)

    async def binary(self, event, status=200):
        """send as a binary cloudevent"""
        headers, body = to_binary(event)
        await self._send_encoded_cloudevent(headers, body, status)

    async def http(self, message):
        """Send a raw http response, bypassing the automatic cloudevent
        encoding.  Use this for more granular control of the response."""
        await self._send(message)

    async def _send_encoded_cloudevent(self, headers, body, status=200):
        """Send the given cloudevent headers and body."""
        headers = [
            (k.encode(), v.encode())
            for k, v in headers.items()
        ] + [(b"content-length", str(len(body)).encode())]

        await self._send({
            "type": "http.response.start",
            "status": status,
            "headers": headers
        })

        await self._send({
            "type": "http.response.body",
            "body": body,
        })
