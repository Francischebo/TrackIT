# Docker guide

This guide explains how to build and run the project in Docker locally, and how to use the CI-ready `Dockerfile.ci` for reproducible builds in CI pipelines.

Local development (quick, interactive)

1. Build a development image (uses `Dockerfile`):

```powershell
docker build -t assets-inventory-dev -f Dockerfile .
```

2. Run an interactive container with the project mounted so edits are reflected immediately:

```powershell
docker run --rm -it -v ${PWD}:/app -w /app assets-inventory-dev bash
```

Use the container shell to run management commands, e.g. `python -m pip install -r requirements.txt` or `python run.py`.

CI / reproducible build (recommended)

Use `Dockerfile.ci` in CI pipelines to ensure dependencies are installed in a controlled builder stage and copied into a minimal runtime image.

Example build command (CI or locally):

```bash
docker build -t assets-inventory-ci -f Dockerfile.ci .
```

The `Dockerfile.ci` is optimized for:
- Installing system-level build deps only in the builder stage
- Producing a small final image that contains only runtime files and installed Python packages
- Running as a non-root `app` user

Example GitHub Actions snippet to build and run tests inside the CI image:

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build CI image
        run: docker build -t assets-inventory-ci -f Dockerfile.ci .
      - name: Run tests in container
        run: |
          docker run --rm -v ${{ github.workspace }}:/app -w /app assets-inventory-ci python -m pytest -q
```

Notes and recommendations
- Keep `requirements.txt` up to date; `Dockerfile.ci` uses it directly.
- For production images you may add a pinned base image digest for immutability.
- If your app requires environment variables or secrets, inject them via the CI system or Docker runtime options (avoid baking secrets into images).
