import argparse
import logging
from func_python.http import serve

# Set the default logging level to INFO
logging.basicConfig(level=logging.INFO)

# Allow this test to be either instanced (default) or --static
# to test the two different primary method signatures supported in the
# final Function.
parser = argparse.ArgumentParser(description='Serve a Test Function')
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
    logging.info("OK: static!!")

    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': 'OK: static'.encode(),
    })


# Example instanced handler
# This is the default expected by this test.
# The class can be named anything, but there must be a constructor named "new"
# which returns an object with an async method "handle" conforming to the ASGI
# callable's method signature.
class MyFunction:
    async def handle(self, scope, receive, send):
        logging.info("OK")

        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': 'OK: instanced'.encode(),
        })

    def alive(self):
        logging.info("liveness checked")
        return True, "I'm alive!"

    def ready(self):
        logging.info("readiness checked")
        return True, "I'm ready!"

    def stop(self):
        logging.info("Cleanup on stop")
        # Add cleanup logic here if necessary


# Function instance constructor
# expected to be named exactly "new"
# Must return a object which exposes a method "handle" which conforms to the
# ASGI callable spec.
def new():
    """ new is the factory function (or constructor) which will create
    a new function instance when invoked.  This must be named "new", and the
    structure returned must include a method named "handle" which implements
    the ASGI specification's method signature.  The name of the class itself
    can be changed.
    """
    return MyFunction()


# Run the example.
# Start either the static or instanced handler depending on flag --static
if __name__ == "__main__":
    if args.static:
        logging.info("Starting static handler")
        serve(handle)
    else:
        logging.info("Starting new instance")
        serve(new)
