# Python API Test Framework

A Python API test automation framework for validating REST APIs. It currently
tests the JSONPlaceholder `/posts` resource and separates critical-path smoke
coverage from broader regression coverage. The framework provides reusable HTTP
fixtures, configurable API settings, JSON Schema validation, request and
response evidence in Allure, and CI execution through GitHub Actions.

## Stack

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/) for Python and dependency management
- pytest and pytest-xdist for test execution
- requests for HTTP client sessions
- jsonschema for response contract validation
- Allure pytest and Allure Commandline for test reports
- Ruff, Pylint, and mypy for code quality and type checking
- GitHub Actions for continuous integration

## Installation

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and enter it:

   ```bash
   git clone https://github.com/nadiaalexqa/python-api-test-framework.git
   cd python-api-test-framework
   ```

3. Create local configuration from the example file:

   ```bash
   cp .env.example .env
   ```

   Set `BASE_URL`, `API_TIMEOUT`, and (if required) `API_TOKEN` in `.env`.
   The defaults point to `https://jsonplaceholder.typicode.com` with a
   10-second timeout.

4. Install the locked dependencies and managed Python version:

   ```bash
   uv sync
   ```

## Running tests

pytest writes Allure result files to `allure-results/` by default.

| Suite | Command | Purpose |
| --- | --- | --- |
| Smoke | `uv run pytest -m smoke` | Fast critical-path API health checks |
| Regression | `uv run pytest -m regression` | Exhaustive, negative, and edge-case coverage |
| All tests | `uv run pytest` | Runs both smoke and regression tests |

Pass `--base-url` or `--api-timeout` to override local configuration for one
run:

```bash
uv run pytest -m smoke --base-url https://api.example.com --api-timeout 20
```

To view a local Allure report, install
[Allure Commandline](https://allurereport.org/docs/install/) and run:

```bash
allure generate allure-results --clean -o allure-report
allure open allure-report
```

## Code quality

Ruff and Pylint are included in the project dependencies and configured in
[`pyproject.toml`](pyproject.toml). Run the same checks locally that the CI
quality gate runs:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pylint tests/ config/ --fail-under=8.0
```

To automatically apply Ruff formatting, run:

```bash
uv run ruff format .
```

Ruff checks lint rules and formatting across the repository. Pylint analyzes
the `tests/` and `config/` packages and requires a score of at least 8.0.

## CI/CD

GitHub Actions is configured in
[`.github/workflows/api-tests.yml`](.github/workflows/api-tests.yml).

- A **Lint & Static Analysis** quality gate runs Ruff linting, Ruff format
  checks, and Pylint before every test job. A failed lint check prevents the
  dependent smoke or regression suite from running.
- **Pull requests and pushes** to `main` or `master` run the smoke suite.
- **Scheduled runs** execute the regression suite every day at **07:00 UTC**
  (`0 7 * * *`; 02:00 EST / 03:00 EDT).
- **Manual runs** are available through **Actions → API Tests → Run workflow**.
  Choose `smoke`, `regression`, or `all`.
- Each job runs on `ubuntu-latest`, checks out the repository, installs `uv`
  and Python, restores dependencies with `uv sync`, and runs its selected
  pytest marker.
- Regardless of test outcome, each job generates an Allure HTML report and
  uploads both raw results and the HTML report as artifacts. Artifacts are
  retained for 14 days.

The workflow uses repository configuration variables when present:

- `BASE_URL` (defaults to `https://jsonplaceholder.typicode.com`)
- `API_TIMEOUT` (defaults to `10`)

Set these under **Settings → Secrets and variables → Actions → Variables** to
target a different API or adjust the CI timeout.
