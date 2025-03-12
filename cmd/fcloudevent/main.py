import argparse
import logging
import json
from func_python.cloudevent import serve
from cloudevents.http import CloudEvent

# Set the default logging level to INFO
logging.basicConfig(level=logging.INFO)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Serve a CloudEvents Function')
parser.add_argument('--static', action='store_true',
                    help='Serve the static handler (default is instanced)')
args = parser.parse_args()


# Static handler implementation
# Enable with --static
# Must be named exactly "handle"
async def handle(scope, receive, send):
    """Static handler for CloudEvents"""
    logging.info("CloudEvent static handler called")
    
    # Process the CloudEvent from the scope
    event = scope.get("event")
    if not event:
        error_event = CloudEvent(
            {"type": "dev.functions.error", "source": "/cloudevent/error"},
            {"message": "No CloudEvent found in request"}
        )
        await send(error_event, 400)
        return
    
    # Log the received event
    logging.info(f"Received event type: {event['type']}")
    logging.info(f"Received event source: {event['source']}")
    logging.info(f"Received event data: {json.dumps(event.data)}")
    
    # Create and send response CloudEvent
    response_event = CloudEvent(
        {"type": "dev.functions.response", "source": "/cloudevent/processor"},
        {"message": "Processed static", "original_data": event.data}
    )
    await send(response_event)


# Instanced handler implementation
class MyCloudEventFunction:
    def __init__(self):
        self.event_count = 0
        logging.info("CloudEvent function instance created")
    
    async def handle(self, scope, receive, send):
        """Handle CloudEvents in an instanced function"""
        event = scope.get("event")
        if not event:
            error_event = CloudEvent(
                {"type": "dev.functions.error", "source": "/cloudevent/error"},
                {"message": "No CloudEvent found in request"}
            )
            await send(error_event, 400)
            return
        
        self.event_count += 1
        
        # Log the received event
        logging.info(f"Received event type: {event['type']}")
        logging.info(f"Received event source: {event['source']}")
        logging.info(f"Received event data: {json.dumps(event.data)}")
        logging.info(f"Total events processed: {self.event_count}")
        
        # Create and send response CloudEvent
        response_event = CloudEvent(
            {"type": "dev.functions.response", "source": "/cloudevent/processor"},
            {
                "message": "Processed instanced", 
                "original_data": event.data,
                "count": self.event_count
            }
        )
        await send(response_event)
    
    def alive(self):
        logging.info("Liveness checked")
        return True, f"I'm alive! Events: {self.event_count}"
    
    def ready(self):
        logging.info("Readiness checked")
        return True, "I'm ready!"
    
    def stop(self):
        logging.info(f"Stopping after {self.event_count} events")


# Function instance constructor
def new():
    """Create a new function instance"""
    return MyCloudEventFunction()


# Run the example
if __name__ == "__main__":
    if args.static:
        logging.info("Starting static CloudEvent handler")
        serve(handle)
    else:
        logging.info("Starting instanced CloudEvent handler")
        serve(new)
