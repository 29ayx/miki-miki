# 🔒 Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Miki Miki seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to [security@fdsyd.com](mailto:security@fdsyd.com).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

### Information to Include

- **Type of issue** (buffer overflow, SQL injection, cross-site scripting, etc.)
- **Full paths of source file(s) related to the vulnerability**
- **The location of the affected source code (tag/branch/commit or direct URL)**
- **Any special configuration required to reproduce the issue**
- **Step-by-step instructions to reproduce the issue**
- **Proof-of-concept or exploit code (if possible)**
- **Impact of the issue, including how an attacker might exploit it**

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Disclosure Policy

When we receive a security bug report, we will assign it to a primary handler. This person will coordinate the fix and release process, involving the following steps:

1. **Confirm the problem** and determine the affected versions.
2. **Audit code** to find any similar problems.
3. **Prepare fixes** for all supported versions. These fixes will be released as fast as possible to the main branch.

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.

## Security Best Practices

### For Users
- Keep Miki Miki updated to the latest version
- Use strong, unique API keys for Gemini AI
- Regularly review and rotate your API credentials
- Monitor your API usage for unusual activity
- Report any suspicious behavior immediately

### For Contributors
- Follow secure coding practices
- Validate all user inputs
- Use parameterized queries when applicable
- Keep dependencies updated
- Review code for potential security issues
- Test security-related changes thoroughly

## Security Features

Miki Miki includes several security features:

- **Local Data Storage**: Learning data is stored locally, not transmitted to external servers
- **API Key Protection**: API keys are stored locally and not logged
- **Input Validation**: All user inputs are validated and sanitized
- **Error Handling**: Secure error handling prevents information leakage
- **HTTPS Communication**: All external API calls use HTTPS

## Responsible Disclosure

We appreciate security researchers who:

- Give us reasonable time to respond to issues before any disclosure
- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our service
- Do not access or modify other users' data
- Do not perform actions that may negatively impact other users

---

**Developed by [Flash Dynamics Syndicate](https://fdsyd.com)**
