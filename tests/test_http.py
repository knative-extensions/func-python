import httpx
import logging
import os
import signal
import threading
import time
from func_python.http import serve

logging.basicConfig(level=logging.INFO)

# Set a dynamic test URL using an environment variable
os.environ["LISTEN_ADDRESS"] = os.getenv("LISTEN_ADDRESS", "127.0.0.1:8081")
# Retrieve the LISTEN_ADDRESS for use in the tests
LISTEN_ADDRESS = os.getenv("LISTEN_ADDRESS")

def test_static():
    """
    ensures that a user function developed using the default "static"
    style (method signature) is served by the middleware.
    """

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
    # Run async, this attempts to contact the running function and confirm the
    # handle method was successfully served.
    def test():
        for i in range(10):
            time.sleep(0.5)
            if i == 10:
                logging.info("server did not start")
                return
            try:
                httpx.get(f"http://{LISTEN_ADDRESS}")
                break
            except httpx.ConnectError:
                logging.info("... retrying server.")
                continue

        # Test that the handler was served
        try:
            response = httpx.get(f"http://{LISTEN_ADDRESS}")
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

def test_instanced():
    """
    ensures that a user function developed using the default "instanced"
    style is served by the middleware
    """

    # User Function
    # An example standard "instanced" function (user's Function) which is
    # exposed on the network as an ASGI service by the middleware.
    class MyFunction:
        async def __call__(self, scope, receive, send):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': 'test_instanced OK'.encode(),
            })

    def new():
        return MyFunction()

    # Tests
    # Attempts to contact the running function and confirm the user's function
    # was instantiated and served.
    def test():
        for i in range(10):
            time.sleep(0.5)
            if i == 10:
                logging.info("server did not start")
                return
            try:
                httpx.get(f"http://{LISTEN_ADDRESS}")
                break
            except httpx.ConnectError:
                logging.info("... retrying server.")
                continue

        # Test that the handler was served
        try:
            response = httpx.get(f"http://{LISTEN_ADDRESS}")
            assert response.status_code == 200
            assert response.text == "test_instanced OK"
        finally:
            # Signal the main thread to shut down the server
            os.kill(os.getpid(), signal.SIGINT)

    # Start the test loop asynchronously
    test_thread = threading.Thread(target=test)
    test_thread.start()

    # Serve the handle function
    try:
        serve(new)
    except KeyboardInterrupt:
        logging.info("signal received")

    test_thread.join(timeout=5)

def test_signal_handling():
    """
    Tests that the server gracefully shuts down when receiving a SIGINT signal.
    """
    # Example minimal ASGI app
    async def handle(scope, receive, send):
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Signal Handling OK',
        })

    # Function to send a SIGINT after a delay
    def send_signal():
        time.sleep(2)  # Allow server to start
        os.kill(os.getpid(), signal.SIGINT)

    # Start signal sender in a separate thread
    signal_thread = threading.Thread(target=send_signal)
    signal_thread.start()

    # Serve the function
    try:
        serve(handle)
    except KeyboardInterrupt:
        logging.info("SIGINT received and handled gracefully.")

    signal_thread.join(timeout=5)
