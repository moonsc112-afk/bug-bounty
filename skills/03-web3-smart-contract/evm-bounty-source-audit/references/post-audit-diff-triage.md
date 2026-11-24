# Post-audit diff triage for audit competitions

Use when the target has a prior audit report and the competition pins a newer commit.

- If the PDF has no usable text layer, extract it with `pdftotext -layout <report>.pdf <out>.txt` and grep the result for finding IDs, severity headers and keywords. A tiny `read_file` result on a PDF means extraction method failed, not that the report is empty.
- Record the commit the audit actually reviewed from the report introduction, then compare it with the pinned commit using the GitHub compare API: `curl -sL https://api.github.com/repos/<org>/<repo>/compare/<audited>...<pinned>`. Parse `files`, `commits`, `additions` and `deletions` to size the post-audit surface.
- Map every `[Unreleased]` changelog item to an audit finding by keyword before calling it fresh surface. Post-audit changelogs are usually fix logs; mislabeling them as unaudited code wastes a hunt on already-known issues.
- Print the patch for each changed source file, not just the file list. Identify new branches, new require statements and new helper calls, and check whether the same commit changed the tests that cover them.
- Treat post-audit implementation churn as the highest-value fuzz target: run the full suite first, then write mutation harnesses against the exact changed functions.
- When all changelog items map to findings, say so explicitly in the verdict. A precise negative result is stronger than a vague "no issue found".
