# invoice-reimbursement

A local, privacy-conscious invoice reimbursement workflow skill.

- Collects invoice attachments from configured email accounts (QQ / 163 / 126 / Gmail / Outlook / enterprise) over IMAP, read-only.
- Validates invoices: buyer name and tax ID, invoice number, issue date, seller, tax-inclusive amount, category, original-PDF rule, duplicates, red invoices.
- Routes invoices by buyer company and delivers one folder per company/batch: a company-formatted Excel workbook plus an `发票/` original-invoice folder.
- Optional local scheduler (LaunchAgent / cron) for daily invoice monitoring.

Usage: see `SKILL.md`. All personal, company, email, and invoice data stays outside the skill directory; credentials are stored in the OS credential store.
