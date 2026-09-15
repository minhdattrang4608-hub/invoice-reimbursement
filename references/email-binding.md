# Email binding

Use this reference only after the user chooses a provider. Never display a generic guide on the opening screen. Provider interfaces may change; describe the current visible labels and fall back to the provider's official help when they differ.

## Shared safety rule

- Request the provider-supported authorization method, never the normal login password.
- Keep the mailbox read-only and use `INBOX` unless the user chooses another folder.
- Store the secret in the operating-system credential store.
- Run `mail_fetch.py test` before the first fetch.

## QQ and Foxmail

Display `assets/email-guide-qq.png`. Guide the user to mailbox settings, enable IMAP/SMTP, complete the provider's identity verification, and generate a QQ authorization code. The code is used once for local credential storage. The IMAP host is `imap.qq.com` on port `993`.

## 163 and 126

Display `assets/email-guide-163.png`. Guide the user to POP3/SMTP/IMAP settings, enable IMAP/SMTP, and create a client authorization password. Hosts are `imap.163.com` or `imap.126.com` on port `993`.

## Gmail

Display `assets/email-guide-gmail.png`. Prefer OAuth or “Sign in with Google.” When only this portable IMAP script is available, use a 16-character app password only for an account with 2-Step Verification and app passwords enabled. Gmail IMAP is on by default for personal accounts. If app passwords are unavailable, offer Agent upload or a supported OAuth email connector.

## Outlook and Microsoft 365

Display `assets/email-guide-outlook.png`. Require a host-provided Microsoft OAuth connector or an OAuth-capable adaptation. Exchange Online has disabled Basic Authentication for IMAP; an ordinary password or app password is not a valid fallback for this portable script. If OAuth is unavailable, offer Agent upload rather than requesting a password.

## Enterprise or custom IMAP

Do not display one generic binding image. Ask for the email address, IMAP host, TLS port, and administrator-approved authorization method. Do not guess a server hostname or claim OAuth support that the host does not provide.
