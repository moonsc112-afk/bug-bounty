# Native ARM64 library analysis for APK reviews

Use this path when a lead points into a bundled `.so` (crypto envelopes, protocol parsers, key derivation). Automated provider selection is oriented to PE/macOS native targets, so drive the locally installed Ghidra headless directly for ARM64 ELF.

## 1. Extract and lay out

- Decompiled libs are already at `E:/audit/<t>/apktool/lib/arm64-v8a/` after apktool.
- Create `E:/audit/<t>/native/scripts/` for Java post-scripts and a separate Ghidra project directory.
- Keep all decompiler output and logs under `E:/audit/<t>/native/`.

## 2. Map report addresses before decompiling

A report's RVAs are rarely the address Ghidra displays. Parse the ELF PT_LOAD headers with Python stdlib `struct` (e_phoff at 0x20, e_phentsize at 0x36, e_phnum at 0x38, then 8-byte p_offset/p_vaddr/p_paddr/p_filesz). For extracted Android `.so` files the first LOAD usually maps file offset 1:1 to vaddr; Ghidra's default image base is `0x100000`, so a report RVA `r` is typically at `0x100000 + r` in Ghidra. Confirm by checking which of `r` and `r + 0x100000` contains a function. Also locate quoted error strings with a raw byte search in the file and use the same mapping to confirm the target function references them.

## 3. Java post-script rules (Ghidra 12)

- Filename must equal the public class name; extend `ghidra.app.script.GhidraScript`; override `public void run() throws Exception`.
- Import `java.io.File` and `java.io.PrintWriter` explicitly; the script compiler does not add them.
- `getReferencesTo(Address)` returns `Reference[]`, not an iterator. Iterate the array and use `getFunctionContaining(r.getFromAddress())`.
- If auto-analysis created no function at the report address, call `createFunction(addr, name)` and decompile it. Verify the result: a real function body should reference the expected strings or call the expected OpenSSL/crypto APIs. Garbage output means the address is wrong.
- Decompile with `DecompInterface.openProgram(currentProgram)` and `decompileFunction(f, 180, monitor)`; write `getDecompiledFunction().getC()` to a file rather than to stdout.

## 4. Run headless through a wrapper batch file

Write a `.bat` containing:

```
call "<Ghidra>\support\analyzeHeadless.bat" E:\audit\<t>\ghidra_project <name> -import E:\audit\<t>\apktool\lib\arm64-v8a\<lib>.so -scriptPath E:\audit\<t>\native\scripts -postScript <Script>.java
```

Invoke from git-bash as `cmd.exe /c 'E:\audit\<t>\native\run-ghidra.bat' > log 2>&1`. Initial analysis of a ~1 MB library takes roughly two minutes; poll the log. For a second pass over the saved project use `-process -noanalysis` instead of `-import`.

- For a large library (10 MB+), the first auto-analysis can run 10+ minutes and emit thousands of `VarnodeContext` and demangled-address-table warnings that do not stop the run. Poll until `REPORT: Analysis succeeded` and the script's `DONE` line appear; killing and restarting discards the analysis work.
- While Ghidra analyzes, `E:/tools/venv/Scripts/python.exe` has capstone installed and can disassemble a small address range for an opcode-level check of a specific instruction sequence.

## 5. What to verify in a crypto envelope parser

- Signedness and width of length fields (a `ushort` read from two bytes promoted to `ulong` changes how `length >= ek_len + tag` is evaluated).
- Bounds checks happen before pointer arithmetic: version byte, key id, wrapped-key length, IV and tag offsets, and plaintext length.
- AAD bytes must be identical in encrypt and decrypt paths; random IV generation belongs in the encrypt path (e.g. EVP_SealInit) and IV reuse is the bug to look for when it is absent.
- Error-code numbering: compare every return path with the caller's expected codes; a missing code is a robustness issue, not a security finding unless the caller treats the substitute code as success.
- For AEAD frame crypto, trace the callers of the tag/authentication function to locate nonce construction. A base salt XORed with a per-frame counter from the frame header is the expected SFrame design; a fixed salt reused across frames is the finding. Confirm the counter source and the derived nonce length before claiming reuse.
- A forced function whose decompiled body is plausible still needs a caller/JNI entry trace before calling it a finding.
