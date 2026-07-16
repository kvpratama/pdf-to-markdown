# pdf-to-markdown

Download an arXiv PDF and convert it to Markdown, with the option of running two
backends side by side so the outputs can be compared.

The tool accepts an arXiv URL, downloads the PDF into a local `pdf/` directory,
validates the file is a real PDF, and then runs one or both of the supported
conversion backends:

- **Docling** writes Markdown to `docling/`.
- **MarkItDown** (Microsoft) writes Markdown to `markitdown/`.

By default both backends run so you can compare their output, but each backend
can also be selected on its own.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Project Layout](#project-layout)
- [Programmatic API](#programmatic-api)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- One-command download of an arXiv PDF, with idempotent local caching.
- Built-in PDF integrity check (magic bytes plus `%%EOF` trailer).
- Pluggable converter registry; new backends can be added by registering an
  adapter without changing the CLI or the workflow.
- Per-backend output directories so Docling and MarkItDown outputs never
  overwrite each other.
- Interactive overwrite prompt, plus a `--yes`/`-y` flag for non-interactive
  runs.
- Structured exit codes for scripting:
  - `0` on full success
  - `1` on any converter, network, or validation failure
  - `2` when the URL is invalid
- A small Python API (`pdf_to_markdown.workflow.run_workflow`) for embedding
  the same flow in other tools.

## Requirements

- Python **3.14** (see `.python-version`).
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency
  management.
- Network access to `arxiv.org` to download PDFs.
- Disk space for the two converter backends; `docling` and `markitdown[all]`
  ship with large optional extras and model assets.

## Installation

1. Clone the repository and change into it:

   ```bash
   git clone https://github.com/kvpratama/pdf-to-markdown.git
   cd pdf-to-markdown
   ```

2. Install dependencies with `uv`. The dev extras include the test runner and
   linters; the runtime backends are listed in `pyproject.toml`.

   ```bash
   uv sync
   ```

The first conversion with each backend may download model files on demand.

## Usage

The package ships a CLI that can be launched either through the
`pdf-to-markdown` shim or directly:

```bash
# Default: download the PDF and run both converters.
uv run main.py https://arxiv.org/pdf/0000.00000

# Or use the module entrypoint.
uv run python -m pdf_to_markdown https://arxiv.org/pdf/0000.00000
```

After a successful run, the converted Markdown files live at:

- `docling/0000.00000.md`
- `markitdown/0000.00000.md`

### Selecting a converter

```bash
# Run only Docling.
uv run main.py https://arxiv.org/pdf/0000.00000 --converter docling

# Run only MarkItDown.
uv run main.py https://arxiv.org/pdf/0000.00000 --converter markitdown

# Run both explicitly.
uv run main.py https://arxiv.org/pdf/0000.00000 --converter both
```

### Controlling the download and overwrite behavior

```bash
# Re-download the PDF even if it already exists locally.
uv run main.py https://arxiv.org/pdf/0000.00000 --force

# Overwrite existing Markdown without prompting.
uv run main.py https://arxiv.org/pdf/0000.00000 --yes
```

### Supported URL forms

Any URL containing an arXiv identifier is accepted, for example:

- `https://arxiv.org/pdf/0000.00000`
- `https://arxiv.org/pdf/1234.56789v1`
- `https://arxiv.org/pdf/1234.56789.pdf`
- `https://arxiv.org/abs/1234.56789`

## CLI Reference

| Flag            | Short | Description                                                                 |
| --------------- | ----- | --------------------------------------------------------------------------- |
| `url`           |       | arXiv PDF URL, e.g. `https://arxiv.org/pdf/0000.00000`. Required.           |
| `--force`       |       | Re-download the PDF even if it already exists locally.                      |
| `--yes`         | `-y`  | Overwrite existing Markdown files without prompting.                        |
| `--converter`   |       | Which converter(s) to run. Choices: `both` (default), `docling`, `markitdown`. |
| `-h` / `--help` |       | Show the built-in help text and exit.                                       |

## Configuration

Runtime settings are encapsulated in
[`pdf_to_markdown.config.AppConfig`](pdf_to_markdown/config.py):

| Field                | Default                                | Purpose                                         |
| -------------------- | -------------------------------------- | ----------------------------------------------- |
| `project_root`       | the package's parent directory         | Base for relative paths.                        |
| `pdf_dir`            | `<project_root>/pdf`                   | Where downloaded PDFs are stored.               |
| `docling_dir`        | `<project_root>/docling`               | Output directory for the Docling backend.       |
| `markitdown_dir`     | `<project_root>/markitdown`            | Output directory for the MarkItDown backend.    |
| `user_agent`         | `pdf-to-markdown/0.1 (+https://arxiv.org)` | HTTP `User-Agent` header for the download.  |
| `pdf_timeout_seconds`| `60`                                   | Network timeout for the PDF download.           |

The CLI uses `AppConfig.default()`. To customize paths or timeouts, build
your own `AppConfig` and call `run_workflow` directly (see
[Programmatic API](#programmatic-api)).

## Project Layout

```text
.
├── main.py                      # Compatibility shim that calls the package CLI.
├── pdf_to_markdown/             # Main package.
│   ├── __init__.py              # Re-exports `main` for `python -m pdf_to_markdown`.
│   ├── arxiv.py                 # arXiv URL parsing and identifier extraction.
│   ├── cli.py                   # Argument parsing and CLI entrypoint.
│   ├── config.py                # AppConfig and converter name constants.
│   ├── downloader.py            # PDF download over HTTP.
│   ├── models.py                # WorkflowResult dataclass.
│   ├── storage.py               # Directory creation, overwrite prompts, writes.
│   ├── validators.py            # PDF and Markdown integrity checks.
│   ├── workflow.py              # End-to-end orchestration of the pipeline.
│   └── converters/
│       ├── base.py              # ConverterAdapter dataclass.
│       ├── docling.py           # Docling backend adapter.
│       ├── markitdown.py        # MarkItDown backend adapter.
│       └── registry.py          # Name-to-adapter mapping.
├── tests/                       # Pytest suite, organized by module.
├── pyproject.toml               # Project metadata and dependencies.
├── uv.lock                      # Locked dependency graph.
└── README.md
```

## Programmatic API

The same workflow that the CLI runs is exposed as
[`pdf_to_markdown.workflow.run_workflow`](pdf_to_markdown/workflow.py). It
returns a structured `WorkflowResult` so callers can inspect the result
without parsing stdout.

```python
from pathlib import Path

from pdf_to_markdown.config import AppConfig, CONVERTER_DOCLING, CONVERTER_MARKITDOWN
from pdf_to_markdown.converters.registry import get_converter
from pdf_to_markdown.workflow import run_workflow

config = AppConfig.default().with_pdf_dir(Path("/tmp/papers"))

result = run_workflow(
    url="https://arxiv.org/pdf/0000.00000",
    selected_converters=[CONVERTER_DOCLING, CONVERTER_MARKITDOWN],
    force=False,
    overwrite=True,
    config=config,
    converters={
        CONVERTER_DOCLING: get_converter(CONVERTER_DOCLING).convert,
        CONVERTER_MARKITDOWN: get_converter(CONVERTER_MARKITDOWN).convert,
    },
)

print(result.exit_code)            # 0 on success
print(result.outputs)              # {"docling": Path(...), "markitdown": Path(...)}
print(result.failed_converters)    # [] on success
```

The workflow also accepts injected callables (`download_pdf_fn`,
`confirm_overwrite`, `log`, `err_log`) which makes it straightforward to
unit-test downstream code that wraps the same flow.

## Development

Install the development dependencies:

```bash
uv sync
```

Common tasks:

```bash
# Lint the codebase.
uv run ruff check .

# Auto-fix lint issues.
uv run ruff check . --fix

# Format the codebase.
uv run ruff format .

# Type-check the codebase.
uv run ty check

# Run the pre-commit hooks on every file.
uv run pre-commit run --all-files
```

`pyproject.toml` pins the development tooling to the versions used in CI.

## Testing

The test suite uses `pytest` and is organized to mirror the package layout
(one test module per source module):

```bash
# Run the full suite.
uv run pytest

# Run a single test module.
uv run pytest tests/test_workflow.py

# Run a single test.
uv run pytest tests/test_workflow.py::test_run_workflow_returns_two_for_invalid_url
```

Heavy backends are loaded lazily, so the test suite does not require
`docling` or `markitdown` to be available. Tests that need them are
expected to stub the relevant adapters in `pdf_to_markdown.converters`.

## Troubleshooting

- **"Docling is not installed"** — run `uv sync` to install the `docling`
  dependency declared in `pyproject.toml`.
- **"MarkItDown is not installed"** — the `markitdown[all]` extra pulls in
  format-specific adapters; rerun `uv sync` if the extra was skipped.
- **"Overwrite confirmation unavailable (non-interactive shell)"** — the
  CLI is asking for a `y/N` answer on stdin. Re-run with `--yes` to skip
  the prompt, for example in CI.
- **"is not a valid PDF"** — the downloaded file did not start with the
  PDF magic bytes or did not contain a `%%EOF` marker. The file is
  removed and the workflow exits with code `1`; rerun with `--force` to
  re-download.
- **Slow first run** — the first conversion with each backend may download
  model files. Subsequent runs are faster.

## Contributing

1. Fork the repository and create a feature branch.
2. Make your change. Keep modules small and focused; new behavior should
   land in the module that owns the responsibility, not in `main.py` or
   `cli.py`.
3. Add or update tests so the new behavior is covered.
4. Run `uv run ruff check .`, `uv run ruff format .`, `uv run ty check`,
   and `uv run pytest` before opening a pull request.
5. If you are adding a new conversion backend, register an adapter in
   `pdf_to_markdown/converters/registry.py` and a corresponding output
   directory attribute on `AppConfig`.

## License

This project is licensed under the MIT License. See
[LICENSE](LICENSE) for the full text.
