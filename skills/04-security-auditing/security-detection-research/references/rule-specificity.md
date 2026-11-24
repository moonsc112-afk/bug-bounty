# Rule specificity decision table

Use this when asked whether a set of detection rules is ready to deploy or how much noise it will make. Classify each rule into one bucket, then report the bucket with the evidence that placed it there.

| Evidence in the rule | Bucket | What to report |
|---|---|---|
| Exact campaign strings, container names, image names, implant paths, hashes | Campaign-specific, low false-positive risk | Cite the SID or rule id and the literal string. Safe to deploy after a baseline. |
| Requires the legitimate tool's process plus a changed config flag | Misuse detection, medium risk | State that it detects a configuration change, not the tool. Note which flag and which process parent is required. |
| Matches a config flag or script name alone, with no parent-process or path constraint | Misuse detection with an unscoped branch | Name the exact branch that fires without context. Compare against the `falsepositives` text and say if it does not actually filter. |
| Matches normal product features: server header, dashboard title, chat gateway, user-edited persona file | Asset discovery, not attack detection | Say plainly that a legitimate install triggers it. Point to the rule's own confidence metadata if it is already Medium or Low. |
| Pure IOC or watchlist match against addresses and domains | Indicator sweep | Flag infrastructure reassignment risk and require the `review_by` or confidence column to be checked before blocking. |
| Generic behavior rule shared by every framework | Broad by design | Mark it as needing a separate baseline; do not judge it by the framework-specific rules' false-positive rate. |

## Checks before classifying

- Read the `condition` or `where` clause, not just the description and `falsepositives` list.
- Note severity, trigger threshold, and time window; threshold zero with a short window turns a benign config edit into an alert.
- For YARA, read the `meta` block: an explicit note that a source-tree match is expected by design should be reported as such, not as a defect.
- For files written into a tool's home folder, check whether the write is a normal feature. A persona file or a prefill file can be both a normal config and an attacker artifact; the surrounding context decides.
- Cross-check the authors' stated testing scope. Syntax and conversion tests are not the same as validation against a captured intrusion.
