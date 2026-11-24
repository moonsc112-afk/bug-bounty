# Parity comparison for two implementations

Use when a fork and a clean-room rewrite, or any two pipelines, claim the same output.

## Procedure

1. Write one canonical input file into scratch and keep it as a verifiable handle in the report.
2. Run each implementation through a small Node/Python driver that calls the real pipeline API and writes artifacts into separate folders. Never hand-copy sample output into the comparison.
3. Compute objective metrics: file count, generated tags, labels, residual input directives, validation issues, and bytes. Add a unified diff so the difference is concrete.
4. Report a metric table, one short output excerpt per side, then a verdict naming which output is runtime-ready.
5. If one side leaves input directives untouched, say it is structurally valid but not contract-compatible. That is not parity.

## Scenario ladder

Cover more than the happy path before declaring parity:

- one short input that exercises the core directive set;
- a multi-scene input with control flow, macro blocks, and declarations that emit no tag;
- a duplicate-label or other validation error case, comparing the detected problem and not the message wording;
- a stateful case that carries entities across outputs, including a case that exceeds the available slots and forces eviction.

A reimplementation often matches every single-output test and still diverges when state persists across outputs.

## Bulk pair check

After the scenario drivers exist, normalize only the lines known to be implementation identity, such as a generator comment, then compare every artifact pair in one pass. Report the number of pairs checked and the number of mismatches after normalization. A single `diff -u` is evidence for one file; a mismatch count over all pairs is evidence for the claim.

## Pitfalls

- Do not compare prose descriptions of two designs; compare bytes produced from the same input.
- Do not treat a shared file extension as equivalence. A `.ks` file containing raw `@bg` or `@choice` lines is not runnable TyranoScript.
- Use scratch for ad hoc drivers and keep the script beside its artifacts so it can be rerun immediately; promote any comparison that becomes a reported parity claim into the repo.
- When the only remaining diff is a generator-identification comment, declare parity explicitly with the byte delta instead of chasing byte-identical output across independently written implementations.
- Model hidden state carried across outputs in the reference implementation, such as active entities, slot ownership, or recency ticks, because a stateful renderer usually diverges in that state rather than in the directive being tested.
- Keep a durable parity harness in the repo under `tests/parity/` with an env var pointing at the reference implementation, because a scratch-only driver disappears when the compared repos move and the parity claim stops being reproducible.
- Gitignore the harness output directory and assert the runner's summary counts from a `node:test` case, because generated artifacts must not enter the commit and a runner that silently skips cases can still exit zero.
