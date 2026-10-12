---
title: "Release Process"
---
# Release Process

How a new version of Convexfolio gets published.

> 📖 **New to releasing software?** See the
> [Glossary](/convexfolio/docs/glossary/) for terms like *commit*, *tag*, *SemVer*.

---

## What is a release?

A "release" is a named snapshot of the code. Once a release exists:

- It has a version number (e.g., `2.0.1`).
- It's tagged in git so you can find it later.
- It's described in `CHANGELOG.md` so people know what changed.

You'd cut a release when:

- You've fixed a bug users care about.
- You've added a feature.
- You've made a breaking change (this deserves a major version bump).

Releases are mostly administrative — there's no magic build step.

---

## What is SemVer?

[Semantic Versioning](https://semver.org/) is a convention for version
numbers. A version has three parts: `MAJOR.MINOR.PATCH`.

| Bump | When | Example |
|---|---|---|
| **MAJOR** | Incompatible change — old code will break. | `1.0.0` → `2.0.0` |
| **MINOR** | New feature, backwards-compatible. | `2.0.0` → `2.1.0` |
| **PATCH** | Bug fix, backwards-compatible. | `2.0.0` → `2.0.1` |

Examples:

- "I renamed the `Risk` class to use `CFVaR2nd` directly." → MAJOR
  (callers must update).
- "I added a `QualityScore` class." → MINOR (additions don't break
  anything).
- "I fixed a typo in a docstring." → PATCH.

Convexfolio uses SemVer.

---

## What is a git tag?

A "tag" is a named pointer to a specific commit. Tags are how
software marks releases in version control. ([Glossary: tag](/convexfolio/docs/glossary/))

```bash
git tag v2.0.0                  # tag the current commit as v2.0.0
git push origin v2.0.0          # push the tag to the remote
```

Once a tag exists, you can always check out that exact version of
the code:

```bash
git checkout v2.0.0
```

---

## The pre-release checklist

Run through these before cutting a release. Each item is a one-liner
explanation.

### Code quality

- [ ] **All tests pass.** Run the coverage-enabled command from CI; the suite
      must pass the 90% package and critical-module branch gates.
- [ ] **No type errors.** `mypy convexfolio` — should print
      `Success: no issues found`.
- [ ] **No lint errors.** `ruff check convexfolio tests scripts benchmarks`
      — should print `All checks passed!`.
- [ ] **Build succeeds.** `python -m build` — should produce
      `dist/convexfolio-X.Y.Z-py3-none-any.whl` and
      `dist/convexfolio-X.Y.Z.tar.gz`.
- [ ] **Site builds.** From `site/`, run `npm ci && npm run check && npm run build`.
- [ ] **Links and site invariants pass.** Run `python scripts/check_docs.py`
      and `python scripts/check_site.py`.

### Documentation

- [ ] **`CHANGELOG.md` updated.** Add a section for the new version
      with `### Added`, `### Changed`, `### Fixed`, etc.
- [ ] **`README.md` reflects current features.** Anything you added
      should be documented.
- [ ] **Examples still work.** Re-run any tutorial commands.

### Configuration

- [ ] **Version bumped in `pyproject.toml`.** The `version = "X.Y.Z"`
      line at the top of the file.

---

## The release steps

### 1. Make sure you're on master, up-to-date

```bash
git checkout master
git pull origin master
```

### 2. Bump the version

Edit `pyproject.toml`:

```toml
[project]
version = "2.0.1"            # or whatever the new version is
```

(If you're not sure what to bump, see [SemVer](#what-is-semver)
above.)

### 3. Update the changelog

Add a new section to `CHANGELOG.md`, just below `## [Unreleased]`:

```markdown
## [2.0.1] - YYYY-MM-DD

### Added
- Description of new feature.

### Changed
- Description of behaviour change.

### Fixed
- Description of bug fix.
```

Then add the link at the bottom of the file:

```markdown
[2.0.1]: https://github.com/sachncs/convexfolio/compare/v2.0.0...v2.0.1
```

### 4. Run the quality checks

```bash
ruff check convexfolio tests scripts benchmarks
mypy convexfolio
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
python -m build
```

All four must succeed.

### 5. Commit and tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v2.0.1"
git tag v2.0.1
```

### 6. Push

```bash
git push origin master
git push origin v2.0.1
```

### 7. (Optional) Create a GitHub release

If you want a fancy release page on GitHub:

1. Go to [github.com/sachncs/convexfolio/releases](https://github.com/sachncs/convexfolio/releases).
2. Click "Draft a new release".
3. Pick the tag you just pushed (`v2.0.1`).
4. Title: `v2.0.1`.
5. Description: paste the changelog section.
6. Attach the wheel and sdist from `dist/` (optional — most teams
   attach them, some don't).
7. Click "Publish release".

---

## Rollback and recovery

Releases and deployments are immutable records. Do not delete or force-move a
published tag to make a rollback look like a new release.

### Package rollback

The previous stable package remains available as the `v1.0.0` GitHub release.
Pin the application to that release while the v2 issue is investigated:

```bash
python -m pip install \
  https://github.com/sachncs/convexfolio/releases/download/v1.0.0/convexfolio-1.0.0-py3-none-any.whl
```

Confirm the installed version and run the CLI smoke test before restoring
service:

```bash
convexfolio --version
convexfolio --command print-report > /tmp/convexfolio-rollback-report.json
```

### Pages rollback

GitHub Pages deploys from `master`. For a site regression, identify the last
known-good commit that still contains the Astro site, create a recovery branch
from it, and merge a reviewed pull request into `master`:

```bash
git switch -c recovery/site <known-good-commit>
git push -u origin recovery/site
```

After the merge, the Pages workflow runs automatically. Verify the deployed
homepage and `/docs/architecture/` route before closing the incident. A
package rollback to `v1.0.0` is separate: that tag predates the Astro site and
must not be treated as an automatic Pages rollback target.

---

## Hotfix process

For critical bug fixes:

1. Branch from the release tag, not from `master`:

   ```bash
   git checkout -b hotfix/v2.0.2 v2.0.1
   ```

2. Make the minimum change needed.

3. Bump the PATCH version (`2.0.1` → `2.0.2`).

4. Follow the regular release steps above.

5. Merge back to `master` when done:

   ```bash
   git checkout master
   git merge hotfix/v2.0.2
   git push origin master
   ```

---

## Where to look next

- **[Glossary](/convexfolio/docs/glossary/)** — Every term used here.
- **[CHANGELOG.md](../../../../CHANGELOG.md)** — The changelog itself.
- **[Architecture](/convexfolio/docs/architecture/)** — How the package fits
  together.
- **[Deployment](/convexfolio/docs/deployment/)** — How to run the released
  version in production.
