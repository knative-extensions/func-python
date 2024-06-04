# Function HTTP Test Command

fhttp is a command which illustrates how the func-python library middleware
wraps a function and exposes it as a service.  Useful for development.

This is an example usage of the Functions HTTP middleware.

To see the actual middleware which is used when building a Python Function,
see the [Functions Python Scaffolding](https://github.com/knative/func/tree/main/templates/python/http)

## Running

Create a local virtual environment if it does not already exist:
```bash
python3 -m venv venv
```
Activate the virtual environment:
```bash
source ./venv/bin/activate
```
Ensure the requirements are installed:
```bash
pip install -r requirements.txt
```
Run the application:
```bash
python3 ./main.py
```
use `^C` to stop the application

To Deactivate the virtual environment:
```bash
deactivate
