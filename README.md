# Python Func Runtime

This middleware is used by Knative Functions to expose a Function written in
Python as a network service.


## Contents
```
.
├── cmd
│   └── fhttp     - Example a function using the http middleware
├── src/func_python
│   ├── http.py   - HTTP Middleware
└── README.md     - This Readme
```

## Development

- install `poetry` via `pipx`
- install dependencies with `poetry install`
- activate the virtual environment managed by poetry via `poetry shell`
- run the example via `python cmd/fhttp/main.py`
- deactivate the virtual environment with `exit`
