---
name: race-condition-web-api
description: "Use when hunting Web/API race or TOCTOU. Burst repro steps."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [BugBounty, WebAPI, TOCTOU, RaceCondition]
---

# Race condition Web/API

Pola singkat untuk state-changing flow yang memisahkan cek dan perubahan state. Ini untuk target Web/API, bukan smart contract EVM (eksekusi transaksi EVM berurutan, jadi pola ini tidak berlaku di sana).

## When to Use

- Kode sekali pakai: kupon, gift card, referral, voucher
- Nilai numerik: saldo, poin, kredit, withdraw, refund
- State transisi: OTP/MFA validate, email activation, register then confirm, password reset
- Kuota: rate limit, one per user, vote/upvote, retry payment
- Unik: dua request sama-sama lolos cek "username available", registrasi ganda, atau benturan ID unik lain

## Ciri yang dicari

Backend menjalankan tiga langkah secara terpisah: verifikasi masih valid, potong nilai, lalu tandai terpakai. Kalau tidak ada row-level lock atau transaksi atomik, beberapa request bisa membaca status valid sebelum request pertama selesai menulis.

## Dua bentuk race

1. Identical copies: kirim N request identik bersamaan. Sukses kalau minimal 2 balas 2xx untuk resource yang seharusnya sekali pakai.
2. Different requests (partial construction): kirim daftar request berbeda dalam satu jendela sinkron, misal register lalu confirm memakai object yang sedang setengah jadi.

## Cara menembak

- Burp Repeater: pilih request, group, lalu Send group in parallel (HTTP/2 single-packet attack).
- Turbo Intruder: `engine=Engine.BURP2`, `gate` untuk menyamakan waktu kirim, lalu lepas burst.
- HTTP/2 penting karena satu packet mengurangi jitter. HTTP/1.1 multithreading sering terlalu tersebar dan gagal mereproduksi.
- Mulai dari 10 hingga 30 request di akun sendiri. Jangan gorong-jeorong target tanpa izin.

## Uji minimal sebelum burst

- [ ] Pastikan alur benar-benar state-changing dan ada kode/status sekali pakai
- [ ] Cek idempotensi: apakah request yang sama dua kali memang ditolak secara sequential
- [ ] Siapkan dua akun sendiri dengan marker unik kalau dampaknya lintas akun
- [ ] Catat status akhir sebelum burst (saldo, jumlah kupon terpakai, dll)

## Bukti yang harus dikumpulkan

- [ ] Minimal 2 respons 200 untuk satu kode sekali pakai, sisa request boleh 400
- [ ] Status akhir akun yang menunjukkan potongan berkali-kali
- [ ] Request lengkap, method, path, header penting, body, timestamp
- [ ] Perbandingan sequential (ditolak) vs concurrent (lolos)
- [ ] Jangan klaim ATO atau cross-tenant kalau belum dibuktikan

## Remediasi yang benar

Transaksi database atomik dengan `SELECT ... FOR UPDATE`, atau distributed lock seperti Redis Redlock. Validasi di application layer saja tidak cukup di bawah konkurensi.

## Jebakan

- P2 kadang dianggap High, bukan Critical. Jangan ikut klaim rating tanpa konteks program.
- Angka di judul writeup sering bertentangan dengan isi atau komentar pembaca. Jangan adopsi nominal maupun rating sebagai fakta tanpa sumber utama.
- Kalau burst tidak pernah menang, cek dulu apakah ada lock, queue, atau rate limit yang memang aktif.

## Referensi

Checklist lengkap: `C:/Users/TUF-GAMING/AppData/Local/hermes/checklists/web-api-checklist.md`, bagian 9b.
Sumber pola: writeup race condition kupon dan referensi Claude-BugHunter `hunt-race-condition` (pustaka eksternal, bukan skill terpasang). Skill terpasang untuk pola ini adalah `race-condition-web-api` itu sendiri, bukan `hunt-race-condition`.
