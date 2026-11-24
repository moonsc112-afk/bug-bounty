# Video and image payloads in X posts

Use when `tweet.media.all` exists or a `facets` entry has type `media`, and the
tweet text alone cannot carry the claim. The media is the article. The fxtwitter
JSON gives direct `video.twimg.com` URLs plus duration and resolution, so no
browser or x.com session is needed.

## Procedure

1. Confirm the post id matches the requested id, then read `tweet.media.all[0]`.
   Pick the largest `formats[]` mp4 (highest bitrate) for video, or the image URL
   for a single picture. Record `duration` and `width`/`height`.
2. Download with an explicit native `C:/...` output path (the bash here maps
   bare `/tmp` to `C:\tmp` for native curl):

   ```bash
   SCRATCH="C:/Users/<user>/AppData/Local/hermes/cache/scratch/frameextract"
   mkdir -p "$SCRATCH/frames"
   curl -sL --max-time 120 "<media.all[0].url>" -o "$SCRATCH/media.mp4"
   ```

3. Sample frames at a rate tied to the item count, not to raw seconds. A
   numbered slide list usually shows one item per slide, so `fps=2/3` (one frame
   per 1.5 s) on a 15 s video yielded exactly 10 frames for a 10-item list:

   ```bash
   ffmpeg -y -loglevel error -i "$SCRATCH/media.mp4" \
     -vf "fps=2/3,scale=360:-1" "$SCRATCH/frames/f_%02d.png"
   ```

   For longer or unknown lists, start at `fps=1` and increase only if items look
   duplicated across adjacent frames. For a single image, skip this step.
4. Build a numbered contact sheet with PIL for a quick visual scan, then read
   each frame individually for exact text. Keep the full-resolution frames.
5. For text, run `scripts/windows_ocr.ps1` on each frame. Upscale small frames
   3x to 4x with Lanczos, raise contrast to about 1.4 and sharpness to about 2.0,
   and save a separate `*_up.png` before OCR. This is what makes 360 px wide
   slide text legible; plain 360 px frames lose most words.
6. Reconstruct the list from the line output, keep source wording, and mark any
   word inferred from a garbled glyph as reconstructed in the deliverable.
   Cross-check that the item count from the video matches the title's claimed
   count before reporting it.

## OCR reader rules

- Invoke as `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  "<skilldir>/scripts/windows_ocr.ps1" -Path "C:\...\frame.png"`.
- The script converts forward slashes in `-Path` to backslashes internally.
  `StorageFile.GetFileFromPathAsync` fails on a `C:/...` path, so do not skip
  that conversion when adapting it.
- `Windows.Globalization.Language` must be registered as a WinRT type before
  `New-Object`, or engine creation returns null.
- If both en-US and en-GB are installed, prefer en-US for these English infographic
  slides. Available languages can be listed from
  `[Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages`.
- OCR returns lines in visual reading order. In a two-column slide it reads one
  column top to bottom, then the other; use that to pair each heading with the
  description directly beneath it rather than trusting a flat concatenation.
- OCR places a bell character (\u0007) where an arrow or emoji glyph was not
  recognised. Treat that as a missing connective word, not as text to quote.

## Triage

A short list video is a method-guide/essay item, not a finding. It has no
request/response pairs, repro, marker, timeline, or payout. Report it as a
checklist with a caveat and keep it out of the finding checklist. When paired
with a resource-directory post, cross-map the two into a topic-to-site matrix
and state how many listed items apply to the operator's actual stack.
