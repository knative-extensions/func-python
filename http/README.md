# Functions Python Middleware

An ASGI Application which will serve a Function.  The ASGI application
is the middleware.

The middleware implements lifecycle events such as "start" and "stop", health 
checks for readiness and liveness, and a handler for HTTP requests.

The function is expected to implement "handle", and the middleware will
raise an error if the function does not implement this method.  Start and stop
are optional.  Readiness and liveness are also optional, with the middleware
providing default implementations.

Signals are handled by the ASGI server implementation hypercorn and initiate
shutdown of the service.

## Usage

To see a usage example, refer to cmd/fhttp.



