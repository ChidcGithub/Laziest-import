# Security Policy

## Supported Versions

We are committed to maintaining the security of laziest-import. Currently, we support the following versions:

| Version | Supported         |
| ------- | ----------------- |
| 0.0.5-pre8 | ✅ |
| 0.0.5-pre7 | ✅ |
| 0.0.4 | ✅ |
| 0.0.3 | ❌ |
| < 0.0.3 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability in laziest-import, please report it to us as soon as possible. We take all security issues seriously and will work to address them promptly.

### How to Report

To report a security issue, please:

1. **DO NOT** open a public issue on GitHub
2. Email the maintainers at [your-email@example.com] with the details
3. Include in your report:
   - A description of the vulnerability
   - Steps to reproduce the issue
   - Any relevant code or examples
   - Potential impact of the vulnerability
4. We will acknowledge your report within 48 hours
5. We will work to resolve the issue and release a fix as soon as possible

### What to Expect

- **Acknowledgment**: You will receive an acknowledgment within 48 hours
- **Updates**: You will receive updates on the progress of the fix
- **Disclosure**: We will coordinate the disclosure with you once a fix is available
- **Credit**: We may credit you for the discovery unless you wish to remain anonymous

## Security Best Practices

When using laziest-import, please follow these best practices:

1. **Keep it Updated**: Use the latest stable version of laziest-import
2. **Auto-Install Wisely**: Use the auto-install feature carefully in production environments
3. **Limit Permissions**: Run Python with the minimum necessary permissions
4. **Review Dependencies**: Review third-party packages before installation
5. **Use Virtual Environments**: Isolate your Python environments

## Security Features

laziest-import includes the following security features:

- **Sandboxed Importing**: Modules are imported in a safe way
- **File Cache Security**: Cache files have restricted permissions
- **Input Validation**: All user inputs are validated
- **No Network Calls**: By default, no automatic network connections are made

## Disclosure Policy

When a security vulnerability is discovered and confirmed, we:

1. Confirm the vulnerability and determine affected versions
2. Develop a fix for the vulnerability
3. Test the fix thoroughly
4. Release the fix as a new version
5. Publish a security advisory on GitHub
6. Notify affected users through the issue tracker and release notes

## Scope

This security policy applies to:
- The laziest-import library itself
- The official repository on GitHub
- All distributions on PyPI and other package managers

## Questions

If you have any questions about our security policy, please contact us.

Thank you for helping keep laziest-import secure! 🔒
