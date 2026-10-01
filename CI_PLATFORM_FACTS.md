# CI Platform Type-Check / Test Facts

> Moved from `AGENTS.md` §8.8 (2026-09-23). Platform-specific CI type-check and
> test constraints that still apply. Revisit when touching pyright/mypy config
> or CI workflows on any OS.

- **`steamworks` pyright stubs** — `.pyi` stubs under `stubs/steamworks/`
  (`__init__.pyi`, `structs.pyi`); pyproject sets `stubPath = "stubs"` +
  `reportMissingModuleSource = "none"`. mypy already ignores `steamworks.*`.
- **`lxml` `.text` assignment (Linux pyright + super-linter mypy)** — resolved
  by removing `types-lxml` (kept `lxml-stubs`, which types `.text` as settable)
  and a scoped `reportAttributeAccessIssue = "none"` executionEnvironment in
  `[tool.pyright]`.
- **QtWebEngine segfault (Linux CI)** — `.github/workflows/pytest.yml` Linux
  test step exports `QTWEBENGINE_DISABLE_GPU=1` and
  `QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-gpu-compositing
  --no-sandbox"`.
- **`runJavaScript` callback arity (macOS)** — no-op callbacks passed to
  `page.runJavaScript(...)` must accept the JS return value
  (`lambda _=None: None`), not `lambda: None`.
