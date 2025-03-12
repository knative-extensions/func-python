# Function HTTP Test Command

fhttp is a command which illustrates how the func-python library middleware
wraps a function and exposes it as a service. Useful for development.

This is an example usage of the Functions HTTP middleware.

Run the function
```
poetry run python cmd/fhttp/main.py
```

Send a HTTP request against it:
```
curl -v -X POST http://127.0.0.1:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello HTTP Function",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "data": {
      "name": "Test User",
      "id": 12345
    }
  }'
```

To see the actual middleware which is used when building a Python Function,
see the [Functions Python Scaffolding](https://github.com/knative/func/tree/main/templates/python/http)
