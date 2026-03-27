# Security Policy

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security issues using [GitHub's private security advisory feature](https://github.com/sohan-a11y/gtm-engine/security/advisories/new). This ensures the report is only visible to maintainers until a fix is ready.

When submitting, please include:

- A clear description of the vulnerability
- Steps to reproduce (proof-of-concept code or curl commands are helpful)
- The potential impact (what an attacker could do)
- Your assessment of severity (critical / high / medium / low)

---

## Response Timeline

| Milestone | Target |
|-----------|--------|
| Acknowledge receipt | Within 48 hours |
| Confirm or dispute | Within 5 business days |
| Patch released | Within 14 days for critical/high; 30 days for medium/low |
| CVE published (if applicable) | After patch is available |

We will keep you informed throughout the process and credit you in the release notes unless you prefer to remain anonymous.

---

## Scope

The following are in scope:

- **Authentication bypass** — any mechanism that allows access without valid credentials
- **Authorization bypass** — accessing another organization's data by manipulating requests
- **SQL injection** — any user-controlled input reaching a raw SQL query
- **Remote code execution (RCE)** — arbitrary code execution on the server
- **Credential exposure** — stored integration tokens or API keys readable by unauthorized parties
- **JWT manipulation** — forging or tampering with JWT tokens to escalate privileges
- **Webhook signature bypass** — forging webhook requests without a valid HMAC signature

---

## Out of Scope

The following are **not** in scope:

- Rate limiting and denial-of-service attacks (we have rate limiting at Nginx and app level, but it is not hardened against determined DDoS)
- Social engineering or phishing of maintainers
- Vulnerabilities requiring physical access to the server
- Issues in third-party dependencies that have no practical exploit path in this application
- Self-XSS (attacks that only affect the attacker's own session)
- Missing security headers on non-sensitive routes
- Reports generated purely by automated scanners with no demonstrated impact

---

## Supported Versions

We provide security patches for the latest release on the `main` branch. Older tags do not receive backported security fixes.

---

## Disclosure Policy

We follow **coordinated disclosure**: we ask that you give us a reasonable window to fix the issue before publishing details publicly. We will reciprocate by fixing promptly and crediting your responsible disclosure.
