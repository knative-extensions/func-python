import argparse
import logging
import func_python.http

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser(description='Serve a Test Function')
parser.add_argument('--static', action='store_true',
                    help='Serve the example static handler (default is to '
                         'instantiate and serve the example class)')
args = parser.parse_args()


async def handle(scope, receive, send):
    """ handle is an example of a static handler which can be sent to the
    middleware as a funciton.  It will be wrapped in a default Funciton
    instance before being served as an ASGI application.
    """
    logging.info("OK: static")

    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': 'OK: static'.encode(),
    })


class Function:
    """ Function is an example of a functioon instance.  The structure
    implements the function which will be deployed as a network service.
    The class name can be changed.  The only required method is "handle".
    """

    async def handle(self, scope, receive, send):
        """ handle is the only method which must be implemented by the
        function instance for it to be served as an ASGI handler.
        """
        logging.info("OK: instanced")

        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': 'OK: instanced'.encode(),
        })


def new():
    """ new is the factory function (or constructor) which will create
    a new function instance when invoked.  This must be named "new", and the
    structure returned must include a method named "handle" which implements
    the ASGI specification's method signature.  The name of the class itself
    can be changed.
    """
    return Function()


if __name__ == "__main__":
    if args.static:
        logging.info("Starting static handler")
        func_python.http.serve(handle)
    else:
        logging.info("Starting new instance")
        func_python.http.serve(new)
