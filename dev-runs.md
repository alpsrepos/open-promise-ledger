# Development runs (development set only)

27 November 2026, H&M reference case (website terms allow AI use), extraction prompt development version 0.1, model claude-opus-5-5, each run in a fresh agent context in this project, no web.

| Run | Pack | Rows (instruments, promises, links, observations) | Quote check |
|---|---|---|---|
| hm-A | full (13 sources) | 1, 3, 3, 26 | 23 of 23 found |
| hm-B | full | 1, 3, 3, 27 | 2 reported by the run as failing (OCR misread, column layout) |
| hm-trap | without the 2025 progress report | 1, 3, 3, 20 | 20 of 20 unsupported under the old check: table rows joined into one line |

Results against the final record (scripts/readings.py):
- Both readings found the three promises, with the same direction, promised value (30, -20, -10), observation dates (2025-11-28, 2025-08-31, 2024-12-31) and reporting deadline (2026-04-30) as the record. No core number differed.
- Trap run: no 2025 result and no statement was entered; the links were flagged "report not obtained". No invented values.
- Differences were all in form: free-text units and metric descriptions, page cells with words ("2 (image page)"), periods written in words, extra columns, and observations for interim years (26 and 27 rows against 5 in the record).

Changes made (development version 0.2): dictionary columns only; page as digits; periods and dates in ISO form; units as printed; table figures quoted as "row label | column heading | cell"; interim figures kept out of observations.csv (Method, Observation); the frame row (group_key and LEIs) supplied in the pack. The quote check now reads each page three ways (pypdf, pdftotext -layout and -raw), checks table parts separately and uses the OCR text with a tolerance for image pages; scripts/readings.py matches rows by content, not by id.

## Prompt development version 0.2, 27 November 2026

| Run | Pack | Rows (instruments, promises, links, observations) | Quote check |
|---|---|---|---|
| hm-v02 | scripts/build_pack.py (18 files; files over 100 pages cut to search-term pages, two pages either side) | 1, 3, 3, 7 | 10 of 10 found, after the check learned to match hyphenated words broken at a line end |

Against the final record: same three promises, directions, values, observation dates and deadline; observations now limited to the observation period (7 rows: the absolute figure and the change against each baseline), pages as digits, units as printed, no extra columns. Remaining differences are the record's own longer free-text units and metric descriptions, which the record will follow in the new form, and whether baseline_value holds the issuer's reported baseline when the terms state none (to settle on the pilot). scripts/readings.py now compares sources by file hash, so packs that number sources differently compare.

## AI blind coder development run, 27 November 2026

| Run | Model | Result against the final record |
|---|---|---|
| coder-hm | claude-fable-5-2, fresh context, files indexed by type only | Same 3 promises, directions, values, observation dates and deadline; same status, basis and consequence code on all 3 links; same flags. Differences in form only (free-text units, table quotes joined in layout order, page 2 against 3 for figures printed on both pages); first_call_date not in its sheet (an AI-filled field outside the coder's sheet). 123 of 123 quotes on their pages by its own check. |

Changes to the coder instructions: an evidence sheet (entry-evidence.csv) for source, page and quote per value; table figures quoted by parts; a training/ folder for Appendix A and the pilot records, which resolves the conflict the run reported between "read the pilot records" and "open no records".
| coder-enel | claude-fable-5-2 | Same promise, value, direction, observation date, deadline (270-day fallback), reported value, status and basis on all 5 links, same states. One disagreement: consequence code "stated as applied" (from a class statement without ISINs) against "announced" in the record; settled by the editor with rule E.10.15 (record stays "announced"). It read two OCR files of the restricted Teleborsa copy by accident and used nothing from them; the restricted copy's OCR files are now moved out of the evidence folder. |

## AI auditor development runs, 27 November 2026 (claude-sonnet-5-5, records with 6 planted errors each)

H&M: 5 of 6 planted errors caught, no false findings, plus one real minor error in the record (Deloitte named on S-3 p.8, not p.7; fixed). Enel: all 6 found, one logged under the wrong field. Both missed or mislabelled the planted page number because the audit sheet had no line for the cited source and page; scripts/audit_sheet.py now adds them as lines to check, and link lines no longer point to the statement's source for the consequence fields.
