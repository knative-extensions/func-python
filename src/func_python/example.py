from typing import Dict, Any, Callable, Awaitable, Optional
from functools import partial
from cloudevents.http import from_http, to_structured
from cloudevents.exceptions import MissingRequiredFields, InvalidRequiredFields

async def receive_body(receive: Callable) -> bytes:
    """Utility to receive the complete body from an ASGI receive callable"""
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body

class CloudEventSender: """Wraps the ASGI send callable to provide CloudEvent-aware sending"""

    def __init__(self, send: Callable[[Dict[str, Any]], Awaitable[None]]):
        self._send = send
        
    async def __call__(self, message: Dict[str, Any]) -> None:
        await self._send(message)
    
    async def send_event(self, event: Dict[str, Any], status: int = 200) -> None:
        """Send a CloudEvent as an HTTP response"""
        headers, body = to_structured(event)
        
        await self._send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (k.encode(), v.encode())
                for k, v in headers.items()
            ] + [(b"content-length", str(len(body)).encode())]
        })
        
        await self._send({
            "type": "http.response.body",
            "body": body,
        })
    
    async def send_error(self, status: int, message: str, error_type: str = "error") -> None:
        """Send an error as a CloudEvent"""
        error_event = {
            "specversion": "1.0",
            "type": f"com.example.{error_type}",
            "source": "/cloudevent/error",
            "id": "error-response",
            "data": {"error": message}
        }
        await self.send_event(error_event, status)

class CloudEventMiddleware:
    def __init__(self, app: Callable):
        self.app = app
    
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        try:
            # Get the body and convert headers
            body = await receive_body(receive)
            headers = {
                k.decode("utf-8").lower(): v.decode("utf-8")
                for k, v in scope.get("headers", [])
            }
            
            # Parse as CloudEvent and add to scope
            event = from_http(headers, body)
            scope["cloudevent"] = event
            
            # Wrap the send callable
            cloud_sender = CloudEventSender(send)
            
            # Call the wrapped application
            await self.app(scope, receive, cloud_sender)
            
        except (MissingRequiredFields, InvalidRequiredFields) as e:
            # If it's not a valid CloudEvent, send error response
            sender = CloudEventSender(send)
            await sender.send_error(400, str(e), "validation.error")
        except Exception as e:
            # Handle unexpected errors
            sender = CloudEventSender(send)
            await sender.send_error(500, str(e), "internal.error")

# Example usage:
async def app(scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
    """
    Example ASGI application using the enhanced scope and sender
    """
    # The CloudEvent is already parsed and available in scope
    event = scope["cloudevent"]
    
    # The send callable is wrapped to handle CloudEvents
    sender = send  # TypeVar would show this as CloudEventSender
    
    # Example response using the enhanced sender
    response_event = {
        "specversion": "1.0",
        "type": "com.example.response",
        "source": scope["path"],
        "id": f"response-to-{event['id']}",
        "data": {
            "message": "Processed successfully",
            "method": scope["method"],
            "client": scope["client"]
        }
    }
    
    await sender.send_event(response_event)

# Wrap your application with the middleware
app = CloudEventMiddleware(app)

# Run with:
# hypercorn app:app --bind 0.0.0.0:3000

