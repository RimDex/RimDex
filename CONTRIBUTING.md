# Contributing to RimDex

Thank you for being interested on contributing to RimDex! This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## Questions and bug reports

You can use the [issue tracker](https://github.com/RimDex/RimDex/issues) to ask questions and report bugs but do not forget to search (including closed issues) to see if your entry has been posted before.

## Contributions

The project and its contributions are currently managed using the issue tracker. Before preparing and submitting a PR for a feature, create an issue on the [tracker](https://github.com/RimDex/RimDex/issues) to allow for discussing and refining the idea before it is implemented. We also have a [Discord](https://discord.gg/aV7g69JmR2) where the majority of discussion takes place.

Before finalizing your PR, please read through the [Development Guide](https://github.com/RimDex/RimDex/wiki/Development-Guide) and feel free to ask any questions needed. Source code contributions must follow the [Contributor Guidelines](https://github.com/RimDex/RimDex/wiki/Development-Guide#contributor-guidelines)!

## Development tooling

All checks and tests are driven by `just` recipes (see `justfile`). Keep the
quality gate green: `just check` (typecheck mypy + pyright + jscpd +
deferred-imports + layer-check + i18n-check on Windows; super-lint + typecheck +
pyright on Unix). The mandatory contributor guardrails live in `AGENTS.md`
(Code Quality, Definition of Done, Traps) — run `just check` after every
implementation and avoid `# type: ignore` unless genuinely necessary.

### Recipe index

**Run / test**

- `just run` — launch the RimDex application (`uv run python -m app`).
- `just test` — full suite with `--doctest-modules --no-qt-log`.
- `just test-verbose` — tests with `-v --tb=short`.
- `just test-coverage` — tests with `--cov=app` XML/HTML/term reports.

**Build / packaging**

- `just build *ARGS` — init submodules, run `check`, then `distribute.py`
  (compiles translations via `translate run-all --lang all`).
- `just build-version VERSION` — same as `build` with an explicit `--product-version`.
- `just build-help` — show `distribute.py` help.

**Dependency / environment**

- `just dev-setup` — init submodules, `uv sync --locked --dev --group build`, then `i18n-compile`.
- `just update` — `uv lock --upgrade` (refresh dependencies).
- `just clean` — remove build artifacts, caches, and generated files.
- `just submodules-init` — `git submodule update --init --recursive`.
- `just install-hooks` — point git `core.hooksPath` at `.githooks`.

**Lint / format (auto-fix)**

- `just fix` — `ruff` + `shfmt-fix` + `markdownlint-fix`.
- `just ruff-fix` — `ruff check --fix`.
- `just ruff-format-fix` — `ruff format`.
- `just markdownlint-fix` — `npx markdownlint-cli2 --fix`.
- `just shfmt-fix` — format shell scripts with `shfmt` (unix: `fd`; windows: downloads shfmt).

**i18n**

- `just i18n-compile` — compile `locales/*.ts` → `*.qm`.
- `just i18n-update` — `pyside6-lupdate app/ -ts locales/*.ts` (extract strings).
- `just i18n-translate` / `i18n-validate` / `i18n-full` — AI translation pipeline
  via the CLI (`translate run-all`; pass flags with `ARGS`).

**CI / gate**

- `just ci` — `check` + test-coverage + `cov-gate` (full local CI simulation).
- `just check` — quality gate (Windows: typecheck + pyright + jscpd +
  deferred-imports + layer-check + i18n-check; Unix: super-lint + typecheck +
  pyright).
