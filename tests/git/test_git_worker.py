from pathlib import Path

from app.git.git_worker import BatchOperationResult, handle_worker_error


def test_handle_worker_error_format() -> None:
    msg = handle_worker_error("clone", "/repo", RuntimeError("boom"))
    assert msg == "Unexpected error during clone: boom"


def test_batch_result_counts() -> None:
    result = BatchOperationResult(
        successful=[Path("/a"), Path("/b")],
        failed=[(Path("/c"), "reason")],
    )
    assert result.total_count == 3
    assert result.success_count == 2
    assert result.failure_count == 1


def test_batch_result_empty() -> None:
    result = BatchOperationResult(successful=[], failed=[])
    assert result.total_count == 0
    assert result.success_count == 0
    assert result.failure_count == 0
