# Invoice checks

Require exact, auditable values for buyer, tax ID, invoice number, issue date, seller, amount, currency, source file, and SHA-256.

Flag:

- buyer name or tax ID mismatch;
- duplicate hash or invoice number;
- red/negative invoice without a matched blue invoice;
- image/screenshot when original PDF is required;
- missing amount, date, or invoice number;
- Excel row without exactly one source file;
- source file not represented in either the workbook or exception report.

Never infer a missing legal identifier from neighboring invoices. Keep long invoice numbers as text, not floating-point numbers.
