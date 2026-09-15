# Portability

The package follows the Open Agent Skills directory convention. Portability has three levels:

1. Instructions: every host can read `SKILL.md` and references.
2. Scripts: require Python 3.10+; PDF extraction improves when `pdftotext` or `pypdf` is available; Excel export requires `openpyxl` or a host spreadsheet tool.
3. Host integration: forms, credential stores, background scheduling, and visual spreadsheet/PDF inspection differ by platform.

Use native host forms for onboarding when available. Fall back to concise numbered choices. Use native spreadsheet tools when they can preserve a complex company template better than `openpyxl`.

Local scheduling support:

- macOS: LaunchAgent.
- Linux: user crontab when available.
- Windows: generate Task Scheduler instructions unless a trusted scheduler API is available.

Do not claim one-click installation on a host that does not implement Skill import. In that case, unzip the package, load `SKILL.md`, and expose the scripts as tools or function calls.
