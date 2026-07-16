from __future__ import annotations

import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from pdf_to_markdown.arxiv import extract_arxiv_id
from pdf_to_markdown.config import ALL_CONVERTERS, AppConfig
from pdf_to_markdown.downloader import download_pdf
from pdf_to_markdown.models import WorkflowResult
from pdf_to_markdown.storage import prompt_for_overwrite, write_markdown
from pdf_to_markdown.validators import is_valid_pdf, validate_markdown

ConverterMap = dict[str, Callable[[Path], str]]
Logger = Callable[[str], None]


def _default_err_log(message: str) -> None:
    print(message, file=sys.stderr)


def _resolve_converters(
    selected_converters: Iterable[str] | None,
    converters: ConverterMap,
) -> list[str]:
    selected = (
        list(selected_converters)
        if selected_converters is not None
        else list(ALL_CONVERTERS)
    )
    for name in selected:
        if name not in converters:
            raise KeyError(f"Unknown converter: {name}")
    return selected


def _run_converter(
    name: str,
    pdf_path: Path,
    out_dir: Path,
    converter_fn: Callable[[Path], str],
    *,
    overwrite: bool,
    log: Logger,
    err_log: Logger,
    confirm_overwrite: Callable[[Path], bool],
) -> Path | None:
    try:
        markdown = converter_fn(pdf_path)
    except (RuntimeError, OSError, PermissionError) as exc:
        err_log(f"[error] {name} conversion failed: {exc}")
        return None

    destination = out_dir / f"{pdf_path.stem}.md"
    try:
        write_markdown(
            markdown,
            destination,
            overwrite=overwrite,
            confirm_overwrite=confirm_overwrite,
            log=log,
        )
    except (RuntimeError, OSError, PermissionError) as exc:
        err_log(f"[error] {name} write failed: {exc}")
        return None

    if not validate_markdown(destination, expected_chars=len(markdown)):
        return None

    log(f"[ok] {name} output verified at {destination}")
    return destination


def run_workflow(
    *,
    url: str,
    selected_converters: Iterable[str] | None,
    force: bool,
    overwrite: bool,
    config: AppConfig,
    converters: ConverterMap,
    download_pdf_fn: Callable[..., Path] = download_pdf,
    log: Logger = print,
    err_log: Logger | None = None,
    confirm_overwrite: Callable[[Path], bool] = prompt_for_overwrite,
) -> WorkflowResult:
    if err_log is None:
        err_log = _default_err_log

    try:
        arxiv_id = extract_arxiv_id(url)
    except ValueError as exc:
        err_log(f"[error] {exc}")
        return WorkflowResult(exit_code=2)

    pdf_path = config.pdf_dir / f"{arxiv_id}.pdf"

    try:
        selected = _resolve_converters(selected_converters, converters)
    except KeyError as exc:
        err_log(f"[error] {exc}")
        return WorkflowResult(exit_code=1, arxiv_id=arxiv_id, pdf_path=pdf_path)

    for name in selected:
        output_dir = config.output_dir_for(name)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            err_log(f"[error] Cannot create directory {output_dir}: permission denied.")
            return WorkflowResult(
                exit_code=1,
                arxiv_id=arxiv_id,
                pdf_path=pdf_path,
            )
        except OSError as exc:
            err_log(f"[error] Failed to create directory {output_dir}: {exc}")
            return WorkflowResult(
                exit_code=1,
                arxiv_id=arxiv_id,
                pdf_path=pdf_path,
            )

    try:
        config.pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = download_pdf_fn(
            url,
            pdf_path,
            force=force,
            user_agent=config.user_agent,
            timeout_seconds=config.pdf_timeout_seconds,
        )
    except PermissionError as exc:
        err_log(f"[error] {exc}")
        return WorkflowResult(exit_code=1, arxiv_id=arxiv_id, pdf_path=pdf_path)
    except (RuntimeError, OSError) as exc:
        err_log(f"[error] {exc}")
        return WorkflowResult(exit_code=1, arxiv_id=arxiv_id, pdf_path=pdf_path)

    if not is_valid_pdf(pdf_path):
        err_log(
            f"[error] {pdf_path} is not a valid PDF (bad magic or missing %%EOF marker)."
        )
        return WorkflowResult(exit_code=1, arxiv_id=arxiv_id, pdf_path=pdf_path)

    outputs: dict[str, Path | None] = {}
    failed_converters: list[str] = []
    for name in selected:
        destination = _run_converter(
            name,
            pdf_path,
            config.output_dir_for(name),
            converters[name],
            overwrite=overwrite,
            log=log,
            err_log=err_log,
            confirm_overwrite=confirm_overwrite,
        )
        outputs[name] = destination
        if destination is None:
            failed_converters.append(name)

    if failed_converters:
        err_log(f"[error] Failed converters: {', '.join(failed_converters)}")
        return WorkflowResult(
            exit_code=1,
            outputs=outputs,
            failed_converters=failed_converters,
            arxiv_id=arxiv_id,
            pdf_path=pdf_path,
        )

    log("[done] Workflow completed successfully.")
    return WorkflowResult(
        exit_code=0,
        outputs=outputs,
        failed_converters=[],
        arxiv_id=arxiv_id,
        pdf_path=pdf_path,
    )
