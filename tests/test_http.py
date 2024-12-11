import httpx
import logging
import os
import signal
import threading
import time
from func_python.http import serve

logging.basicConfig(level=logging.INFO)


def test_static():
    # Functoin
    # An example minimal "static" user function which will be
    # exposed on the network as an ASGI service by the middleware.
    async def handle(scope, receive, send):
        logging.info("Handler Invoked")
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': 'test_static OK'.encode(),
        })

    # Test
    # Run async, this attempts to contact the running functon and confirm the
    # handle method was successfully served.
    def test():
        for i in range(10):
            time.sleep(0.5)
            if i == 10:
                logging.info("server did not start")
                return
            try:
                httpx.get("http://127.0.0.1:8080")
                break
            except httpx.ConnectError:
                logging.info("... retrying server.")
                continue

        # Test that the handler was served
        try:
            response = httpx.get("http://127.0.0.1:8080")
            assert response.status_code == 200
            assert response.text == "test_static OK"
        finally:
            # Signal the main thread to shut down the server
            os.kill(os.getpid(), signal.SIGINT)

    # Start the test loop asynchronously
    test_thread = threading.Thread(target=test)
    test_thread.start()

    # Serve the handle function
    try:
        serve(handle)
    except KeyboardInterrupt:
        logging.info("signal received")

    test_thread.join(timeout=5)
