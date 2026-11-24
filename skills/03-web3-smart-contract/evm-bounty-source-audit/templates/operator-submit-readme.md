# Operator submit kit — <PROGRAM> (<findings N>)

Isi bundel ini dan apa yang harus kamu lakukan, urut dari atas. Semua berkas teks di sini final:
tinggal salin-tempel ke form platform.

## Isi bundel

| berkas | gunanya |
|---|---|
| `<FindingA>-paste.md` | Temuan 1 (<satu baris mekanisme>) — **seluruh isi file ini** masuk ke form temuan pertama |
| `<FindingB>-paste.md` | Temuan 2 (<satu baris mekanisme>) |
| `APPENDIX.md` | Lampiran (tabel aturan, enumerasi, angka eksposur, apa yang **tidak** kita klaim) — tempel di ekor deskripsi |
| `MANIFEST.sha256` | Daftar hash semua artefak yang dikutip, supaya juri bisa memverifikasi sendiri |
| `README-SUBMIT.md` | Berkas ini |

## Langkah submit

1. **Login + deposit** di halaman program (ini bagianmu — jangan bagikan kredensial ke siapa pun).
2. Klik **Submit a finding**.
3. **Judul**: salin persis baris pertama file temuan (tanpa tanda `#`).
4. **Severity**: pilih `<SEVERITY>`.
5. **Description**: tempel seluruh isi file temuan mulai dari baris `Severity:` ke bawah — termasuk blok
   kode, tabel, dan bagian honest-bounds. Bagian itu bukan kelemahan; itu yang membuat laporan
   terbaca jujur dan spesifik.
6. **Lampiran**: tempel `APPENDIX.md` di akhir deskripsi, atau tautkan salinannya (gist) bila form
   membatasi panjang.
7. Ulangi untuk temuan berikutnya di form terpisah — <satu baris alasan kenapa dua root cause berbeda>.
8. Simpan ID/nomor temuan + salinan yang benar-benar dikirim.

## Checklist sebelum submit

- [ ] Login dan deposit selesai (gerbang operator).
- [ ] Severity sesuai yang tertulis di laporan, bukan dinaikkan — rating di atas bukti menggugurkan
      temuan yang valid.
- [ ] Tidak ada klaim dana bergerak di mainnet kecuali memang ada.
- [ ] Tidak ada kalimat soal proses internal atau alat bantu.
- [ ] Simpan salinan `*-paste.md` yang benar-benar dikirim.

## Kalau juri bertanya (jawaban sudah konsisten dengan laporan)

- **"Kenapa <SEVERITY>, bukan lebih tinggi?"** — <batas yang mengikat + angkanya>.
- **"Apakah PoC mengubah state/oracle secara manual?"** — <apa yang nyata: program deployed + akun
  live; apa yang sintetis: model flash-loan/saldo lokal — dan itu dinyatakan terbuka>.
- **"Apakah ada dana bergerak di mainnet?"** — <jawaban>.
- **"Apakah masalahnya hanya di satu instance?"** — <kelas: bentuk konfigurasi yang sama, dan siapa
  yang dilindungi oleh apa>.

## Catatan operator

Deposit, KYC payout, dan submit adalah bagianmu; saya tidak menyentuh kredensial, deposit, atau akun.
