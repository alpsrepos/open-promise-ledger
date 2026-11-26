# Open Promise Ledger

An open record of the measurable targets that issuers set in sustainability-linked bonds, and of what the issuers and their external reviewers later published about them.

The Ledger does not rate, score or rank issuers or instruments, and does not propose or suggest any investment decision. It records what issuers stated, with the page and the quote.

**Status: draft, phase 1 set-up.** One student editor, not yet independent. Nothing in this repository is a release yet.

Editor: Ismet Alp Ceylan (ORCID [0000-0001-7478-6227](https://orcid.org/0000-0001-7478-6227)), a student at Bocconi University. This is not a publication of the university.

## What is here

| Folder | Contents |
|---|---|
| `METHOD.md` | The Method, version 0.1, draft for comment |
| `dictionary/` | The data dictionary (`data-dictionary.md`) and the schema the checks use (`schema.json`) |
| `frame/` | The sampling frame built from the Euronext ESG bonds list, grouped by GLEIF ultimate parent; see `frame/README.md` |
| `data/` | The five record tables (empty until the pilot) |
| `scripts/` | Record checks, random order, quote check, comparison |
| `tests/` | Tests run on every change |
| `protocol/` | Logs: deviations, AI runs, searches, corrections |
| `docs/` | The website at openpromise.org |

## Run the checks

```
pip install pytest pypdf
python -m pytest -q tests
python scripts/checks.py --words
```

## Licences

Data and text by the project: [CC BY 4.0](LICENSE-DATA.md). Code: [MIT](LICENSE). Quotes from issuer documents and the documents themselves stay with their rights holders and are not covered by these licences.

## Corrections

Open an issue, or write to the address on openpromise.org. Corrections are accepted with a public source.
