# Function CloudEvents Test Command

fcloudevent is a command which illustrates how the func-python library middleware
wraps a function and exposes it as a service. Useful for development.

This is an example usage of the Functions CloudEvents middleware.

Run the function
```
poetry run python cmd/fcloudevent/main.py
```

Send a CloudEvent against it:
```
curl -v -X POST http://127.0.0.1:8080/ \
  -H "Content-Type: application/json" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: com.example.event.submit" \
  -H "ce-source: /applications/user-service" \
  -H "ce-id: $(uuidgen)" \
  -H "ce-time: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  -d '{
    "message": "Hello CloudEvents",
    "username": "testuser",
    "action": "submit",
  }'
```

To see the actual middleware which is used when building a Python Function,
see the [Functions Python Scaffolding](https://github.com/knative/func/tree/main/templates/python/cloudevents)
