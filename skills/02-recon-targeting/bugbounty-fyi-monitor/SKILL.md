---
name: bugbounty-fyi-monitor
description: "Use when monitoring/scraping bugbounty.fyi bounties."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bugbounty, monitoring, rss, scraping, cron]
---

# bugbounty.fyi monitor + scraping

## When to Use
- User menyebut monitor bug bounty / perubahan scope/reward dari bugbounty.fyi.
- Perlu scraping atau filter daftar program/queue dari bugbounty.fyi lagi.
- Perlu menyesuaikan cron "bugbounty.fyi watch" (tambah/hapus program, pause).

## Setup aktif di mesin ini (user's Windows box)
- Script monitor: `~/AppData/Local/hermes/scripts/bugbounty_monitor.py` (versi lama: `bugbounty_monitor_v1.bak`)
  - Watchlist: `watchlist.json` di folder `scripts/` — 1.020 program berbayar: 8 platform web3 (Immunefi, Cantina, Sherlock, HackenProof, Remedy, BugRap, CertiK, AuditOne), Sorona (475 OSS), 11 self-hosted terkurasi (Frax, Tether, Cygnus, Beanstalk, Nomad, Eclipse, Dapper, Across, Squads, Glow, Bullpen). Entry: slug -> {name, platform, reward, priority?}; 48 program incaran ditandai `priority: true`.
  - State: `bugbounty_monitor_state.json` (guids yang sudah dilihat + `last_scan_day`; jangan diedit manual).
- Dua fungsi: (1) tiap run — diff RSS /changes.rss vs watchlist, dengan blok 💰 terpisah untuk reward naik pada 48 incaran prioritas dan 🔴 terpisah untuk program closed/paused (⭐ = incaran utama); (2) sekali sehari — scan program baru via halaman `launched=30` per platform (termasuk Sorona dengan `&oss=1`), tambah otomatis ke watchlist. Alert program baru hanya jika **scope kontrak terverifikasi** DAN reward >= $50.000; fungsi `program_page_scope(slug)` mem-parsing seksi scope halaman program.
- Semua fetch (RSS + SSR) pakai 3x retry dengan backoff 2s/4s dan timeout 35s+ — situs sering timeout/502; jangan hapus retry ini. Backup versi lama: `bugbounty_monitor_v1.bak`, `bugbounty_monitor_v2.bak`.
- Cron: job "bugbounty.fyi watch (semua platform web3)" — every 30m, `no_agent=true`, deliver origin. Kelola via `cronjob_manage` (list first, then pause/resume/remove/update).
- Perilaku script: stdout kosong kalau tidak ada yang baru (watchdog pattern — tidak ada spam); run pertama = baseline; `--demo`/`--list`/`--scan` untuk uji manual.
- Verifikasi jalur alert setelah mengubah script/feed: import `bugbounty_monitor` sebagai modul di python, set `m.STATE_PATH` ke file temp (JANGAN sentuh state asli), jalankan `m.main()` (baseline), hapus 1 guid dari state temp, jalankan lagi → harus keluar digest "1 kejadian baru", lalu run ketiga harus silent. Catatan: python native dan bash melihat `/tmp` berbeda (C:\tmp vs MSYS tmp) — selalu pakai path Windows eksplisit untuk file temp lintas-tool.

## Kenapa 30 menit (penting)
`https://bugbounty.fyi/changes.rss` hanya memuat window ~100 kejadian terakhir. Pada jam sibuk itu < 1 jam (ukur: 100 item = 58 menit). Interval polling > 1 jam akan kehilangan event. Jangan naikkan ke harian.
Kategori RSS yang pernah terlihat: `scope_added`, `scope_removed`, `program_launched` (judul "X: New public program."), `program_reactivated`, `program_paused`, `reward_cut`, `reward_tier_added`. Blok 🆕 di digest berasal dari scan harian `launched=30`, bukan dari RSS, meski event launch biasanya juga muncul di window RSS yang sama. Cara merekonsiliasi angka aggregator dengan feed ada di bawah.

## Verifikasi digest aggregator "last 24 hours"

Saat user menempel post aggregator yang merangkum perubahan 24 jam (program baru, back open, reward tier, scope drop), jangan percaya hitungannya. Rekonsiliasi dengan feed primer:

1. Ambil `created_at` dari mirror fxtwitter untuk post aggregator. Itu UTC dan merupakan ujung jendela 24 jam. Timestamp yang tampil di attached context atau di UI X bisa waktu pembaca (viewer-local), jadi jangan dipakai untuk menghitung jendela.
2. Fetch `https://bugbounty.fyi/changes.rss`, parse dengan `xml.etree.ElementTree`, kumpulkan `title`, `link`, `pubDate`, `category` per item. Filter event yang `pubDate`-nya berada di dalam jendela. Event dengan `pubDate` setelah `created_at` post tidak boleh diklaim sebagai isi post itu, walau feed diambil belakangan.
3. Kelompokkan menurut `category`. Jangan samakan angka aggregator dengan jumlah event feed: VDP baru sering tidak dihitung sebagai "program baru berbayar", dan jumlah `program_reactivated` di feed bisa jauh lebih banyak dari angka "back open" di post. Sebut ketidaksesuaiannya, jangan memilih salah satu secara diam-diam.
4. Untuk klaim "added reward tiers", cek apakah program yang sama punya event `reward_cut` dalam jendela yang sama. Tier baru dan penghapusan max reward bisa masuk dalam waktu satu jam; angka lama di post lalu menyesatkan. Cek halaman `programs/<slug>` live sebelum mengutip angka reward.
5. Untuk klaim "scope drop", cari event `scope_removed` dengan aset terbanyak di jendela. Beberapa listing bisa mencatat penghapusan repo yang sama pada jam berbeda, dan event setelah jam post bukan bagian dari ringkasan.
6. Baca baris "At a glance" di halaman program untuk platform tujuannya. Frasa `Report on Cantina` menandakan audit contest dengan pool hadiah, bukan bounty per bug. Sampaikan sebagai pool, jangan sebagai "up to $X per temuan".
7. Freshness listing bukan liveness. `Last change`, event `scope_added`, dan daftar target baru di bugbounty.fyi bisa muncul pada engagement yang sedang di-pause platformnya. Buka halaman platform tujuannya dulu: banner status dan tanggal pause di Bugcrowd, feed Activity berisi suspend/unsuspend di Intigriti. Program yang paused tetap di-skip walaupun aggregator menampilkan scope baru.

Keluaran: tabel per klaim aggregator berisi angka post, angka feed, dan sumber yang dipakai, lalu rekomendasi program yang benar-benar relevan dengan stack user.

## Scraping situs
- Filter URL: `?kind=bounty`, `sort=reward|launched|recent|scope|response`, `harbor=1`, `nokyc=1`, `oss=1`, `asset=...`, `on[0]=<platform>`, `q=<teks>`, `fresh=30`, `launched=30`.
- **Pagination client-side**: tombol `Next »` (50 baris/halaman). Klik via JS, tunggu baris pertama berubah sebelum baca; jangan andalkan `?page=N` (return kosong).
- **Tanpa API JSON** (performance entries cuma Cloudflare/GA), Livewire app — tapi halaman pertama ter-render server-side → urllib biasa bisa scrape. Baris di `<tr wire:key=...>`; regex per chunk: slug dari `href="https://bugbounty.fyi/programs/<slug>"`, platform dari `lg:table-cell`, scope dari `sm:table-cell text-fg-2`, reward dari `num font-semibold`, floor dari `num block text-xs text-muted`. Buang komentar `<!--[...]-->` dulu.
- **Deteksi program baru tanpa browser**: filter `launched=30&sort=launched`, halaman 1 = 50 terbaru; per platform web3 biasanya < 10 program/30 hari → 1 halaman cukup.
- Struktur baris tabel: cells = `[icon, nama, domain, flags...]`, lalu `[platform, scope, response, "reward | from $floor"]`.
- Halaman program: **server-rendered juga** → `urllib` cukup untuk `https://bugbounty.fyi/programs/<slug>` (hanya halaman daftar yang butuh browser); ambil teksnya lalu regex `Top reward`, `Top severity paid`, `Assets in scope`, `Last change`, `At a glance`, dan seksi `Scope`.
  Field `Top severity paid` adalah label severitas tertinggi dengan reward terdaftar, bukan bukti ada payout. Klaim payout dari berita, misalnya fase privat, tetap klaim terpisah dan jangan disamakan dengan riwayat pembayaran platform.
- **Slug program bisa menyimpan dua program berbeda untuk satu proyek.** `beanstalk-sherlock` di bugbounty.fyi adalah program Sherlock baru dengan top $50.000 dan 22 aset, sedangkan program Immunefi Beanstalk punya maximum $1,1 juta. Jangan pernah menggabungkan angkanya. Cek field `Report on` di halaman program untuk tahu platform mana yang jadi sumber reward, lalu verifikasi ke halaman platform itu.
- **Tab scope Sherlock tidak ikut ter-render di teks biasa.** `web_extract` pada `?tab=scope` hanya mengembalikan judul "Contracts in scope" tanpa baris. Fetch HTML mentah dengan `urllib` dan regex pola Next.js `\\"network\\":\\"([A-Z]+)\\",\\"address\\":\\"(0x...)\\",\\"displayName\\":\\"(...)\\"` untuk mendapatkan pasangan chain, alamat, dan nama kontrak. Verifikasi bytecode dengan `eth_getCode` di RPC chain yang bersangkutan: alamat yang sama bisa kosong di Ethereum tetapi hidup di Arbitrum.
- **Ambil daftar alamat in-scope langsung dari HTML mentah** kalau tabel scope di-render client-side dan teksnya cuma `...`: regex `0x[a-fA-F0-9]{40}` dari halaman `programs/<slug>` yang di-fetch dengan `m.fetch`, lalu dedupe huruf besar/kecil. Tiap alamat biasanya berdekatan dengan tautan explorer, jadi ini cukup untuk dapat 15/15 alamat tanpa browser. Cross-check dengan Sourcify (chainId benar) sebelum memakai salah satunya untuk klaim.
- **Filter scope kontrak via HTTP (tanpa browser)**: cari frase `assets you may test`, buang `<script>`/tag, baca pasangan label + angka (`Smart contracts`, `Source code`, `Web`, dll). Lolos kalau ada `Smart contracts`, atau `Source code` + keyword `contract|solidity|anchor|evm|solana|rust`. Jangan grep seluruh halaman: kata `Programs` muncul di navigasi semua halaman (false positive). Uji real: Kamino/Metric/Exactly/1inch lolos; Booking/Glow/Bullpen/Chainlink-node tidak.
- **Survei terstruktur tanpa parse ulang**: import script monitor sebagai modul
  (`importlib.util.spec_from_file_location` dari path script-nya) lalu panggil
  `m.parse_ssr_rows(m.fetch(m.SCAN_URL.format(plat[0], ""), timeout=60))` untuk tiap entry `m.PLATFORMS`.
  `m.PLATFORMS` berisi tuple `(slug, label, suffix)` dan `m.SCAN_URL` punya dua placeholder,
  jadi `.format(slug)` saja menghasilkan URL yang salah.
  Hasilnya baris dict `{slug, name, platform, scope, reward, floor}` siap diurutkan/di-filter
  dengan Python — jauh lebih cepat dan tahan perubahan markup daripada menulis regex SSR sendiri.
  Ini cara menjalankan survei "apa yang launch 30 hari terakhir di semua platform" sekali jalan.
- Badge `New` / filter `launched=30` = umur **LISTING**, bukan umur kode — verifikasi umur kode dulu (lihat skill `new-feature-bug-hunt`) sebelum menghabiskan waktu pada target yang sudah diaudit.
- Situs sering 502 (bad gateway) dan navigate timeout flaky: retry 1-2x setelah 3-5 detik; treat "Bad gateway" sebagai kegagalan.
- KYC terdeteksi dari frasa "KYC to get paid" / "Proof of identity needed" (kalau tidak muncul = tidak disebut, bukan berarti bebas KYC).

## Konteks user
- Fokus: EVM + Solana smart contract, hanya impact loss-of-funds yang dibayar, workflow PoC + KYC ditangani sendiri.
- Deliverable tersimpan juga di Desktop user: `bugbounty-legit-list.md`, `bugbounty-shortlist-evm-solana.md/.csv`, `bugbounty-queue-....csv`, `bugbounty-target-kamino-recon.md`.
- Saat menilai legitimasi program: bedakan **deposit refundable** (Sherlock: USDC 250, kembali jika valid) dari **fee tetap** (Metric/Immunefi: USDC 50 per report, tidak kembali). Fee = red flag; deposit refundable = anti-spam biasa.
