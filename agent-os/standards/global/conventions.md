## General development conventions

- **Consistent Project Structure**: Keep the importable package under `stocksurferbd_pkg/stocksurferbd/`; keep example/driver scripts (`fetch_*.py`, `plot_*.py`) at the repo root. New public classes are exported from the package `__init__.py`.
- **Clear Documentation**: Keep `README.md` up to date — it is both the user guide and the PyPI long description. Every public method should have a copy-paste usage example there.
- **Version Control Best Practices**: Use clear commit messages and feature branches; describe what changed and why in PRs. See `CONTRIBUTING.md`.
- **Dependency Management**: Keep dependencies minimal and pinned. The pins in `requirements.txt` and `setup.py`'s `install_requires` must stay in sync; document why a dependency is added.
- **Versioning**: Bump the `version` in `setup.py` for every release (semantic versioning) and tag the release.
- **Release Process**: Build with `python setup.py sdist bdist_wheel`, then publish with `twine upload dist/*`.
- **Environment Configuration**: Never commit secrets. The library needs no credentials, but any future config (timeouts, user-agent, TLS verification) should be parameters/env vars, not hardcoded.
- **Changelog**: Note significant changes per release so users can see what each version adds or fixes.
