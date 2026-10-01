# Security Policy

## Reporting a vulnerability

Please do not report exploitable security issues in a public issue or pull request. Use GitHub's **Report a vulnerability** option in the repository's Security tab when it is available. If that option is unavailable, contact the repository owner using the contact options on the GitHub profile for `deswalgeetika03` and include enough detail to reproduce the issue safely.

Reports are handled on a best-effort basis. Please allow time for a response and avoid publicly disclosing the issue before maintainers have had a reasonable opportunity to assess it.

## Supported versions

This is an actively changing prototype. Only the latest code on the default branch is considered for security fixes; no release branches or response-time guarantees are currently defined.

## Secrets and sensitive data

- Never commit API tokens, `.env` files, `.dev.vars` files, credentials, or private health information.
- Treat any credential accidentally committed as exposed: revoke or rotate it, then report the incident privately.
- Use environment variables or the deployment platform's secret store for credentials.
