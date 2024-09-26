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
- activate the virtual environment managed by poetry via `poetry shell`
  Note that on some environments this command may cause collissions with
  configured keyboard shortcuts.  If there are problems, you can source
  the environment variables from the autogenerated venv with:
  `source $(poetry env info --path)/bin/activate`
- install dependencies into the activated environment with `poetry install`
- run the example via `python cmd/fhttp/main.py`
- deactivate the virtual environment with `exit`
