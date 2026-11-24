# Web3 Bug Bounty Writeups — Deep Read (klasifikasi + impact)

> 27 writeup ber-nominal dari bugbountyhunting.com, dibaca satu per satu.
> Kolom: protocol, payout, severity, kelas bug, akar masalah, dampak, pelajaran.
> `content_status`: `ok` = teks lengkap, `thin` = sebagian, `blocked` = 404/login wall.

---

## Ringkasan pola (27 writeup)

| Kelas bug | Jumlah | Contoh |
|---|---:|---|
| Access control / validasi input | 6 | Ocean, Betverse, Wormhole, dHEDGE, Silo, Q |
| Accounting / rounding / share | 5 | Silo, Sovryn, IPOR, Balancer, Tranchess |
| Reentrancy / urutan state | 3 | Tectonic, Sherlock, Tranchess |
| Delegatecall / proxy / precompile | 3 | Aurora, Moonbeam, Oasis |
| Konsensus / liveness / DoS | 3 | Oasys, Sei, Scroll |
| Token-standard edge (FoT, decimals, code-existence) | 3 | DFX, Balancer V2, Warden Swap |
| Lain (truncation, parsing, assembly, voting) | 4 | Polkadot, Interlay, Hyperlane, Q |

**Yang paling sering lahir bug:** (1) cek yang hilang, (2) asumsi accounting yang bocor saat ada callback/flashloan, (3) delegatecall yang bikin konteks panggilan bohong. Ini tiga hal yang sama relevannya buat EVM dan Solana (di Solana: missing owner/signer check, PDA bump, CPI context, accounting precision).

---

## 1. Aurora — Infinite Spend (Rainbow Bridge)

- **Payout:** $6.000.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Delegatecall context confusion / validasi caller di precompile native
- **Akar:** Precompile `ExitToNear` mencatat log dari alamat hardcoded; engine Aurora menganggap log itu janji penarikan yang sah dan berasumsi `msg.value > 0` berarti ETH sudah dikirim. `DELEGATECALL` ke precompile mewarisi `msg.value` caller tapi tidak memindahkan ETH, jadi engine menjadwalkan penarikan nETH yang tidak pernah dibiayai.
- **Dampak:** Exit berulang lewat delegatecall mencetak nETH di NEAR tanpa mengunci ETH; saldo attacker berlipat tiap siklus. Potensi kerugian 70k ETH + $200M aset bridge lain. Tidak ada dana hilang; dipatch setelah disclosure.
- **Pelajaran:** Jangan percaya `msg.value` atau emitter log hardcoded di precompile yang bisa dijangkau `DELEGATECALL`; validasi caller/address asli.

## 2. Moonbeam / Moonwell — Delegatecall Impersonation

- **Payout:** $1.050.000 ($1M Moonbeam + $50k Moonwell) · **Severity:** Critical · **Status:** ok
- **Kelas:** Delegatecall impersonation / `msg.sender` palsu di precompile ERC20 native
- **Akar:** `Erc20BalancesPrecompile` & `Erc20AssetsPrecompileSet` tidak memperhitungkan delegatecall, jadi kontrak jahat bisa meneruskan `msg.sender`-nya sendiri dan precompile tidak bisa membedakan caller asli. Bisa set allowance / transfer saldo victim.
- **Dampak:** Korban yang memanggil kontrak attacker bisa dikosongkan: flash-loan provider, LP token DEX (~$12.6M), MGlimmer Moonwell; loop deposit-borrow-transfer terhadap ~$100M. Tidak dieksekusi; dipatch.
- **Pelajaran:** Precompile jangan percaya `msg.sender` kalau delegatecall mungkin; autentikasi caller asli atau tolak konteks delegatecall.

## 3. Polkadot Frontier EVM — Integer Truncation

- **Payout:** $1.000.000 (Moonbeam $430k, Astar $250k, Polkadot $250k, Acala $70k) · **Severity:** Critical · **Status:** ok
- **Kelas:** Truncation antar-layer (256-bit EVM → 128-bit saldo Substrate)
- **Akar:** Frontier memotong `msg.value` 256-bit jadi 128-bit untuk transfer mata uang Substrate. `msg.value = 1<<128` membuat transfer nyata = 0, tapi kontrak yang percaya `msg.value` (wrapper WETH, pair DEX, vault lending) mengkredit penuh. Attacker menarik kredit hantu itu jadi token asli.
- **Dampak:** Drain kontrak wrapped native >$44M + ~$150M aset pinjaman, dengan kontagin ke DeFi parachain. Ada tx mencurigakan sesudah lapor; dipatch (CVE-2022-31111).
- **Pelajaran:** Jangan truncate jumlah antar-layer; `msg.value` kontrak harus selalu sama dengan jumlah yang benar-benar ditransfer.

## 4. Sherlock — Cross-Protocol Reentrancy

- **Payout:** $250.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Reentransi lintas protokol / manipulasi exchange rate lewat view balance
- **Akar:** `swap1Inch` Euler memberi callback sebelum `eUSDC` totalSupply naik, jadi `_balanceOf()` Sherlock yang membaca `balanceOfUnderlying` (shares × exchangeRate) melihat rate inflasi setelah attacker transfer USDC ke Euler. Attacker redeem saham Sherlock pada rate inflasi dan tarik lebih banyak USDC.
- **Dampak:** Bisa drain sebagian besar pool staking Sherlock, tapi butuh stake terkunci 6 bulan (>$2M modal) + ~$1B flash loan, jadi dana tidak langsung terancam. Fix: view function Euler revert di bawah reentrancy lock.
- **Pelajaran:** Bacaan balance/oracle saat callback lintas protokol bisa dimanipulasi; buat minting atomik atau kunci view function dengan reentrancy lock.

## 5. Balancer V2 — Missing Code-Existence Check

- **Payout:** $250.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Tidak ada cek keberadaan kode di `safeTransferFrom` (frontrun deploy ERC20)
- **Akar:** Fork SafeERC20 gas-optimized Balancer menghilangkan `Address.isContract`, jadi `safeTransferFrom` ke ERC20 yang belum dideploy sukses. Attacker yang frontrun tx deploy token bisa prediksi alamatnya, mendaftarkan saldo Vault hantu, dan menarik deposit nyata begitu token ada + likuiditas masuk.
- **Dampak:** Kasus terburuk ~$120M (frontrun semua token baru) atau ~$80M dari satu LBP volume tinggi. Dibayar $250k sebagai critical.
- **Pelajaran:** Fork library yang dioptimasi gas harus pertahankan safety check; sukses ke alamat tanpa kode bukan transfer token.

## 6. Interlay — Incomplete Tx Parsing (interBTC)

- **Payout:** $200.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Parsing transaksi tidak lengkap / malleability + ekstraksi alamat heuristik
- **Akar:** `BytesParser` mengabaikan byte sisa, jadi dua transaksi berbeda parse jadi `Transaction` yang sama dan lolos cek perbedaan di `report_vault_double_payment`. Heuristik ekstraksi alamat ScriptSig/witness bisa dibuat supaya tx seolah dari vault lain. Keduanya memungkinkan laporan pencurian palsu dan slashing paksa.
- **Dampak:** Attacker bisa memaksa likuidasi vault mana pun (curian 5% kolateral) dan membuat semua vault kena ban, merusak fraud proof bridge. Interlay menonaktifkan fungsi pelaporan yang rentan.
- **Pelajaran:** Bandingkan txid/byte kanonik, bukan struct hasil parse; jangan infer alamat Bitcoin dari template script heuristik.

## 7. Tranchess — Checkpoint Desync

- **Payout:** $200.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Akuntasi checkpoint hilang/usang (desync early-return blok yang sama)
- **Akar:** `_checkpoint()` early-return kalau sudah dipanggil di blok yang sama. Attacker yang memicu rebalance lalu memanggil `claimableRewards()` lebih dulu membuat checkpoint di dalam `deposit()` terlewat. `spareAmount` dihitung dari total supply Queen yang tidak sinkron dengan saldo Queen nyata, lalu attacker deposit jumlah spare dan menariknya.
- **Dampak:** Pencurian langsung dari staker saat kondisi rebalance terpenuhi: sampai ~815 BTC + 1438 ETH dengan dana sendiri, atau ~46.8 BTC + 156 ETH tanpa. ShareStaking jadi insolven.
- **Pelajaran:** Guard early-return per-blok pada fungsi checkpoint/accounting bisa dimanfaatkan untuk desync state; jangan biarkan panggilan publik melewati akuntansi.

## 8. Oasys — Consensus Griefing → Infinite Mint

- **Payout:** $200.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Konsensus / validator-jailing griefing → mint tak terbatas
- **Akar:** `IsSystemTransaction` mengklasifikasi panggilan ke genesis contract dengan `gasPrice == 0` sebagai system tx. Producer blok (`block.coinbase`, cuma diamankan `onlyCoinbase`) bisa kirim `StakeManager.slash` dengan gas price 1 wei, sehingga tidak dianggap system tx dan masuk blok biasa. Slash 500 kali menjail validator dan menyita rewardnya; attacker cuma butuh ~40 blok producer dari epoch 5760 blok untuk menjail 23 validator lain.
- **Dampak:** Attacker staking ~$50k bisa menjail semua validator, jadi satu-satunya producer: halt jaringan (butuh hard fork), sensor, dan `Environment.updateValue` untuk mint OAS tanpa batas.
- **Pelajaran:** Jangan klasifikasi panggilan privileged berdasarkan gas price; allowlist system tx harus menyebut kontrak+method eksak, dan panggilan ubah-konsensus butuh lebih dari `msg.sender == block.coinbase`.

## 9. Silo Finance — Rounding/Accounting (Compound fork)

- **Payout:** $100.000 · **Severity:** Critical · **Status:** thin (thread terpotong di login wall X)
- **Kelas:** Rounding / accounting error di lending market fork Compound
- **Akar:** Detail persis tidak ada di thread; konteks mengarah ke kelas yang sama dengan drain Hundred Finance April 2023: attacker jadi satu-satunya supplier/borrower pasar collateral (`cToken.totalSupply == 0`) dan error rounding memungkinkan drain; pola yang sama ditemukan di kode Silo.
- **Dampak:** Flaw rounding/accounting di market Silo bisa mengekstrak nilai atau merusak akuntansi share; divalidasi dan dibayar $100k critical.
- **Pelajaran:** Re-audit fork terhadap insiden yang diketahui di protokol induk: asumsi rounding dan pasar satu sisi berulang di derivatif Compound.

## 10. Sei Network — ABCI EndBlocker Panic DoS

- **Payout:** $75.000 · **Severity:** Critical · **Status:** blocked (writeup 404)
- **Kelas:** DoS konsensus / panic yang tidak tertangani (ABCI EndBlocker)
- **Akar:** Best-effort: panic tidak ter-recover di ABCI EndBlocker — module EVM coinbase sweep memakai `BankKeeper.GetBalance` (locked + unlocked) lalu mengirim total itu ke `SendCoinsAndWei` yang error saat sebagian balance terkunci, dan jalur error memanggil `panic()`. Hook ABCI tidak terbungkus recovery `RunTx` Cosmos, jadi node crash.
- **Dampak:** Vesting account dibuat di alamat coinbase deterministik per-tx dengan token terkunci → blok EVM berikutnya panic, chain halt; butuh hard fork.
- **Pelajaran:** Jangan `panic` di hook ABCI Begin/EndBlock; pakai `SpendableCoins`, bukan `GetBalance`, saat sweep saldo.

## 11. Q Blockchain — Double Voting

- **Payout:** $50.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Double voting / accounting voting power
- **Akar:** `VotingWeightProxy.getVotingWeight` menjumlahkan `pendingUnlockAmount` user dan `delegationInfos[_who].receivedWeight`, tapi `announceUnlock` hanya set `pendingUnlockTime/Amount` tanpa menghapus token dari `receivedWeight` sampai waktu unlock. Delegator A delegate ke B, B vote dengan bobot A, lalu A announceUnlock dan vote di proposal yang sama → token terkunci A dihitung dua kali.
- **Dampak:** Token Q terkunci sama mempengaruhi proposal dua kali; voter bisa melebihi voting power nyata dan memanipulasi governance (ubahan konstitusi, appointment root node, vote slashing).
- **Pelajaran:** Voting weight harus snapshot konsisten per sumber; unlock pending harus langsung berhenti menghitung bobot delegasi, bukan di waktu unlock.

## 12. Wormhole — Guardian-Set Expiration Bypass

- **Payout:** $50.000 · **Severity:** High · **Status:** ok
- **Kelas:** Access control / bypass expiration guardian set
- **Akar:** Verifikasi VAA Wormchain mengekspire guardian set hanya kalau `0 < ExpirationTime < blockTime`, jadi set dengan `ExpirationTime == 0` tidak pernah expire. Genesis set 0 dan 1 dua-duanya `ExpirationTime 0` dan memakai key yang sama, sehingga satu key itu memenuhi quorum 13-of-19 untuk VAA apa pun di Wormchain.
- **Dampak:** Model keamanan guardian di Wormchain runtuh jadi satu key: kebocoran key genesis bisa memalsukan VAA dan mengirim pesan lintas-chain sembarangan.
- **Pelajaran:** Cek expiration harus menangani set terbaru secara khusus dan mengekspire set usang secara eksplisit; key genesis bersama tidak boleh tetap berlaku bersama set baru.

## 13. Alchemist (MIST/Aludel) — Admin Brick

- **Payout:** $28.000 · **Severity:** High · **Status:** ok
- **Kelas:** Missing access control + transisi state tidak dicek di timelock 2 langkah
- **Akar:** `TimelockConfig.confirmChange()` tidak punya modifier `onlyAdmin` (berbeda dengan `requestChange`/`cancelChange`) dan tidak memverifikasi bahwa perubahan sudah di-request. Mapping `_pending` yang tidak ada mengembalikan struct zero, bukan revert, jadi siapa pun bisa `confirmChange(configID)` sembarang dan langsung set ke 0.
- **Dampak:** Attacker brick config mint-recipient ke 0 → `Alchemist.advance()` revert dan inflasi $MIST + streaming ke staker Aludel berhenti permanen. Dana tidak dicuri tapi reward brick.
- **Pelajaran:** Terapkan access control konsisten di tiap langkah proses multi-step dan verifikasi langkah sebelumnya; mapping miss di Solidity mengembalikan struct zero, bukan revert.

## 14. Oasis Earn — Unprotected delegateCall / ACE

- **Payout:** $20.000 · **Severity:** High · **Status:** blocked (halaman 205 byte)
- **Kelas:** DelegateCall tidak dilindungi / state confusion (arbitrary code execution)
- **Akar:** Oasis Earn berasumsi `executeOp` hanya jalan di dalam DSProxy user, tapi bisa dipanggil langsung ke `OperationExecutor` dengan storage kosong. DelegateCall allowlist terbatas mencapai `InitializableUpgradeabilityProxy` (proxy AAVE LendingPool); `initialize()` dengan data kosong saat implementation = 0 membuka delegateCall kedua dengan target & calldata attacker, dan nama `CustomOperation` melewati `verifyAction`.
- **Dampak:** Rantai delegateCall memberi arbitrary code execution atas platform Oasis; attacker bisa pasang kontrak selfdestruct dan menghancurkan kontrak target, brick platform.
- **Pelajaran:** Jangan berasumsi konteks caller: target delegateCall dan jalur initializer harus divalidasi independen dari asal panggilan.

## 15. Tidak diketahui — High $20K

- **Payout:** $20.000 · **Severity:** High · **Status:** blocked (mirror.xyz 404)
- **Kelas:** Tidak determinable
- **Akar/Dampak:** Postingan mirror.xyz sekarang 404 (migrasi ke paragraph.com); tidak ada teks yang tersisa. Hanya judul yang mengindikasikan high severity $20K.
- **Pelajaran:** Arsip link payout sebelum post mirror.xyz migrasi; 404 menghancurkan semua detail teknis.

## 16. Sovryn — Dust/Share Inflation

- **Payout:** $15.000 · **Severity:** Medium · **Status:** ok
- **Kelas:** Share/dust inflation (akuntasi share)
- **Akar:** Jalan burn/redeem Sovryn menolkan sisa balance ≤ 10 wei, menciptakan gap "debu" tidak terakuntasi antara `totalAssets` dan `totalSupply` yang merusak invariant share price (pola inflasi totalSupply=1/totalAssets=2).
- **Dampak:** Attacker bisa inflate share price dan mencuri nilai dari depositor lain; pola sama menyebabkan kerugian $464k Wise Lending dan $6M MIM.
- **Pelajaran:** Threshold rounding/debu yang mengubah balance tanpa mint/burn share sebanding merusak invariant totalAssets/totalSupply.

## 17. DFX Finance — Fee-on-Transfer Token

- **Payout:** $10.000 (dua finding medium) · **Severity:** Medium · **Status:** ok
- **Kelas:** Token fee-on-transfer (FoT) tidak didukung / asumsi quote asset salah
- **Akar:** DFX hargai USDC hardcoded 1e8 dan merutekan semua pair lewat USDC tanpa menangani FoT, jadi mis-harga di curve FoT/USDC dan attacker bisa drain likuiditas via transfer fee.
- **Dampak:** LP di curve FoT/USDC terkikis dan pool tidak bisa dipakai; FoT 10% + oracle USDC 1:1 memungkinkan ekstraksi jauh lebih banyak USDC dari deposit.
- **Pelajaran:** Jangan asumsikan quote/bridge asset bebas fee atau harga tetap; validasi jumlah diterima dan perlakukan token FoT sebagai tidak didukung.

## 18. Ocean Protocol — Missing onlyOwner

- **Payout:** $5.000 · **Severity:** Medium · **Status:** ok
- **Kelas:** Access control / `onlyOwner` hilang
- **Akar:** `Dispenser.ownerWithdraw()` tidak punya cek `onlyOwner`, jadi siapa pun bisa memanggil dan memaksa seluruh saldo datatoken kontrak ke payment collector token.
- **Dampak:** Dispenser tanpa datatoken, owner tidak bisa dispense ke penerima yang seharusnya — DoS permanen pada fungsi dispense.
- **Pelajaran:** Setiap fungsi state-changing "owner" harus enforce modifier owner; satu `onlyOwner` hilang = redirect dana gratis dan trivial.

## 19. Lybra Finance — totalSupply Manipulation

- **Payout:** $5.000 · **Severity:** Critical (dibayar $5k setelah proyek dispute likelihood) · **Status:** ok
- **Kelas:** Reward/share accounting via manipulasi `totalSupply`
- **Akar:** `esLBRBoost` menghitung boost dari `totalSupply`, dan `ProtocolRewardsPool` mengizinkan unstake (burn) + restake (mint) esLBR, jadi whale bisa flash-kurangi `totalSupply` tepat saat klaim reward.
- **Dampak:** Whale/kartel menginflate share reward dan mint LBR dengan mengorbankan holder lain; kartel 2M esLBR dapat ~13% reward ekstra, ~580.000 LBR setahun.
- **Pelajaran:** Kalau `totalSupply` masuk formula reward/boost, perlakukan burn-and-mint sebagai kendali attacker dan kecualikan dari kalkulasi.

## 20. Hyperlane — Inline Assembly Revert

- **Payout:** $2.500 · **Severity:** Low · **Status:** ok
- **Kelas:** Revert inline-assembly salah (panjang returndata buruk)
- **Akar:** `OwnableMulticall.proxyCalls` revert dengan `revert(add(returnData, 32), returnData)`, meneruskan pointer return-data sebagai argumen panjang, bukan `returndatasize()`/`mload(returnData)`, jadi blob revert malformasi.
- **Dampak:** Caller & tooling menerima revert data korup dan tidak bisa decode alasan gagal; dana tidak langsung terancam.
- **Pelajaran:** Saat bubble-up revert data di assembly, argumen kedua harus panjang data (`returndatasize()`), bukan pointer.

## 21. Tectonic (Cronos) — Reentrancy via Swap Path

- **Payout:** $1.600 · **Severity:** Critical · **Status:** ok
- **Kelas:** Reentrancy / urutan update state lintas swap eksternal
- **Akar:** `performConversionForTokens()` publik dan menghitung `tonicBalanceAfter - tonicBalanceBefore` di sekitar path swap VVS arbitrer yang tidak di-whitelist; token jahat di tengah path re-enter `stake()`, jadi TONIC attacker dihitung sebagai output swap dan dibayar sebagai "reward", mencetak xTonic gratis.
- **Dampak:** Posisi $23k TONIC drain >$2.5M dalam satu tx dan skew rate TONIC/xTonic (59%→73%); staker lama tidak bisa tarik deposit; bisa diulang hingga pool kosong.
- **Pelajaran:** Jangan ukur token diterima dari delta balance lintas panggilan eksternal arbitrer — whitelist path swap dan pakai reentrancy guard.

## 22. Warden Swap — Payable Fund Lock

- **Payout:** $1.000 · **Severity:** Low · **Status:** ok
- **Kelas:** Validasi input hilang / dana payable terkunci
- **Akar:** `WardenRouterV2.swap()` payable dan menerima ETH bersama parameter source token ERC20 valid, tapi tidak memvalidasi `msg.value` terhadap path swap yang dipilih, jadi ETH diambil tapi tidak dipakai maupun direfund.
- **Dampak:** ETH user terkunci permanen di WardenRouterV2 tanpa jalur pemulihan; dana absorbed bisa jadi pemicu exploit lanjutan. Low karena butuh perilaku user tidak sengaja.
- **Pelajaran:** Validasi `msg.value` terhadap swap path dan refund/tolak ETH native untuk swap ERC20.

## 23. Betverse — Function Visibility

- **Payout:** $1.000 · **Severity:** Critical · **Status:** ok
- **Kelas:** Access control / visibility fungsi salah
- **Akar:** `transferTokenToLockedAddresses()` kebetulan dideklarasikan `public` bukan `internal`, jadi siapa pun bisa memanggil dengan parameter sembarang dan tiap panggilan mentransfer `amount.div(term)` BToken ke kontrak TokenTimelock pilihan attacker.
- **Dampak:** Attacker berulang kali menyapu seluruh saldo BToken kontrak ICO Betverse ke timelock miliknya, kerugian signifikan ke ICO dan user.
- **Pelajaran:** Pakai visibility terketat (`internal`) + access control untuk logic minting/transfer privileged.

## 24. IPOR — Token Decimal Mismatch

- **Payout:** $1.000 · **Severity:** Low · **Status:** ok
- **Kelas:** Ketidakcocokan presisi desimal token
- **Akar:** `wadMiltonErc20BalanceBeforeRedeem` diberi saldo ERC20 mentah (6 desimal untuk USDC/USDT) bukan nilai WAD 18-desimal yang dikonversi, jadi `calculateRebalanceAmountBeforeWithdraw` jalan dengan skala salah.
- **Dampak:** Aset lebih banyak dari seharusnya ditarik dari vault penghasil bunga Stanley saat withdraw, mengikis pendapatan LP, bukan mencuri dana user secara langsung.
- **Pelajaran:** Normalisasi semua jumlah token ke presisi internal 18-desimal sebelum aritmetika.

## 25. Scroll — Forced Re-org / Chain Halt

- **Payout:** $1.000 · **Severity:** Critical · **Status:** thin (thread terpotong)
- **Kelas:** Konsensus / chain-halt DoS (re-org paksa)
- **Akar:** Siapa pun bisa memaksa Scroll L2 ke re-org tak berujung yang menghentikan produksi blok; mekanisme contract-level tidak ada di thread. Scroll menyebutnya known issue audit Trail of Bits yang dijadwalkan untuk upgrade Euclid.
- **Dampak:** >$100M TVL beku: tidak ada tx/withdraw, aksi DeFi time-sensitive (top-up likuidasi, update oracle) gagal, sequencer berhenti mencari fee. Serangan nol biaya dan bisa ditahan terus.
- **Pelajaran:** Perlakukan vektor re-org/chain-halt sebagai critical dan verifikasi fix terhadap kode yang dideploy, bukan attestasi audit.

## 26. dHEDGE — Swap Path Validation

- **Payout:** $500 (goodwill) · **Severity:** Critical · **Status:** ok
- **Kelas:** Validasi input / bypass access control di swap guard
- **Akar:** Guard `execTransaction` untuk UniswapV3 `exactInput` hanya memvalidasi asset asal & tujuan, bukan token path perantara, dan mengizinkan slippage 10%, jadi manager bisa merutekan dana pool lewat pool fake USDT/FAKE dan FAKE/USDC berulang kali.
- **Dampak:** Manager jahat bisa mengikis nilai pool tiap swap dan drain ~96% pool dalam satu tx (sampai ~$14.4M dari pool $15M), melanggar janji non-custodial dHEDGE. Tim menutup won't-fix tanpa mitigasi nyata.
- **Pelajaran:** Validasi seluruh swap path, bukan hanya endpoint, dan batasi kerugian kumulatif per transaksi, bukan slippage per-swap.

## 27. Balancer — Duplicate Claim (MerkleOrchard)

- **Payout:** 50 ETH · **Severity:** Critical · **Status:** ok
- **Kelas:** Logic error / klaim duplikat (bypass update state)
- **Akar:** Di `MerkleOrchard.claimDistributions`, batch beberapa klaim dengan `distributionId` sama menjaga `currentWordIndex == distributionWordIndex` tetap true, melewati `_setClaimedBits` (yang hanya jalan untuk elemen array terakhir), jadi klaim yang sama bisa diputar ulang dalam satu transaksi.
- **Dampak:** LP mana pun bisa mengalikan klaim reward dan drain saldo vault MerkleOrchard (~$3.2M di Ethereum, Polygon, Arbitrum), mencuri yield belum diklaim dari LP lain. Flaw live di produksi ~463 hari.
- **Pelajaran:** Update flag claimed per klaim secara independen dari posisi array, dan fuzz batch multi-klaim.

---

## Cara pakai file ini

- **Precedent negosiasi:** pakai payout + severity + kelas bug sebagai komparabel. Contoh argumen: "critical fund-loss di bridge/DC serupa dibayar $100k–$250k (Moonbeam, Balancer V2, Oasys), laporan ini sebanding."
- **Pola buru:** 3 kelas teratas (access control, accounting/rounding, reentrancy/state ordering) + delegatecall/proxy + konsensus/liveness. Di Solana, terjemahannya: owner/signer check, PDA bump/derivation, CPI context, precision/rounding, account state ordering.
- **Laporan:** tiap entri punya "pelajaran" satu baris yang bisa langsung dipakai sebagai rekomendasi fix di laporan.
