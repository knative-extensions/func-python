# Python Func Runtime

This middleware is used by Knative Functions to expose a Function written in
Python as a network service.

## Contents
```
.
├── cmd
│   └── fhttp                - Example Function using the http middleware
│   └── fcloudevent          - Example Function using the CloudEvent middleware
├── src/func_python
│   ├── http.py              - HTTP Middleware
│   ├── cloudevents.py       - CloudEvent Middleware
├── tests
│   ├── http_test.py         - HTTP Middleware tests
│   ├── cloudevent_test.py   - CloudEvent tests
└── README.md                - This Readme
```

## Development

## Tests

Install dependencies:
`poetry install`

Run suite:
`poetry run pytest`

Or more verbosely:
`poetry run pytest -vs --log-cli-level=INFO`

To enable more granular log levels:
`poetry run pytest --log-cli-level=INFO`

## Example Commands

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
   `git worktree add feature-a`

2. Implement the code changes and commit.

3. Update the CHANGELOG.md to include the change in the "Unreleased" section.

4. Commit, push and create a PR to the upstream repository's main branch.

5. Solicit a code-read from another team member.

6. Upon approval, squash and merge to main.

7. (optional) cleanup by removing the worktree and associated local and remote
   branches.

8. (optional) pull into local fork's main and push to remote fork main.

## Testing Published Package

Prior to releasing, it's possible to test the package which was published
to TestPyPI when the release PR is merged to main but before the tag
is pushed (which triggers production release).

To test, in a test project ensure the it adds the test package as an
explicit source in pyproject.toml:
```
[[tool.poetry.source]]
name = "test-pypi"
url = "https://test.pypi.org/simple/"
priority = "explicit"
```
Then update the dependency to explicitly pull the new version which is only
available on TestPyPI.  For example to test a hypothetical unreleased version
0.1.2:
```
[tool.poetry.dependencies]
func_python = {version = "0.1.2", source = "test-pypi"}
```
Run `poetry install` to install the unreleased version from Test PyPI

Note: do not check in this change.


## Releasing

NOTE: This process is currently undergoing minor tweaks, and thus contains
several manual steps.  Once the process is codified, it can be more highly 
automated.

1. Create a new branch "release-x.y" from an up-to-date main
   When incrementing, follow Semantic Versioning standard. eg:
   - Bug fixes:  ++ patch version
   - Features:   ++ minor version
   - Breaking Changes:  ++ major version

2. Update pyproject.toml with the new version.

3. Update CHANGELOG.md by moving the "Unreleased" items into a new
   section for the given version (leaving an empty Unreleased section as a
   template for future updates)

4. Commit, push and create a PR to upstream's main branch
   Please set the commit message to "Release vx.y.z" with the new version number

5. Obtain approval for release from another team member.

6. Squash and merge (ensure the commit message remains Release vx.y.x).

7. Verify the new version was correctly published to test PyPI and all
   precautions have been taken to ensure it is functioning as intended.
   (See testing above)

8. Pull from upstream into your local main branch and tag the commit vx.y.z
   (the squash and merge will have created a new commit hash)

9. push the tag to upstream, triggering the release to production PyPI.

10. Update the GitHub release's notes to be the changelog section's contents .


### Potential improvements

Update to using the suffix "rcX" so as not to confuse folks pulling tags list
from the git repo.  Without this suffix, a simple listing of the latest
tags from the repo would show a potentially unreleased version as the latest.

With the use of these release-candidate tags, the use of TestPyPI may be
unnecessary.

Perhaps push the RC tag to the PR's commit and test prior to merging the
PR to main, such that a potentially broken version is not kept in the main
branch's history.  For example, if v0.1.2rc1 failed, its commit will not be
part of the main branch.
