# Contributing to pipeonjoy

Contributions are welcome. Read this before opening a PR.

## Ground rules

- This project is GPL v3. By contributing you agree your work is licensed under the same terms.
- No LLM-generated music logic — all theory rules, emotion maps, and pattern generators must be hand-coded and citable.
- No network calls at runtime — pipeonjoy must remain 100% air-gappable (except the optional v2.0 sample download tool, which is explicitly opt-in).
- No new runtime dependencies without discussion first. Keep the install footprint small.

## What to work on

Good first contributions:
- New SFZ instrument support (add to `audio/instruments.py` + `assets/sfz/`)
- Additional Surge XT preset mappings in `audio/instruments.py`
- More chord progression presets in `theory/chords.py`
- More emotion → parameter mappings in `wizard/lyrics_analysis.py`
- Tests for `wizard/lyrics_analysis.py` and `wizard/release.py`

v2.0 work (sample analysis):
- `wizard/sample_analysis.py` contains the full spec as comments — implement from there.

## How to submit

1. Fork the repo and create a branch: `feat/<short-description>` or `fix/<short-description>`.
2. Work inside a `.venv` — `pip install -e ".[dev]"`.
3. Run `pytest tests/ -v` before pushing.
4. Open a PR with a clear description of what changed and why.
5. One logical change per PR. No layer-split commits.

## Commit format

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.  
Lowercase. Present-tense imperative. No AI attribution in commit messages.

## Code style

- Comments: 1-line max — no block comments.
- Bug fixes at the root cause — never patch tests to make them pass.
- No dead code or commented-out blocks.
