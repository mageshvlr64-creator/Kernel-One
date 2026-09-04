# Spreadsheet Analysis

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

features/23_spreadsheet_intelligence

## Steps

1. User uploads an XLSX workbook
2. Spreadsheet Intelligence parses sheets, formulas, and tables (features/23_spreadsheet_intelligence/02_workbook_parsing.md)
3. Agent answers questions using the Calculator Tool for any derived numeric claim (REQ never allows a numeric claim without a calculator-verified computation, features/07_calculator_tool/05_deterministic_verification.md)
4. Optionally generates a chart artifact (features/23_spreadsheet_intelligence/11_chart_generation.md)

## Notes

—
