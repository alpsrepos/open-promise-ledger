# Frame registration: Open Promise Ledger, phase 1

Zenodo DOI: [10.5281/zenodo.24572399](https://doi.org/10.5281/zenodo.24572399) (public record, restricted files), published 26 November 2026.

Registered by Ismet Alp Ceylan (ORCID 0000-0001-7478-6227) on 26 November 2026, before the seed is known and before any group is screened. Method version 0.1 (METHOD.md in this repository at the tagged commit `frame-v1`).

## 1. Inputs

| Input | Retrieved | SHA-256 |
|---|---|---|
| Euronext ESG bonds list, CSV exported from the download on www.euronext.com (restricted file: Euronext's terms of use do not allow republication) | 26 Nov 2026 | `c8c068bef65c3813f8bbead3a461d7d777883d32477916c88a08664d71cc0c5f` |
| GLEIF ISIN-LEI mapping, `isin-lei-20261126T081510.zip` (CC0) | 26 Nov 2026 | `8f66113ff535619d3d90d67edda0a58ff37af1ddce4d525901787feed0b865bb` |
| GLEIF LEI records and ultimate-parent relationships, API, golden copy of 26 Nov 2026 16:00 UTC (CC0) | 26 Nov 2026 | queried live by `scripts/build_frame.py` |
| Archive check (protocol/archive-check.md): first capture on or after 31 Dec 2023 holds no readable list; nothing added | 26 Nov 2026 | see that file |

## 2. Frame (restricted files, same deposit)

| File | Contents | SHA-256 |
|---|---|---|
| `frame-bonds.csv` | 213 ISINs typed "Sustainability-Linked Bond", with LEI, LEI source and issuer group | `1a478ecd67a56cdfe3168e372d1a108a71ef060a535388342c028ab47f029b4b` |
| `frame-groups.csv` | 106 issuer groups (GLEIF ultimate parent), 75 with a bond first listed by 31 Dec 2023 | `84f314e3864a132c12a2d84905e3f122fd57134dfcab47a5b31a32dd194fe783` |
| `name-match-picks.json` | LEIs chosen by name match, checked against GLEIF | `490058425c7589364f750cdc1c36135d51ead4cca1c5a5f1cd21c3fd504d8268` |
| `isin-overrides.json` | LEIs set ISIN by ISIN after the check | `13d0b494284341f22e518a24d92c8aff4639b2fb0bb089b16e35e7a775dbe17e` |

Code: `scripts/build_frame.py` (`3e10eda032baa8d3a7326a4af95715bdf7973f914a3131e06a9b39b7fac11bb9`), `scripts/order.py` (`028ad5e1732af9339da7974cdf71a07c78120d1f72621bbd9f22f8642837df7e`).

## 3. Random order (Method section 3, Appendix D)

- Sort key: group key (GLEIF ultimate-parent LEI; "NOLEI:" plus the issuer label where no LEI exists).
- Software: Python 3 (built with 3.13), `random.Random(seed).shuffle` on the sorted list, as in `scripts/order.py`.
- Seed: the five main numbers and two Lucky Stars of the first EuroMillions draw held after this deposit is published, in the order drawn as published by the operator, each written as two digits and joined into one integer (for example 5, 12, 23, 34, 45, stars 3, 9 gives 5122334450309).
- The ordered list `order.csv` and its SHA-256 are added to the record as a new version of this deposit, without changing anything above.

## 4. Inclusion and stopping (from Method E.3, unchanged)

Groups are screened one by one in the order. A group is in scope if at least one of its bonds in the frame was listed on or before 31 Dec 2023, its reporting entity has its legal address in the EEA, the United Kingdom or Switzerland, and its terms contain a target with an observation date in 2024 or 2025. The first three in-scope groups are the pilot. Wave 1 continues until ten in-scope groups reached by the order have been coded, pilot included.

## 5. Central and Eastern European stratum

Countries (legal address of the reporting entity): Bulgaria, Croatia, Czechia, Estonia, Hungary, Latvia, Lithuania, Poland, Romania, Slovakia, Slovenia. Source: the eleven Central and Eastern European member states of the European Union that joined in 2004, 2007 and 2013. If more than four such groups are in scope, the first four in the order are coded in wave 1.

## 6. Reference cases known before registration

Enel, Eni and PPC (Method Appendix A). If drawn, they are coded, flagged "reference case" and kept out of the blind coding and the held-out set.
