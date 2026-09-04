# Spreadsheet Benchmark

> Evaluates `features/23_spreadsheet_intelligence/`-relevant reasoning — parsing accuracy and
> correct use of the Calculator Tool for derived values.

## Method

Fixed workbooks with known correct answers to questions requiring formula/cell reasoning;
scored on: parsing correctness (are cells/formulas read accurately) and calculation
correctness (does the model correctly delegate numeric computation to the Calculator Tool
rather than computing "in its head" — per `industrial/10_engineering_calculations.md`'s rule).
