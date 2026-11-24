---
name: bugbounty-payout-negotiation
description: "Use when negotiating a bounty payout or dispute."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, Payout, Negotiation, Severity, Dispute]
---

# Bug Bounty Payout & Negotiation

Use when a report's severity/award is being decided, when a program lowballs, or when a
report is disputed. The goal is to argue the number with evidence, not feeling.

## When to Use

Load this when a report's severity or award is being decided, when a program offers less
than the published band/midpoint, when a report is disputed or rejected, or when you are
deciding whether to accept an out-of-table deal (bonus, NDA, exclusivity, IP terms).

## Core principle

Lead with **impact**, not CVSS. The program is buying the option to skip an incident:
quantify the damage, cite the program's own terms and precedents, then ask for a specific
number (top of the band), not "more".

## Numbers that anchor a negotiation (2026)

- Immunefi: median critical **$20,000**; mean **$114,355**; critical = ~92.7% of payout value.
- Scan the Chain (225 active programs, 190 critical rows): median **$100,000**, p25 $50k,
  p75 $500k, p90 $1M; largest ceiling $15M (LayerZero).
- Median onchain hack 2024-2025: **$2.2M** (avg $24.5M). Bounty is the cheap path.
- Web tables: GitHub public Low $250 / Med $2k / High $5k / Crit $10k; HackerOne
  Crit $6k-15k; Shopify Crit $90k-200k (CVSS-mapped).
- Web3 SC: 0x crit $100k-1M (10% of funds affected), Sky crit $150k-10M, Beanstalk $100k-1.1M.

## Rules that bind the outcome

- **Program is law** (Immunefi): the program page fixes severity + award; projects cannot
  retroactively underpay; researchers are bound too. Use "Request Help" for mediation.
- **Primacy of Rules vs Primacy of Impact** decides whether out-of-scope assets still pay.
- **Downgrade conditions** (race, permissioned set, governance action, collusion, easy recovery)
  are how programs lower severity - check the list and pre-empt it.
- **PoC is the gate** for Critical/High SC: no reproducible PoC = no reward.
- **Range vs static**: a range is room to negotiate; static means only discretionary bonus moves it.

## Negotiation moves

1. Quantify impact ($ at risk, users, conditions) before mentioning severity.
2. Cite the program's published band + precedent for the same bug class/asset.
3. Ask for top of the band specifically; offer remediation/validation as added value.
4. Escalate through official channels: report thread -> program manager -> platform mediation
   (HackerOne, Immunefi, Cantina).
5. Walk away on: below-minimum offer, full IP assignment without pay, no safe harbor,
   premature-disclosure demands.
6. Never threaten public disclosure or sale - it burns reputation and can create legal exposure.

## Full reference

The full checklist, tables, per-program benchmarks, the BEMIX/CVSS/Immunefi mapping,
dispute handling, and a ready-to-use message template are in
[references/playbook.md](references/playbook.md).

Web3/smart-contract writeup precedents with disclosed bounty amounts (curated from
bugbountyhunting.com) are in [references/web3-writeups.md](references/web3-writeups.md);
the 27 paid writeups read in depth (bug class, root cause, impact, lesson) are in
[references/web3-writeups-deep.md](references/web3-writeups-deep.md).
