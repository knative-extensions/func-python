# CloudEvent Function Example

This directory contains an example CloudEvent function that demonstrates how to use the `func_python.cloudevent` middleware to handle CloudEvents.

This is an example usage of the Functions CloudEvents middleware.

Run the function
```

## Start the Function

Run the instanced handler (default):
```bash
poetry run python cmd/fcloudevent/main.py
```

Run the static handler:
```bash
poetry run python cmd/fcloudevent/main.py --static
```

Change the listen address (default is [::]:8080):
```bash
LISTEN_ADDRESS=127.0.0.1:8081 poetry run python cmd/fcloudevent/main.py
```

## Invoke the Function

You can send a CloudEvent to the function using curl with structured encoding:

```bash
curl -X POST http://127.0.0.1:8080 \
  -H "Ce-Specversion: 1.0" \
  -H "Ce-Type: com.example.test" \
  -H "Ce-Source: /test/source" \
  -H "Ce-Id: test-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello CloudEvents!"}'
```

Or with a full CloudEvent in structured format:

```bash
curl -X POST http://127.0.0.1:8080 \
  -H "Content-Type: application/cloudevents+json" \
  -d '{
    "specversion": "1.0",
    "type": "com.example.test",
    "source": "/test/source",
    "id": "test-456",
    "datacontenttype": "application/json",
    "data": {
      "message": "Hello from structured CloudEvent!",
      "value": 42
    }
  }'
```


To see the actual middleware which is used when building a Python Function,
see the [Functions Python Scaffolding](https://github.com/knative/func/tree/main/templates/python/cloudevents)
