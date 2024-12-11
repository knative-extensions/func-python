# Python Func Runtime

This middleware is used by Knative Functions to expose a Function written in
Python as a network service.

## Contents
```
.
├── cmd
│   └── fhttp          - Example a Function using the http middleware
├── src/func_python
│   ├── http.py        - HTTP Middleware
├── tests
│   ├── http_test.py   - HTTP Middleware tests
└── README.md          - This Readme
```

## Development

## Tests

Run suite
`poetry run python -m pytest tests/* -v -s`

To enable debug logging use `--log-cli-level`:
`poetry run python -m pytest tests/* -v -s --log-cli-level=DEBUG`

## Example Main

Minimal example of running the test command, which shows how this
library is used when integrate with Functions, and can be useful during dev.

- install `poetry` via `pipx`
- install dependencies with `poetry install`
- activate the virtual environment managed by poetry via `poetry shell`
  Note that in some environments this command may cause collissions with
  configured keyboard shortcuts.  If there are problems, you can instead
  source the environment variables directly with:
  `source $(poetry env info --path)/bin/activate`
- run the example via `poetry run python cmd/fhttp/main.py`
- deactivate the virtual environment with `exit`

## Suggested Flow

A nice method of development using git worktrees:

p. From a personal fork, create a new worktree for the bug, feature or chore
   named appropriately (eg. "feature-a")

2. Implement the code changes and commit.

3. Update the CHANGELOG.md to include the change in the "Unreleased" section.

4. Commit, push and create a PR to the upstream repository's main branch.

5. Solicit a code-read from another team member.

6. Upon approval, squash and merge to main.

7. (optional) cleanup by removing the worktree and associated local and remote
   branch.

8. (optional) pull into local fork's main and push to remote fork main.

