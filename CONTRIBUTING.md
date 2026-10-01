# Contributing to Wellness AI

Thanks for considering a contribution. This is a research and engineering prototype for general well-being information, not a clinical product.

## Before you start

- Search existing issues and pull requests to avoid duplicate work.
- For substantial changes, open an issue first to discuss the approach.
- Do not include private health information, credentials, API tokens, local database files, or machine-specific paths.
- Do not present the system as a diagnostic tool or claim clinical validation.

## Local setup

Follow the setup sections in the [README](README.md). In brief, the Python environment uses `requirements.txt`; the frontend is in `wellness_ai_frontend_phase3B/wellness_ai_frontend`; and the Cloudflare Worker is in `cloudflare-deployment`.

Run checks for the area you change:

```text
python Tests/test_all.py
```

```text
cd cloudflare-deployment
npm ci
npm test -- --run
```

```text
cd wellness_ai_frontend_phase3B/wellness_ai_frontend
npm ci
npm run build
```

Worker tests that use remote Cloudflare bindings may require configured Cloudflare test credentials. Never commit those credentials. If an environment prevents a check from running, include the command and limitation in the pull request.

## Changes and evaluation claims

- Keep changes focused and explain user-visible or safety-relevant behavior.
- Add or update tests for code changes.
- Preserve frozen evaluation results. Report later measurements separately and describe their dataset and limitations.
- Do not silently reconcile conflicting evaluation artifacts. Record the discrepancy and its source.
- Update documentation when runtime behavior changes, and distinguish local behavior from production behavior.

## Pull requests

Use the pull request template. Include a concise summary, test results, documentation changes, and any remaining risks or known limitations. Be respectful and responsive during review.
