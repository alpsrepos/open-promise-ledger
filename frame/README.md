# Frame, draft (not yet registered)

The frame tables are not published: Euronext's terms of use do not allow its list to be republished or compiled into a database without written permission, which has been requested. This file, the hashes and the code are public; the tables go to Zenodo with restricted access. Anyone who downloads the same list can rebuild the frame with `scripts/build_frame.py` and compare the hashes.

Built on 26 November 2026 from the Euronext ESG bonds list and GLEIF data, by `scripts/build_frame.py`.

| Input | Date | SHA-256 |
|---|---|---|
| Euronext ESG bonds list, all bond types, 4,239 rows (CSV exported by the editor; kept private until the reuse terms are recorded) | downloaded 26 Nov 2026 | `c8c068bef65c3813f8bbead3a461d7d777883d32477916c88a08664d71cc0c5f` |
| GLEIF ISIN-LEI mapping file `isin-lei-20261126T081510.zip` | 26 Nov 2026 | `8f66113ff535619d3d90d67edda0a58ff37af1ddce4d525901787feed0b865bb` |
| GLEIF LEI records and ultimate-parent relationships (API, golden copy of 26 Nov 2026 16:00 UTC) | 26 Nov 2026 | (queried live) |

## Counts

- Rows typed "Sustainability-Linked Bond": 250, which are 213 distinct ISINs.
- Of these, 136 ISINs were first listed on or before 31 December 2023.
- Issuer groups (GLEIF ultimate parent): 106, of which 75 have at least one bond listed by 31 December 2023.
- LEI source per bond: 74 from the GLEIF ISIN-LEI map, 11 from another ISIN of the same issuer label, 124 by name match (checked against GLEIF on 26 Nov 2026), 2 corrected ISIN by ISIN, 2 with no LEI found (Seaspan).

## Before registration

1. The editor checks each name match in `lei-name-matches-to-check.csv` (62 issuer labels) against the GLEIF record and corrects any wrong LEI in `name-match-picks.json`; then the frame is rebuilt.
2. The editor records the Euronext reuse terms.
3. Done 26 Nov 2026: the first capture on or after 31 December 2023 (18 Jan 2024) holds no readable list, so no bonds were added (protocol/archive-check.md).
4. The frame files, their hashes and the stratum rule are deposited on Zenodo with a DOI and a tagged commit.
5. Only then is the seed fixed (the next EuroMillions draw after the deposit) and `scripts/order.py SEED` run.

Inclusion is not checked here: under the Method, groups are screened one by one in the random order.

## Files

- `frame-bonds.csv`: one row per ISIN, with issuer, LEI, LEI source and issuer group.
- `frame-groups.csv`: one row per issuer group.
- `name-match-picks.json`: LEIs chosen by name match, to be checked.
- `order.csv`: written by `scripts/order.py` after registration.
