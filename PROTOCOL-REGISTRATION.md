# Protocol registration (draft, to be deposited on Zenodo after the pilot and before any wave 1 reading)

This file is filled in on the day of registration. Until then it is a draft. After registration, a change to the Method needs a public proposal and 14 days for comment (Appendix C).

## What is registered
1. The Method, METHOD.md, version [version], with its sha256.
2. The frozen extraction prompt, protocol/extraction-prompt.md, version [version], with its sha256, and the fixed message inside it.
3. The model identifier as shown: claude-opus-5-5 (Claude, by Anthropic), for both readings; route: agent tasks inside one Claude project in one account, each reading in a fresh context, no web search and no connectors; account settings recorded with dated screenshots at the start of the extraction period.
4. The check panel models: value check and adversarial check claude-sonnet-5-5; blind re-reading claude-fable-5-2; blind status check claude-haiku-5-5. No panel check is run by the reading model.
5. The data dictionary (dictionary/schema.json) and every script, by sha256 (protocol/frozen-hashes.txt, written by scripts/freeze.py).
6. The seed, the order file's sha256 (frame/REGISTRATION.md) and the pilot groups.
7. The statistics plan: Method E.7 (blind coding, validation of the AI reading with the marks 90 per cent, 90 per cent and zero, effect of the editor's check) and E.9 (inference, reporting); exact Clopper-Pearson intervals; Krippendorff's nominal alpha and Gwet's AC1 for status; issuer-clustered bootstrap with 10,000 resamples once the random sample has ten groups, plain counts before that; 270-day fallback deadline with a 365-day sensitivity count (scripts/stats.py).
8. The planted-error test: before the pilot and after every ten instruments, six planted errors; the share caught by scripts and value check is reported; below five of six, the panel prompts are revised on the development set only.
9. The deviations logged up to registration (protocol/deviations.md) and the development runs (protocol/dev-runs.md).
10. Timeline: notices on [date], reply period of 15 working days, release on [date].

## Hashes
[paste the output of scripts/freeze.py]
