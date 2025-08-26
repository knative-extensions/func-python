import argparse
import logging
from func_python.cloudevent import serve
from cloudevents.http import CloudEvent

# Set the default logging level to INFO
logging.basicConfig(level=logging.INFO)

# Allow this test to be either instanced (default) or --static
# to test the two different primary method signatures supported in the
# final Function.
parser = argparse.ArgumentParser(description='Serve a Test CloudEvent Function')
parser.add_argument('--static', action='store_true',
                    help='Serve the example static handler (default is to '
                         'instantiate and serve the example class)')
args = parser.parse_args()


# Example static handler.
# Enable with --static
# Must be named exactly "handle"
async def handle(scope, receive, send):
    """ handle is an example of a static handler which can be sent to the
    middleware as a function.  It will be wrapped in a default Function
    instance before being served as an ASGI application.
    """
    logging.info("Static CloudEvent handler invoked")
    
    # Access the CloudEvent from the scope
    event = scope["event"]
    if not event:
        error_event = CloudEvent(
            {"type": "dev.functions.error", "source": "/fcloudevent/error"},
            {"message": "No CloudEvent found in scope"}
        )
        await send(error_event, 500)
        return
    
    logging.info(f"Received CloudEvent: type={event['type']}, source={event['source']}")
    
    # Handle event data - it might be bytes or dict
    event_data = event.data
    if isinstance(event_data, bytes):
        import json
        event_data = json.loads(event_data)
    logging.info(f"CloudEvent data: {event_data}")
    
    response_event = CloudEvent(
        {
            "type": "com.example.response.static",
            "source": "/fcloudevent/static",
        },
        {
            "message": "OK: static CloudEvent handler",
            "received_event_type": event['type'],
            "received_event_source": event['source'],
            "received_data": event_data
        }
    )
    
    await send(response_event)


# Example instanced handler
# This is the default expected by this test.
# The class can be named anything, but there must be a constructor named "new"
# which returns an object with an async method "handle" conforming to the ASGI
# callable's method signature.
class MyCloudEventFunction:
    def __init__(self):
        self.event_count = 0
        logging.info("CloudEvent function instance created")
    
    async def handle(self, scope, receive, send):
        logging.info("Instanced CloudEvent handler invoked")
        
        # Access the CloudEvent from the scope
        event = scope["event"]
        if not event:
            # This shouldn't happen with our fix, but let's handle it gracefully
            error_event = CloudEvent(
                {"type": "dev.functions.error", "source": "/fcloudevent/error"},
                {"message": "No CloudEvent found in scope"}
            )
            await send(error_event, 500)
            return
        
        self.event_count += 1
        
        logging.info(f"Received CloudEvent #{self.event_count}: type={event['type']}, source={event['source']}")
        
        # Handle event data - it might be bytes or dict
        event_data = event.data
        if isinstance(event_data, bytes):
            import json
            event_data = json.loads(event_data)
        logging.info(f"CloudEvent data: {event_data}")
        logging.info(f"Total events processed: {self.event_count}")
        
        response_event = CloudEvent(
            {
                "type": "com.example.response.instanced",
                "source": "/fcloudevent/instanced",
            },
            {
                "message": "OK: instanced CloudEvent handler",
                "event_count": self.event_count,
                "received_event_type": event['type'],
                "received_event_source": event['source'],
                "received_data": event_data
            }
        )
        
        # Demonstrate different sending methods
        if self.event_count % 2 == 0:
            # Use structured encoding (default)
            logging.info("Sending structured CloudEvent response")
            await send.structured(response_event)
        else:
            # Use binary encoding
            logging.info("Sending binary CloudEvent response")
            await send.binary(response_event)
    
    def alive(self):
        logging.info("Liveness checked")
        return True, f"I'm alive! Events: {self.event_count}"
    
    def ready(self):
        logging.info("Readiness checked")
        return True, "I'm ready!"
    
    def stop(self):
        logging.info(f"Stopping after {self.event_count} events")


# Function instance constructor
# expected to be named exactly "new"
# Must return a object which exposes a method "handle" which conforms to the
# ASGI specification's method signature.
def new():
    """ new is the factory function (or constructor) which will create
    a new function instance when invoked.  This must be named "new", and the
    structure returned must include a method named "handle" which implements
    the ASGI specification's method signature.  The name of the class itself
    can be changed.
    """
    return MyCloudEventFunction()


# Run the example.
# Start either the static or instanced handler depending on flag --static
if __name__ == "__main__":
    if args.static:
        logging.info("Starting static CloudEvent handler")
        serve(handle)
    else:
        logging.info("Starting instanced CloudEvent handler")
        serve(new)

