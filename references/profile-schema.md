# Profile schema

Store profiles under `~/.invoice-reimbursement/profiles/` or `$INVOICE_REIMBURSEMENT_HOME/profiles/`. Never store secrets here.

```json
{
  "version": 2,
  "profile_name": "work",
  "usage_mode": "personal",
  "reimbursement_people": ["张三"],
  "ask_person_each_batch": false,
  "output_root": "/absolute/output/path",
  "companies": [
    {
      "id": "example-company",
      "name": "示例科技有限公司",
      "tax_id": "91310000XXXXXXXXXX",
      "address": "",
      "phone": "",
      "bank": "",
      "bank_account": "",
      "template": {
        "mode": "generic",
        "path": "",
        "sheet": "报销说明",
        "start_row": 3,
        "title_cell": "A1",
        "columns": {
          "category": "A",
          "description": "B",
          "unit_price": "C",
          "unit": "D",
          "quantity": "E",
          "total": "F",
          "has_invoice": "G",
          "file_name": "H"
        },
        "total_column": "F"
      }
    }
  ],
  "email_accounts": [
    {
      "id": "mail-1",
      "address": "zhangsan@example.com",
      "provider": "auto",
      "folder": "INBOX",
      "company_id": "",
      "enabled": true
    }
  ],
  "rules": {
    "require_original_pdf": true,
    "categories": ["住宿", "机票", "打车", "餐饮", "其他"],
    "clarification_mode": "consolidated"
  },
  "monitoring": {"enabled": false, "preset": "daily-0900"},
  "onboarding": {"completed": true}
}
```

Required for a complete profile: `profile_name`, `output_root`, one reimbursement person or `ask_person_each_batch`, at least one company with `name`, `tax_id`, and template mapping, plus an explicit monitoring choice. Email may be skipped only when the user chooses a non-email collection source.

Keep `company_id` empty for a general mailbox. Route invoices after extraction using buyer name and tax ID. Set it only when the mailbox account is dedicated to exactly one company.
