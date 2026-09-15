# Low-effort onboarding

## Goal

On first invocation, lead the user from mailbox selection to a ready reimbursement profile. Never stop at “installed successfully.” Ask one choice question at a time and infer everything available from artifacts.

## Opening screen

Show a concise welcome:

> 发票报销助手已就绪。接下来我会带你完成：选择并绑定邮箱 → 选择扫描时间 → 确认公司和报销规则 → 生成可复用配置。完成后，定时任务负责收集附件，Agent 在活跃任务中审核；默认交付只有一个 Excel 和一个发票文件夹。

Ask Screen 1 immediately. Do not display any binding image on this opening screen.

## Screen 1 - Mailbox provider

Offer:

- `QQ 邮箱（推荐）`
- `163 / 126 邮箱`
- `Gmail`
- `Outlook / Microsoft 365`
- `企业邮箱 / 自定义 IMAP`
- `暂不绑定，只使用对话上传`

After selection, load [email-binding.md](email-binding.md), display only the selected provider's guide, and then ask for the email address. Infer the provider and default folder to `INBOX`. Do not ask for company information yet.

## Screen 2 - Authorization and connection test

Explain that an authorization code or app password is not the normal login password. Tell the user where to enable IMAP using concise provider-specific guidance. Never ask them to paste a normal password.

Store the code with:

```bash
python scripts/configure.py secret-set --profile <name> --account-id <id>
```

Test without downloading attachments:

```bash
python scripts/mail_fetch.py test --profile <name> --account-id <id>
```

If the test fails, translate the error into one fix at a time. Do not proceed as if the mailbox were connected.

## Screen 3 - Monitoring time

Offer:

- `每天 09:00（推荐）`
- `每天 22:00`
- `每 6 小时`
- `每周一 09:00`
- `自定义每天时间`
- `暂不开启`

Explain that the computer must be awake and able to run background tasks. Preview the schedule, show the exact local time and Python runtime path, and obtain explicit approval before installing it. Prefer a persistent runtime under the reimbursement data directory; warn when a temporary workspace interpreter would be scheduled.

## Screen 4 - Person and destination

Infer the operating-system username and Desktop path.

- Usage: `个人使用（推荐） / 团队共用`
- Output: `桌面（推荐） / Documents / 自选文件夹`
- Reimbursement person: show an inferred value only when it is reliable; otherwise use `每次询问`.

Use `张三` only as an example, never as an inferred real value.

## Screen 5 - Company information

Offer:

- `上传一张完整公司抬头发票，自动识别（推荐）`
- `粘贴开票信息`
- `稍后配置`

Infer company name, tax ID, address, phone, bank, and account. Display extracted values and ask `全部正确 / 修改某项 / 再传一张`.

Support multiple companies. Leave a mailbox account unassigned by default so invoices can be routed later by buyer name and tax ID. Ask `还要添加另一家公司吗？ 不需要（推荐） / 添加`.

## Screen 6 - Reimbursement workbook

Offer:

- `上传一份历史已完成 Excel，自动学习（推荐）`
- `上传空白模板`
- `使用通用模板`

Infer sheet name, first data row, columns, formulas, totals, merged cells, formatting, and naming conventions. Never edit the source template. Show a compact mapping preview and ask `使用此映射 / 调整 / 改用通用模板`.

## Screen 7 - Rules

Infer category and description formats from the historical Excel. If no sample exists, offer:

- Category set: `差旅常用（住宿/机票/打车/餐饮） / 通用 / 自定义`
- Original requirement: `必须有 PDF（推荐） / 图片也可 / 按类别设置`
- Ambiguities: `集中询问后再生成（推荐） / 先生成草稿`

## Final confirmation

Show one compact summary: mailbox connection, monitoring, reimbursement person, companies, template, rules, output folder, and unresolved fields. Choices: `完成配置 / 返回修改 / 先保存但不启用监控`.

After confirmation, run one incremental fetch. Explain that downloaded attachments are only candidates: review and buyer-based routing still happen before Excel generation.
