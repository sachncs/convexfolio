# Release Process

## Overview

This document describes the release process for the Optimal Option Portfolios package.

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** — Incompatible API changes
- **MINOR** — Backward-compatible functionality additions
- **PATCH** — Backward-compatible bug fixes

## Pre-Release Checklist

### Code Quality

- [ ] All tests passing: `PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q`
- [ ] No type errors: `mypy options`
- [ ] No lint errors: `ruff check src tests scripts`
- [ ] Code coverage acceptable

### Documentation

- [ ] CHANGELOG.md updated
- [ ] README.md reflects current features
- [ ] API documentation updated
- [ ] Examples working

### Configuration

- [ ] Version updated in `pyproject.toml`
- [ ] Dependencies reviewed and updated

## Release Steps

### 1. Prepare Release Branch

```bash
git checkout main
git pull origin main
git checkout -b release/vX.Y.Z
```

### 2. Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"
```

### 3. Update CHANGELOG.md

Add release date and section:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

### 4. Commit and Tag

```bash
git add .
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
```

### 5. Run Quality Checks

```bash
ruff check src tests scripts
mypy options
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
python -m build
```

### 6. Build Distribution

```bash
python -m build
```

### 7. Push

```bash
git push origin main
git push origin vX.Y.Z
```

### 8. Create GitHub Release

1. Go to GitHub Releases
2. Click "Draft a new release"
3. Select tag `vX.Y.Z`
4. Title: `vX.Y.Z`
5. Add release notes from CHANGELOG.md
6. Attach distribution files from `dist/`
7. Publish release

### 9. Publish to PyPI (When Ready)

```bash
pip install twine
twine upload dist/*
```

## Post-Release

- [ ] Verify GitHub release is correct
- [ ] Test installation from PyPI (when published)
- [ ] Update any dependent projects
- [ ] Announce release (if appropriate)

## Hotfix Process

For critical bug fixes:

1. Create hotfix branch from release tag
2. Make minimal fix
3. Bump patch version
4. Follow release steps above

## Release Notes Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Change description

### Fixed
- Bug fix description

### Removed
- Removed feature description

### Deprecated
- Deprecated feature description

### Security
- Security fix description
```
