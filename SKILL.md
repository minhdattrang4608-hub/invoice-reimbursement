---
name: invoice-reimbursement
description: "Configure and run a reusable invoice reimbursement workflow: first ask the user to choose an email provider, then show that provider's specific authorization guide, test the connection, set scan scheduling and reimbursement rules, periodically collect and validate invoices, separate them by buyer company, and deliver only a company-formatted Excel workbook plus an original-invoice folder by default. Use after installing or invoking the Skill, or when a user mentions 发票、报销、邮箱绑定、邮箱抓取、报销表、Excel 模板、费用归档、缺票检查、定期收集发票、下一步怎么做."
---

# Invoice Reimbursement

Build a local, privacy-conscious reimbursement workflow. Keep the Skill generic; store all personal, company, email, template, and invoice data outside the Skill directory.

## Start every request

1. Run `python scripts/doctor.py`.
2. Run `python scripts/configure.py status --profile <name>` when a profile name is known; otherwise run `python scripts/configure.py list`.
3. If no complete profile exists, **immediately start** [onboarding.md](references/onboarding.md). Do not end after reporting installation, environment status, or missing configuration. Use the host's native choice/form UI when available; otherwise ask one short choice question per message.
4. Never ask users to retype information that can be inferred from an uploaded invoice, an Excel sample, an email domain, the operating system, or an existing profile.

When installation has just completed, say what the Skill will deliver and begin with the mailbox-provider choice. **Do not display any binding image before the provider is selected.** After selection, display only the matching provider guide listed in [email-binding.md](references/email-binding.md). A Skill package cannot force every host to open a post-install screen; the default prompt and this rule make the first invocation enter onboarding immediately.

Missing PDF or Excel dependencies do not block mailbox onboarding. Report them briefly and continue; request permission to install them only before invoice extraction or workbook generation.

## First-time setup

Follow this user-facing order and save only confirmed values:

1. **Choose email first.** Offer `QQ 邮箱（推荐） / 163或126 / Gmail / Outlook或Microsoft 365 / 企业邮箱 / 暂不绑定`. Do not show a generic binding guide. Read [email-binding.md](references/email-binding.md) and display the selected provider's guide only after the user chooses.
2. Infer the provider from the address. Ask only for the address and the provider-supported authorization method; default the folder to `INBOX`. Never imply every provider uses the same kind of authorization code.
3. Store secrets in the operating-system credential store via `scripts/configure.py secret-set`; never put them in profile JSON, logs, ZIPs, workbooks, or chat summaries. Test with `python scripts/mail_fetch.py test --profile <name> --account-id <id>` before fetching attachments.
4. **Choose monitoring time.** Offer `每天 09:00（推荐） / 每天 22:00 / 每 6 小时 / 每周一 09:00 / 自定义每天时间 / 暂不开启`. Preview first and install only after explicit confirmation.
5. **Configure reimbursement details.** Infer the profile name, usage mode, output folder, and reimbursement person. Use `张三` for examples; never reuse a prior user's identity or company data.
6. Prefer extracting company billing information from one valid invoice. Show the extracted company name and tax ID and ask `确认 / 修改 / 稍后配置`. Support multiple companies.
7. Prefer analyzing a completed or blank company Excel reimbursement template. Preserve it and save a field mapping; offer the bundled generic template only when no company template exists.
8. Infer categories, description formats, and original-file rules from the historical Excel. Summarize settings once and ask for final confirmation.

Save confirmed non-secret answers with:

```bash
python scripts/configure.py save --profile <name> --answers <answers.json>
```

See [profile-schema.md](references/profile-schema.md) for the JSON schema and template mapping fields.

## Collect invoices

Fetch new email attachments without modifying the mailbox:

```bash
python scripts/mail_fetch.py fetch --profile <name>
```

Add files supplied directly by the user to the profile inbox, preserving the originals. Accept PDF, OFD, JPG, JPEG, PNG, HEIC, WebP, and safe ZIP archives. Treat screenshots and images as evidence requiring an original PDF unless the company explicitly accepts images.

Keep general mailbox downloads in an unassigned staging folder unless an account is explicitly dedicated to one company. During review, route each invoice by its parsed buyer name and tax ID. Never assume every attachment is an invoice, and never count downloaded attachments as confirmed invoices.

Do not claim that background monitoring means an Agent is reasoning continuously. The local scheduler only downloads and pre-indexes attachments; the Agent performs visual review and final reconciliation during an active run.

## Prepare and review a batch

Scan a profile inbox:

```bash
python scripts/invoice_pipeline.py scan --profile <name> --company <company-id> --project <project> --person <person>
```

Read the generated manifest and inspect every ambiguous source visually. Validate at minimum:

- buyer name and tax ID;
- invoice number, issue date, seller, tax-inclusive amount;
- category and company-specific description rule;
- duplicate file hash and duplicate invoice number;
- red/negative invoice and its matching blue invoice;
- original PDF availability;
- workbook row-to-source-file traceability.

Set `include: true` only for confirmed records. Ask one consolidated clarification containing all unresolved items; do not interrupt once per invoice. Never invent a missing value.

## Generate deliverables

After review, package the manifest:

```bash
python scripts/invoice_pipeline.py package --manifest <manifest.json>
```

Deliver one folder per company/batch containing:

- the company-formatted Excel reimbursement workbook;
- `发票/` with only the untouched originals corresponding to included Excel rows.

Default delivery must contain exactly those two items. Keep manifests, hashes, excluded files, missing-PDF lists, red-invoice matches, and review notes in the private working data directory, not the delivery folder. Create an audit ledger, exception sheet, or extra folders only when the user explicitly requests them; then run `package` with `--include-audit-materials`.

Inspect formulas and render every workbook sheet before reporting completion when the host has spreadsheet rendering tools. Ensure every included Excel row points to exactly one archived source file.

## Local monitoring

Preview the scheduler first:

```bash
python scripts/schedule_local.py preview --profile <name> --preset daily-0900
```

Install only after the user explicitly approves:

```bash
python scripts/schedule_local.py install --profile <name> --preset daily-0900 --confirm
```

For a custom daily time, use `--daily-time HH:MM` instead of `--preset`.

Use `status` and `uninstall --confirm` for management. Local schedules run only while the device can execute background tasks.

## Portability

Use this directory as an Open Agent Skills package. Skills-compatible agents load `SKILL.md` directly. On hosts without Skill loading, unpack the ZIP, provide `SKILL.md` as operating instructions, and run the portable Python scripts. Read [portability.md](references/portability.md) before adapting platform-specific forms, schedulers, spreadsheet tools, or secret stores.

## Safety rules

- Keep credentials and personal configurations outside the Skill directory.
- Never delete or alter mailbox messages by default.
- Never overwrite source invoices or the user's Excel template.
- Never enable a scheduler, install dependencies, or access an email account without explicit permission.
- Prefer local processing and least-privilege access.
- Flag uncertainty instead of guessing.
