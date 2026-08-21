# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an email to **[INSERT SECURITY EMAIL]**. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours of your report
- **Initial Assessment**: Within 1 week
- **Fix or Mitigation**: Within 2 weeks for critical vulnerabilities
- **Public Disclosure**: After the fix is released

## Disclosure Policy

We follow a coordinated disclosure process:

1. **Report received** — We acknowledge receipt and investigate
2. **Confirmation** — We confirm the vulnerability and assess severity
3. **Fix developed** — We develop and test a fix
4. **Release** — We release the fix in a new version
5. **Disclosure** — We publicly disclose the vulnerability with credit to the reporter

## Security Best Practices

When using this package:

- Keep dependencies updated: `pip install --upgrade -e .[dev]` from the cloned source tree
- Use virtual environments to isolate dependencies
- Review configuration files before use
- Do not expose sensitive data in logs or outputs
- Validate all input data from untrusted sources

## Scope

This security policy applies to:

- The `convexfolio` Python package
- Official GitHub repository: `sachncs/convexfolio`
- Documentation and examples in this repository

## Recognition

We appreciate the security research community and will acknowledge reporters who help improve the security of this project (unless they prefer to remain anonymous).

## Contact

For security-related inquiries, please contact:

- **Email**: [INSERT SECURITY EMAIL]
- **GitHub**: Create a private security advisory via the "Security" tab
