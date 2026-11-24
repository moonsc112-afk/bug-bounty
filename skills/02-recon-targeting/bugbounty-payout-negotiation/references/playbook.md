# Bug Bounty Payout & Negotiation Playbook

> Tujuan: bikin kamu siap jalanin (dan menang) negosiasi nominal bounty.
> Isi: cara severity dipetakan ke uang, benchmark angka 2026, aturan main per platform,
> taktik negosiasi, dan template. Semua angka ada sumbernya.

---

## 1. Dari severity ke uang: framework yang beredar

### CVSS (de facto, tapi jangan diandalkan sendirian)
- Common Vulnerability Scoring System = standar teknis severity (0-10), bukan kalkulasi risiko.
- Banyak program bayar per bucket: Critical 9.0-10.0, High 7.0-8.9, Medium 4.0-6.9, Low 0.1-3.9.
- Contoh pemetaan CVSS ke $ (Bug Bounty COI, ilustratif): Critical <=$10.000, High <=$7.500, Medium <=$1.500, Low <=$500.
- Shopify pakai tabel CVSS detail: Critical 9.0->$90k sampai 10.0->$200k; High 7.0->$17k sampai 8.9->$85k; Medium 4.0->$1.3k sampai 6.9->$10k.
- **Trap:** CVSS tinggi != bayaran tinggi. Program yang bagus menimbang *dampak bisnis*, bukan skor.

### BEMIX (BugEx) - impact-first, 4 dimensi
- E Economic Impact (kerugian $ langsung), D Data Exposure (kontrol yang didapat dari data bocor),
  O Operational Disruption (ketersediaan sistem), X Exploitability (modifier).
- Rumus: `Score = 5A + 2B + C + X - 4`, A/B/C = E,D,O diurut desc, X = exploitability. Range 1-30.
- Severity: Low 1-7, Medium 8-14, High 15-21, Critical 22-30.
- E=D=O=0 -> Informational (tidak dibayar). Dampak >$1M bisa negosiasi terpisah (mis. ~10% dari kerugian).
- **Pelajaran:** pisahkan "seberapa parah kalau dieksekusi" dari "seberapa gampang dieksekusi". Dua hal beda, dan keduanya bisa dinego.

### Immunefi Severity Classification (impact-based)
- Skala 5 level, terpisah untuk web/app vs smart contract/blockchain.
- Dua aturan penentu: **Primacy of Rules** (sekali-sekali kena terms di halaman program) vs
  **Primacy of Impact** (impact menang, aset keluar scope tetap dibayar kalau impact in-scope).
- Contoh aturan program: 0x & Sky & Beanstalk bayar critical SC = 10% dari dana yang terpengaruh,
  dengan minimum (0x $100k, Sky $150k, Beanstalk $100k) untuk cegah researcher menahan laporan.
- PoC wajib untuk Critical/High SC di banyak program.

### Platform lain
- **HackerOne / Bugcrowd / Intigriti / YesWeHack**: tabel per severity, kadang per aset; ada mediasi.
- **Cantina**: severity classification sendiri; status `Confirmed` baru eligible payout; bisa `Disputed` -> mediasi.
- **Sherlock**: bug bounty per program, ceiling ikut TVL; severity "watertight".

---

## 2. Benchmark angka 2026 (buat argumentasi "pasaran")

### Immunefi (sumber: riset Immunefi Apr 2026, 593 program, Jan 2021-Feb 2026)
| Metrik | Angka |
|---|---|
| Median payout critical | **$20.000** |
| Mean payout critical | **$114.355** (ditarik ekor panjang) |
| Total dibayar untuk critical | **$107,3 juta** |
| Share critical dari nilai payout | ~92,7% |
| Confirm critical per program (yang pernah) | rata-rata 2,7 |
| Program 5+ tahun yang pernah critical | 93,9% |
| Rata-rata payout/program/tahun | ~$63.300 (~$54.500 untuk critical) |
| Median hack onchain 2024-2025 | $2,2 juta (avg $24,5 juta) |

Tambahan (Scan the Chain, 2026-10-01, 225 program aktif, 190 baris critical):
- Median critical **$100.000**; p25 $50.000; p75 $500.000; p90 $1.000.000; ceiling terbesar $15M (LayerZero).
- Q1 2026 Immunefi: $7,87M dibayar, rata-rata $7.131/laporan; satu laporan $3M = 38% total kuartal.

> Artinya: **jangan pakai mean**. Kamu dibayar sesuai severity yang kamu kena, di program yang kamu pilih. Median $20k vs mean $114k = pasar power-law.

### Tabel platform (contoh publik)
| Program | Low | Medium | High | Critical |
|---|---|---|---|---|
| GitHub (public) | $250 | $2.000 | $5.000 | $10.000 |
| GitHub (VIP) | $1.000 | $7.500 | $20.000 | $30.000+ |
| HackerOne | $100-200 | $1.000-1.500 | $3.000-7.000 | $6.000-15.000 |
| Valve (Steam/CS2) | $100-200 | $200-750 | $750-2.500 | $2.500-7.500 |
| Shopify | - | $1.300-10.000 | $17.000-85.000 | $90.000-200.000 |
| OpenAI | - | ~$2.400 | ~$3.200 | $30.000 (exceptional $100k, +bonus sampai $172k) |
| 1inch (web) | $100-1.000 | $1.000-5.000 | $5.000-15.000 | $15.000-50.000 |
| 0x (SC) | - | $5.000 | $35.000-100.000 | $100.000-1.000.000 (10% dana) |
| Sky (SC) | $1.000 | $5.000 | sampai $100.000 | $150.000-10.000.000 (10% dana) |
| Beanstalk (SC) | - | $1.000-10.000 | $10.000-100.000 | $100.000-1.100.000 |
| Cosmos (DLT) | $500 | $1.000 | $4.000 | $50.000 (flat) |

### Web pada umumnya (TRIAGERS, per jenis perusahaan)
| Severity | Early stage | Established | High-stakes (fintech/infra/health) |
|---|---|---|---|
| Critical | $2.500-5.000 | $10.000-20.000 | $50.000+ |
| High | $1.000-2.500 | $4.000-8.000 | $15.000-25.000 |
| Medium | $250-500 | $1.000-2.500 | $3.000-6.000 |
| Low | $50-150 | $200-500 | $500-1.500 |

> Insight penting: rasio antar tingkat matters. Critical 20-50x Low itu sehat; Critical cuma 3x Medium = orang akan farm medium pakai scanner.

---

## 3. Aturan main yang mengikat (baca sebelum nego)

- **"Bug bounty program is law" (Immunefi):** halaman program = kontrak. Severity + tabel = patokan.
  Proyek dilarang menekan di bawah yang tertulis; researcher juga terikat (gak boleh hitung impact
  seenaknya). Kalau proyek melanggar, pakai tombol "Request Help" -> mediator Immunefi.
- **Primacy of Rules vs Primacy of Impact:** tentukan mana yang dipakai program. Primacy of Impact
  biasanya lebih menguntungkan researcher (asset di luar scope tetap bayar kalau impact in-scope).
- **Downgrade conditions:** banyak program DC yang bisa menurunkan 1 level (mis. Cosmos: race condition
  di luar kendali attacker, butuh permissioned set, butuh aksi governance, kolusi validator >=1/3,
  mudah dipulihkan, butuh relayer jahat). Cek daftar ini - argumen "butuh kondisi X" sering dipakai
  untuk nurunin severity.
- **PoC gate:** Critical/High SC di Immunefi wajib PoC (tanpa PoC = no reward). Siapkan PoC yang
  reproducible, bukan teori.
- **Static vs range:** GitHub pindah ke static (Low $250 ... Crit $10k) + bonus diskresioner. Range =
  ruang negosiasi; static = patokan keras, bonus = satu-satunya kelonggaran.
- **Bonus:** OpenAI punya multiplier (Quality 1.15, Loyalty 1.10-1.15, Priority Campaign 1.30) yang
  bisa menaikkan $30k jadi $51,6k. Cek apakah program punya bonus kualitas/loyalty/kampanye.
- **Mediasi:** HackerOne, Immunefi, Cantina semua punya jalur mediasi kalau disput severity/nominal.
  Jangan ragu pakai - ini resmi, bukan "berisik".

---

## 4. Kenapa satu High $1.000 dan lain $5.000

Yang menentukan nominal di dalam band:
1. **Dampak bisnis, bukan skor.** "Bug ini jadi insiden apa?" - fraud loss, notifikasi regulasi,
   disclosure ke klien besar, downtime. Sebagian kecil dari biaya insiden itu = bounty wajar.
2. **Biaya alternatif.** Kalau bug segitu butuh pentest $1.500-2.500/hari-tester dan mungkin seminggu
   untuk ketemu, membayar $1.000 untuk RCE pre-auth berarti di bawah "rate intern" perusahaan.
3. **Nilai data.** PII/finansial punya exposure statuter per record. IDOR yang enum 400.000 record
   vs bounty $500 = rounding error.
4. **Kualitas laporan.** Repro jelas, PoC jalan, argumen severity terukur -> triager lebih gampang
   naikkan ke atas band.
5. **Precedent & komparabel.** Program biasanya konsisten per kelas bug/aset. Cita-cita: "kelas
   bug ini di program ini dibayar X". Tapi hati-hati: kutip **midpoint** program lain, bukan
   ceiling teoritisnya.

---

## 5. Taktik negosiasi (yang work, yang jangan)

**Work:**
- **Lead with impact, bukan CVSS.** "One-click account takeover, 85% server reachable" > "CVSS 9.8".
- **Kuantifikasi dampak**: dana berapa, aset apa, berapa user, kondisi apa. Angka > adjektif.
- **Cite precedent & standar industri**, dan tunjukkan kalau penawaran di bawah midpoint band.
- **Tawarkan nilai tambah**: remediation guidance/patch, mitigasi sementara, validasi pasca-fix.
- **Minta "top of the band" secara spesifik**, bukan "lebih". Mis. "top of High band ($7.500), CVSS 8.1".
- **Pakai jalur resmi**: komentar laporan -> program manager -> mediasi platform. professionalism = koin.
- **Minta keputusan tertulis** untuk deal di luar tabel (bonus/exclusivity): scope, milestone, IP, disclosure, safe harbor.

**Jangan:**
- Jangan ancam disclosure publik / jual bug. Itu merusak reputasi dan bisa berakhir hukum.
- Jangan terima NDA yang melarang write-up publik **sementara** bounty di bawah dampak - tawar dulu, atau tolak.
- Jangan terima assignment IP penuh tanpa kompensasi wajar.
- Jangan terima "budget terbatas" sebagai alasan - alternatif researcher bukan budget kamu, tapi program lain.
- Jangan nego per-laporan dengan harapan tabel naik; sinyal pasar dibaca dari banyak researcher, bukan satu.

**Kapan walk away:** tawaran di bawah minimum waktu/risiko; IP assignment tanpa bayaran; tidak ada safe harbor;
disclosure timeline yang memaksa exposure prematur.

---

## 6. Template pesan (bisa disesuaikan)

> Hi [Program/Triager],
>
> Thanks for triaging. I want to respectfully discuss the severity/award.
>
> **Impact:** [satu kalimat - apa yang bisa dilakukan attacker, skala berapa]
> **Evidence:** [tx hash / PoC / screenshot]
> **Program terms:** [ severity X per halaman program, impact Y in-scope ]
> **Comparables:** [kelas bug serupa di program ini / platform dibayar $Z; median critical Immunefi $20k, program ini midpoint $W]
> **Request:** top of the [severity] band ($X), plus [bonus kualitas/kampanye] kalau berlaku.
>
> Kalau ada kondisi yang bikin kalian nurunin severity (mis. [sebut]), tolong tunjukkan yang mana -
> saya siap tambah PoC/bukti. Saya juga bisa bantu remediation.
>
> Thanks,
> [handle]

---

## 7. Checklist sebelum terima tawaran

- [ ] Severity yang diberikan = severity yang layak menurut halaman program? (bukan perasaan)
- [ ] Nominal di dalam band? Kalau di bawah midpoint, sudah ada argumen impact/komparabel?
- [ ] Ada bonus kualitas/loyalty/kampanye yang terlewat?
- [ ] KYC & payout method sudah siap (Cantina: KYC + team payment preference; Immunefi: KYC per program)?
- [ ] Syarat NDA / IP assignment / disclosure timeline - masih wajar?
- [ ] PoC requirement terpenuhi?
- [ ] Ada duplicate? (kalau duplikat, kredit/timestamp bisa diangkat)
- [ ] Jalur mediasi dicatat (HackerOne mediation, Immunefi Request Help, Cantina Disputed)?
- [ ] Kalau ditolak/lowball: apakah worth eskalasi atau lebih baik park + dokumentasi?

---

## 8. Sumber

- BugEx BEMIX: https://bugex.ai/bemix
- Bug Bounty COI - Payment: https://bugbountycoi.org/framework/chapter-5/
- Bug Bounty COI - Disputes: https://bugbountycoi.org/framework/chapter-6/
- Immunefi research (criticals, 593 programs, Jan 2021-Feb 2026): https://immunefi.com/blog/research/nearly-every-long-running-bug-bounty-program-on-immunefi-has-found-a-critical-bug
- "The bug bounty program is law" (Immunefi): https://medium.com/immunefi/the-bug-bounty-program-is-law-8d57fc113743
- Scan the Chain - payout distribution: https://scanthechain.com/bug-bounty-payout-distribution.html
- TRIAGERS - reward amounts: https://triagers.com/blog/bug-bounty-reward-decisions
- TRIAGERS - private vs public: https://triagers.com/blog/private-vs-public-bug-bounty-programs
- GitHub bounty restructure: https://github.blog/security/next-chapter-restructuring-githubs-bug-bounty-program
- OpenAI bigger bounties: https://openai.com/index/rewarding-defenders-with-bigger-bug-bounties
- Shopify rewards (CVSS table): https://shopify.com/bugbounty/rewards
- HackerOne hacker mediation: https://docs.hackerone.com/en/articles/8466617-hacker-mediation
- Cantina payout & disputes: https://docs.cantina.security/researchers/participation/bug-bounty-payouts
- HackerOne severity/CVSS: https://docs.hackerone.com/en/articles/8475343-severity
- Web3 guide (payout references): https://blockchainwhitehackers.com/the-web3-bug-bounty-guide-no-one-wants-you-to-read/
