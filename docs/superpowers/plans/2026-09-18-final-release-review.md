# Final release review plan

**Goal:** Determine whether Garhwali Language Lab is fit to release, fix verified defects without reducing features, and leave a reproducible evidence trail in `finalreport.md`.

1. Inventory code, data, reports, release artifacts, and CI entry points. Verify the inventory against Git rather than relying on README claims.
2. Audit language identity, OCR, transcript quality, deduplication, provenance, rights, split isolation, and evaluation methodology with independent scripts and focused tests.
3. Remove verified dead or machine-specific repository state. Keep changes limited to demonstrated portability, correctness, privacy, and maintainability defects.
4. Add regression checks for every fixed defect: language labels, prompt leakage, lexicon gloss recovery, and multi-reference evaluation.
5. Rebuild affected generated data and both Hugging Face package profiles. Refresh manifests, audits, and documentation from the rebuilt outputs.
6. Run focused tests, the complete test suite, release validators, static syntax checks, and a clean-checkout CI simulation.
7. Write `finalreport.md` with evidence, limitations, severity-ranked findings, an explicit release verdict, and the remaining native-speaker or rights-holder work.

Success requires all automated checks to pass, no known split leakage, no unsupported Garhwali labels in the text export, no tracked machine-specific dependency link, and no claim that machine-only review establishes native accuracy.
