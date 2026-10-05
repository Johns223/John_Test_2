# John_Test_2

Sandbox repository for evaluating third-party pull request review tools.

Code on feature branches here is intentionally defective. It exists so that
automated reviewers have something to find, and must not be deployed.

## Running it

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q

Pinned versions and hashes for the whole dependency tree are in
`requirements.lock`.
