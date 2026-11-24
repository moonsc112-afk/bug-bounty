# Checklist: Bug di Fitur Baru (Bug Bounty)

> Prinsip: fitur baru punya review paling sedikit, dibuat buru-buru, dan paling
> sering **tidak konsisten** dengan pola aplikasi lama.
> Pertanyaan pemandu: *"Apakah fitur baru ini ikut aturan lama?"*

## 0. Mindset

- [ ] Fitur rilis < 30 hari = prioritas tertinggi (window sempit).
- [ ] Jangan mulai dari app utama yang sudah lama — peluangnya sudah tipis.
- [ ] Target akhir harus punya impact **"loss of funds"** (kategori yang dibayar).
- [ ] Idealnya lapor dalam 1-7 hari setelah rilis.

## 1. Discovery — cari fitur baru dulu

**Web / app**
- [ ] Changelog & release notes program
- [ ] Blog / perumuan produk / Twitter resmi perusahaan
- [ ] Halaman **scope** — aset/subdomain/endpoint baru
- [ ] Diff **JS bundle**: bundle lama vs baru, cari route/endpoint/API call baru
- [ ] Sourcemap / file sumber kalau ada
- [ ] Bandingkan HTTP traffic app sebelum vs sesudah rilis

**Smart contract (EVM / Solana)**
- [ ] Program ID / alamat deployment baru (validator, explorer, subgraph)
- [ ] Upgrade proxy / impl address berubah (EIP-1967 slot, Solana program upgrade)
- [ ] Proposal governance yang baru passed dan sudah dieksekusi
- [ ] Versi baru protokol (v2, v3) — fungsi yang ikut berubah
- [ ] Changelog / docs / audit report terbaru: apa yang masuk dan **tidak** masuk scope audit
- [ ] Event/log baru: topic baru, instruction discriminator baru, `program log`

**Vetting kontes / program (lakukan SEBELUM riset kode)**
- [ ] Halaman kontes itu produksi, bukan demo/preview — waspadai subdomain preview + tanggal mulai/selesai yang bertentangan
- [ ] Reward berupa uang likid dengan nominal jelas; poin/airdrop dengan konversi kabur bukan target yang dibayar
- [ ] Ada judge bernama + funding guarantee yang nyata
- [ ] Kontes "post-audit" / Critical-only dengan ambang >20% dana = bukan kode segar tak teraudit
- [ ] Umur kode diverifikasi dari commit/deployment, bukan dari badge "launched <30d"

## 2. Recon target baru

- [ ] Petakan semua **entry point publik** fitur baru
- [ ] Siapa boleh panggil? (access control vs pola lama)
- [ ] State apa yang berubah?
- [ ] Event/log apa yang keluar? (lengkap atau hilang)
- [ ] Parameter baru: tipe, batas, tanda, decimals
- [ ] Integrasi: token, oracle, bridge, admin/privilege, fee, pause switch
- [ ] Fitur baru reuse pola lama atau nulis ulang dari nol?

## 3. Cek konsistensi (inti)

Untuk **setiap** aksi yang menggerakkan uang atau state:

- [ ] **Ownership** — resource milik pemanggil? (IDOR)
- [ ] **Permission / role** — cek di level yang sama dengan fungsi lama?
- [ ] **Default deny** — kalau lupa cek, default-nya tolak atau izin?
- [ ] **Accounting** — total masuk = total keluar?
- [ ] **Rounding / precision** — floor/ceil, decimals, `mulDiv`, penempatan pembulatan
- [ ] **Idempotensi / replay** — bisa dipanggil 2x? ada nonce/replay guard?
- [ ] **Reentrancy / callback** — guard sama dengan pola lama?
- [ ] **Slippage / minimum amount** — ada? (sandwich)
- [ ] **Rate limit** — ada? (drain bertahap)
- [ ] **Pause / emergency** — fitur baru bisa distop owner?
- [ ] **Admin / privilege** — apakah fitur baru menambah privilege baru?
- [ ] **Upgrade / storage** — kalau proxy, layout aman?
- [ ] **Error handling** — reject atau `swallow`?
- [ ] **Event** — lengkap? konsumen eksternal bisa tertipu?

## 4. Pola bug yang dicari (fokus loss of funds)

- [ ] IDOR / broken access control
- [ ] Double claim / reward dihitung dua kali
- [ ] Withdraw melebihi saldo / mint tanpa backing
- [ ] Salah hitung bunga/fee/rounding
- [ ] Reentrancy
- [ ] Signature replay / nonce hilang
- [ ] Oracle manipulation / harga basi
- [ ] Missing slippage -> sandwich
- [ ] Privilege escalation / admin key
- [ ] Cross-chain message forgery
- [ ] Dana stuck / locked (denial of funds)
- [ ] Overflow / underflow / cast salah
- [ ] Frontrun / MEV pada fitur baru

## 5. PoC & verifikasi

- [ ] Reproduksi di testnet / fork lokal (Foundry / Anchor + solana-test-validator)
- [ ] Tunjukkan: state awal -> aksi -> state akhir
- [ ] Bukti dana berpindah/hilang: tx hash + PoC script
- [ ] Hitung dampak nyata: berapa dana, seberapa sering
- [ ] Lolos kriteria program: scope, severity, "loss of funds"
- [ ] Cek duplikat (issue tracker, Discord, audit)

## 6. Laporan

- [ ] Judul: `[Program] Fitur X - <impact Y>`
- [ ] Ringkasan 1 paragraf
- [ ] Langkah reproduksi (numbered)
- [ ] Bukti: tx hash, PoC, screenshot/log
- [ ] Dampak: dana berapa, aset apa, kondisi apa
- [ ] Rekomendasi perbaikan
- [ ] Severity sesuai rubrik program

## 7. Versi kilat (15 menit per rilis)

1. [ ] Buka changelog/scope/JS diff -> sebutkan fitur/endpoint/instruction baru.
2. [ ] Tandai yang gerakkan dana atau ubah permission.
3. [ ] Tanya: "fitur ini ikut cek ownership & accounting pola lama?"
4. [ ] Cari 1 celah konsistensi -> cek cepat di fork/testnet.
5. [ ] Ada celah -> lanjut bikin PoC. Tidak ada -> catat dan lanjut.

## Aturan pengingat

- Fitur baru **sering** lupa satu hal yang fungsi lama sudah punya. Cari yang "beda sendiri".
- Kalau fitur baru terlihat "mirip banget" dengan yang lama, justru di situ letak bedanya.
- Deadline = edge case. Bug-nya biasanya bukan di happy path, tapi di batas (0, max, overflow, urutan panggil).
