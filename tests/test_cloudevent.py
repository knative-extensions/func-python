import httpx
import json
import logging
import os
import signal
import threading
import time
import uuid
import pytest
from func_python.cloudevent import serve
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent

logging.basicConfig(level=logging.INFO)

# Set a dynamic test URL using an environment variable
os.environ["LISTEN_ADDRESS"] = os.getenv("LISTEN_ADDRESS", "127.0.0.1:8081")

# Retrieve the LISTEN_ADDRESS for use in the tests
LISTEN_ADDRESS = os.getenv("LISTEN_ADDRESS")


def test_static():
    """
    A basic test which ensures that serving a static "handle" method
    succeeds without failure.
    """

    # Function
    # An example minimal "static" user function which will be
    # exposed on the network as an ASGI service by the middleware.
    async def handle(scope, receive, send):
        # Ensure that the scope contains the CloudEvent
        if "event" not in scope:
            await send(CloudEvent({}, {"message": "no event in scope"}), 500)

        attributes = {
            "type": "com.example.teststatic",
            "source": "https://example.com/event-producer",
        }
        content = {"message": "OK test_static"}

        # The default send encodes the cloudevent using to_structured.
        # use send.binary to send it binary encoded, or send.http to use
        # the raw ASGI response object without CloudEvent middleware.
        await send(CloudEvent(attributes, content))

    # Test
    # Run async, this attempts to contact the running function and confirm the
    # handle method was successfully served.
    test_complete = threading.Event()
    test_results = {"success": False, "error": None}

    def test():
        try:
            wait_for_function()  # to become available

            # Send a CloudEvent to the Function
            attributes = {
                "type": "com.example.test-static",
                "source": "https://example.com/event-producer",
            }
            data = {"message": "test_static"}
            headers, content = to_structured(CloudEvent(attributes, data))
            response = httpx.post(
                f"http://{LISTEN_ADDRESS}",
                headers=headers,
                content=content
            )

            # Assertions
            assert response.status_code == 200
            response_event = json.loads(response.text)
            assert response_event["data"]["message"] == "OK test_static"
            test_results["success"] = True
        except Exception as e:
            test_results["error"] = str(e)
        finally:
            test_complete.set()  # signal test completion
            os.kill(os.getpid(), signal.SIGINT)  # gracefully term Function

    # Start the test loop asynchronously
    test_thread = threading.Thread(target=test)
    test_thread.daemon = True  # exit when test does
    test_thread.start()

    # Serve the handle function
    # Note this will fail if not in the main thread due to "set_wakeup_fd"
    serve(handle)

    if not test_complete.wait(10):
        pytest.fail("Test timed out")

    if not test_results["success"]:
        pytest.fail(test_results["error"] or "Test failed")


def test_instanced():
    """
    ensures that a user function developed using the default "instanced"
    style is served by the middleware
    """

    # User Function
    # An example standard "instanced" function (user's Function) which is
    # exposed on the network as an ASGI service by the middleware.
    class MyFunction:
        async def handle(self, scope, receive, send):
            # Check if this is a CloudEvent
            if "event" not in scope:
                await send(CloudEvent({},{"message": "no event in scope"}), 500)

            attributes = {
                "type": "com.example.testinstanced",
                "source": "https://example.com/event-producer",
            }
            content = {"message": "OK test_instanced"}

            # The default send encodes the cloudevent using to_structured.
            # use send.binary to send it binary encoded, or send.http to use
            # the raw ASGI response object without CloudEvent middleware.
            await send(CloudEvent(attributes, content))

    def new():
        return MyFunction()

    # Tests
    # Attempts to contact the running function and confirm the user's function
    # was instantiated and served.
    test_complete = threading.Event()
    test_results = {"success": False, "error": None}

    def test():
        try:
            wait_for_function()  # to become available

            # Send a CloudEvent to the Function
            attributes = {
                "type": "com.example.test-static",
                "source": "https://example.com/event-producer",
            }
            data = {"message": "test_instanced"}
            headers, content = to_structured(CloudEvent(attributes, data))
            response = httpx.post(
                f"http://{LISTEN_ADDRESS}",
                headers=headers,
                content=content
            )

            # Assertions
            assert response.status_code == 200
            response_event = json.loads(response.text)
            assert response_event["data"]["message"] == "OK test_instanced"
            test_results["success"] = True
        except Exception as e:
            test_results["error"] = str(e)
        finally:
            test_complete.set()  # signal test completion
            os.kill(os.getpid(), signal.SIGINT)  # gracefully term Function

    # Start the test loop asynchronously
    test_thread = threading.Thread(target=test)
    test_thread.daemon = True  # exit when test does
    test_thread.start()

    # Serve the Function
    serve(new)

    if not test_complete.wait(10):
        pytest.fail("Test timed out")

    if not test_results["success"]:
        pytest.fail(test_results["error"] or "Test failed")


def test_signal_handling():
    """
    Tests that the server gracefully shuts down when receiving a SIGINT signal.
    """
    # Example minimal ASGI app that handles CloudEvents
    async def handle(scope, receive, send):
        # For the signal handling test, we just need the server to start
        # and then shut down gracefully, so we keep the handler simple
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


class FunctionNotAvailableError(Exception):
    """ Raised when a Function is not available """


def wait_for_function():
    max_retries = 20
    for i in range(max_retries):
        time.sleep(0.5)
        try:
            httpx.get(f"http://{LISTEN_ADDRESS}/health/liveness")
            break
        except httpx.ConnectError:
            logging.info(f"Retrying ({i+1}/{max_retries})...")
            if i >= max_retries:
                raise FunctionNotAvailableError(f"Function at {LISTEN_ADDRESS} did not start after {max_retries} attempts")
