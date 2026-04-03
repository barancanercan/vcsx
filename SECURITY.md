# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 5.x     | ✅ Active |
| 4.x     | ⚠️ Critical fixes only |
| < 4.0   | ❌ Not supported |

## Reporting a Vulnerability

If you discover a security vulnerability in vcsx, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer or use GitHub's private security advisory feature:
→ https://github.com/barancanercan/vcsx/security/advisories/new

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Time
- We aim to respond within 48 hours
- We'll provide a fix timeline within 1 week

## Security Best Practices for vcsx Users

vcsx generates AI coding environment configs. To keep your projects secure:

1. **Never store secrets in AI config files** (CLAUDE.md, GEMINI.md, AGENTS.md)
2. **Add `.env` to `.gitignore`** — use `vcsx validate` to check
3. **Review generated hook scripts** before enabling them
4. **Keep vcsx updated** — `pip install --upgrade vcsx`
5. **Use `.claudeignore`** to prevent AI from reading sensitive files

## Known Behaviors

vcsx's `secret_scan.sh` hook scans for common secret patterns (API keys, tokens).
This is a best-effort scan and should NOT be your only security measure.
Use dedicated tools like `gitleaks` or `truffleHog` for comprehensive secret scanning.
