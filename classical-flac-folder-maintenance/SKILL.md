---
name: classical-flac-folder-maintenance
description: Organize, tag, rename, clean, add artwork to, and verify FLAC folders for classical music using a composer/work/performance structure instead of a pop release structure. Use when Codex needs to process new classical FLAC files, normalize classical Vorbis comments, split source albums into per-work folders, or align filenames, folder names, and artwork with the established classical library layout.
---

# Classical FLAC Folder Maintenance

Use this skill for manual cleanup and normalization of classical FLAC folders.

## Operating Principles

- Treat the work folder as the canonical unit, not the original album.
- Default to a fast source-release pass when the folder still looks like a compilation or box set.
- Prefer mechanical cleanup first, then musical judgment.
- Read existing tags before writing anything.
- Keep the workflow conservative: preserve valid source context unless it conflicts with the classical library model.
- Favor under-tagging over speculative tagging. If a credit cannot be tied to a trustworthy source or the file itself, leave it unchanged.

## Fast Path

Use this order when the folder looks unfinished, mixed, or source-like:

1. Inspect the folder tree, FLAC tags, and non-FLAC files.
2. Decide whether the folder is a true single-work folder or a source-release container.
3. If one folder contains multiple unique `work` values, or the contents clearly span multiple works/discs, split by work before doing fine-grained cleanup.
4. Verify the release title and release year early.
5. Normalize tags, filenames, artwork, ReplayGain, and integrity.

This avoids spending time polishing a folder that still needs to be split.

## Scope

- Read and write FLAC Vorbis comments directly with Python 3.12 and `mutagen`.
- On Windows, if `py -3.12` fails even though Python 3.12 is installed, run `py -0p` and use the discovered absolute interpreter path directly.
- Prefer `mutagen.flac.FLAC` for comments and embedded pictures.
- Use `metaflac` when it is more direct for FLAC metadata inspection, picture import/export, or ReplayGain work.
- Use `scripts\classical_folder_helper.py` for repeatable mechanical cleanup such as `tracknumber` zero-padding, source-folder splitting, cautious folder/file renaming, `folder.*` extraction or sibling-cover reuse, trailing `ID3v1` stripping, and junk-file removal.
- Keep the workflow manual-first until the user asks for automation.

## Canonical Library Structure

- Top-level folder = composer name, usually `Surname, Firstname`.
- Use `Anonymous` for anonymous works.
- One subfolder per musical work.
- Name the work folder as `work-folder-name (performance-folder-name)`.
- Name FLAC files as `NN) title.flac`.
- Keep one embedded front cover per FLAC and one `folder.*` image in the work folder.
- Treat the work folder, not the original album, as the canonical filesystem object.
- If a work folder has embedded front cover art in the FLAC files but no separate `folder.*` yet, extract the embedded front cover and save it as `folder.*`.

## Source-Release Container Detection

Treat a folder as a source-release container, not a finished work folder, when any of these are true:

- multiple unique `work` values appear in one folder
- the folder contains disc subfolders or obvious split-disc structure
- the folder has one shared cover and tracks clearly belong to more than one work
- the folder name looks like a release title rather than a work title
- the folder still carries compilation-style metadata such as mixed dates, mixed work names, or placeholder album text

When that happens:

- split per work first
- keep shared `album` context identical across the sibling work folders when it comes from the same release
- copy or extract the shared cover into each derived work folder
- do not try to force the whole container into one work folder

Curated retrospective, anthology, box-set, and compilation releases are an exception when the release is already arranged into themed discs or excerpt folders.

- Keep the release-curated thematic folders intact.
- Do not auto-split those folders into per-work canonical folders just because the `work` tags differ.
- Treat `work` as metadata inside the themed folder structure, not as a mandate to reorganize the release.

## Canonical Tag Model

- Keep only these Vorbis comment fields when they have values:
  `replaygain_*`, `composer`, `work`, `title`, `tracknumber`, `date`, `genre`, `performance`, `movement`, `conductor`, `orchestra`, `ensemble`, `album`, `albumartist`.
- Treat `composer` as the primary organizing field. Do not use `artist` for this library.
- Keep `work` as the full canonical work title.
- Keep `title` as the track title only, usually the movement title without repeating the work name.
- Use `movement` when the track is a movement and the numbered movement label matters, for example `I. Allegro`.
- Use `performance` as a semicolon-separated summary of the credited performance forces.
- Do not use `performer` for this library. Use `performance`, `conductor`, `orchestra`, and `ensemble` only when they are actually applicable.
- If a mechanical cleanup step reports a `performer`-style retag for a classical folder, treat that as a prompt to validate or rewrite the canonical `performance`/`conductor`/`orchestra`/`ensemble` fields instead; never write or preserve `performer`.
- Treat `performance` as a sourced credit field, not as free text.
- Allow `album` to preserve the source release title even when the folder represents only one extracted work.
- Allow `albumartist` when the source data meaningfully uses it, but do not let it drive folder naming.
- Treat `date` as the release year only unless the user explicitly wants a fuller date.
- Keep `genre` to exactly one value.
- Remove source-store and release-noise fields such as `artist`, `comment`, `organization`, `label`, `catalog`, `url`, and similar noise.

## Workflow

1. Inspect the folder contents, existing FLAC tags, and non-FLAC files before editing.
2. Identify the intended composer, work, performance credits, and source release title from the files, sibling work folders, or trusted source data.
3. If the folder is a source-release container, split it by work first.
4. Normalize the allowed Vorbis comment set and remove disallowed fields.
5. If `album` is missing, equals the work-folder name, or clearly mirrors the per-work title plus performance suffix instead of the source release, replace it with the best verified source release title.
6. Run `scripts\classical_folder_helper.py` for mechanical cleanup.
7. Write or fix ReplayGain for the complete work folder as one treatment.
8. Reopen the FLAC files and verify the written tags.
9. Rename files, folders, and artwork from the verified tags and performance fields.
10. If a work folder contains duplicate track numbers or an implausible track count, check whether some files actually belong to a sibling work from the same source release before deleting anything.
11. Remove junk files and leftover source-release clutter.
12. Test every FLAC with `flac -t` or `flac.exe -t` before finishing.

## Helper Script

- Run `py -3.12 scripts\classical_folder_helper.py <target-folder> --dry-run` first to preview file edits.
- Run the same command without `--dry-run` to apply the mechanical cleanup actions.
- Use the helper early when the incoming batch still looks like a source release rather than finished work folders.
- The helper may:
  - split direct-FLAC or mixed-work source folders into per-work folders
  - normalize `tracknumber`
  - normalize filenames from tags
  - extract missing `folder.*` art from embedded FLAC front cover art
  - copy `folder.*` art from a clearly matching sibling work folder when the local release art is obviously shared
  - embed `folder.*` back into FLACs that lack pictures
  - strip trailing `ID3v1` tags from FLACs
  - remove junk files such as `Thumbs.db` and `.DS_Store`
- Keep the helper conservative around existing suffix-rich folder names. If a folder already has a meaningful performance suffix, prefer preserving it over rebuilding it from incomplete structured tags.
- Do not rely on the helper for musical decisions such as composer normalization, difficult work-title rewriting, genre inference, or performance-credit interpretation when the source files do not already expose those credits.
- Do not let the helper invent credits that are absent from the source; it may only carry forward or mechanically normalize already supported metadata.

## Tagging Rules

- Read existing tags first; do not overwrite blindly.
- Prefer in-place metadata updates over full rewrites.
- Strip accidental leading or trailing whitespace from textual fields.
- Normalize `tracknumber` to leading-zero form. Use 2 digits for tracks `01`-`99` and 3 digits for `100+`.
- Treat source values such as `1`, `2`, or `3` as invalid intermediate forms and rewrite them to `01`, `02`, or `03`.
- Keep all files in one work folder aligned on `composer`, `work`, `date`, `genre`, and performance fields unless there is a real musical reason not to.
- Treat duplicate `tracknumber` values within one work folder as a warning sign that files may be duplicated, misnamed, or misplaced from a neighboring work folder.
- If two files share duration and musical role but disagree on `work`, `tracknumber`, or ReplayGain context, verify which folder they belong to before keeping both.
- For a single-track work, it is valid for `title` to match `work` and for `movement` to be absent.
- For multi-track works, keep `work` identical across the folder and let `title` and `movement` distinguish tracks.
- Preserve source-release context in `album` when useful; do not replace it just because the folder is per-work.
- Treat a missing `album`, or an `album` that merely repeats the work title or work-folder name, as incorrect intermediate metadata that must be replaced with the best verified source release title.
- Treat a work-folder name copied into `album` as a likely placeholder unless there is good evidence that the commercial release really used that exact title.
- Treat a work title plus performance suffix copied into `album` as the same kind of placeholder unless the source release genuinely used that exact text.
- When several sibling work folders clearly come from the same source release, keep their `album` tags identical across the whole release cluster.
- If one sibling work folder from the same release cluster has a credible full release title and another sibling only has a placeholder or shortened variant, prefer the credible full release title for the cluster.
- When normalizing `album`, use the best release title you can verify, but do not let album-title cleanup override the canonical per-work folder structure.
- Use shared cover art, booklet PDFs, and other repeated source-release artifacts as evidence for clustering sibling work folders onto one `album` value when direct tag evidence is weak.
- When both a structured field and `performance` exist, keep them consistent instead of treating `performance` as free text.
- When a source page uses partial credit language such as `Dir.`, `music director`, `performed by`, or similar shorthand, map it to the narrowest correct canonical field and do not inflate it into broader personnel credits.
- For open-score or early minimalist works, keep `performance` conservative and only as specific as the source actually supports.
- Classify credit confidence in your own reasoning as `hard verified`, `reasonable inference`, or `leave unchanged`; only write metadata for the first two, and use `reasonable inference` sparingly.

## Naming Rules

- Derive the composer folder from `composer`.
- Derive the work folder from `work`, but allow an established display short form for keys and similar classical abbreviations in the folder name.
- Preserve the full canonical form in the `work` tag even when the folder uses a shorter display spelling.
- Example: `work = Partita No. 2 in C minor, BWV 826` can map to folder text `Partita No. 2, Cm, BWV 826`.
- Build the performance suffix from structured performance fields, not from `albumartist`.
- Use these performance-folder patterns:
  `conductor - orchestra`
  `conductor - ensemble`
- Separate performance components with ` - ` in folder names.
- Keep `performance` tag values semicolon-separated instead of using the folder separator.
- Rename files as `NN) title.flac`.
- After any change to `composer`, `work`, `title`, `tracknumber`, or performance fields, re-check matching folder and filename layout so tags and filesystem never drift apart.
- For Windows filesystems, use an intermediate rename for case-only path changes when needed.
- Sanitize filesystem names only. Preserve richer tag text unless it is actually invalid as metadata.
- On Windows, remember that characters valid in tags may still be invalid in filenames. Replace or simplify filesystem-only punctuation such as double quotes while keeping the fuller text in `title`, `movement`, or `work` tags.

## Casing and Text Normalization

- Do not apply pop/rock title rules blindly.
- Preserve the language and scholarly style of classical titles, especially Latin, liturgical, and catalogue text.
- Do not force English title case onto non-English work titles.
- Keep catalogue identifiers such as `BWV`, `Op.`, and work numbering intact.
- Use the established composer inversion format `Surname, Firstname` when the person is a composer.
- Preserve suffixes such as `Saint` exactly as intended in the composer field.
- Correct obvious source mistakes only when the intended classical spelling is clear.

## Genre Guidance

- Keep `genre` to exactly one period/style value from this approved list only:
  `Early Music`, `Medieval`, `Renaissance`, `Baroque`, `Classical Period`, `Romantic Period`, `Late Romantic`, `Nationalist`, `Impressionist`, `Expressionist`, `Modernist`, `Neoclassical`, `Second Viennese School`, `Serialism`, `Avant-garde`, `Minimalism`, `Postminimalism`, `Spectralism`, `Postmodernism`, `Contemporary Classical`.
- If `genre` is missing or ambiguous, infer the single best value from that approved list using the work, composer, date, and musical context before finishing.
- Do not use instrumentation or library-shelf categories such as `Keyboard`, `Orchestral`, or `Sacred` in `genre`.
- Extend this skill with additional confirmed genre values as the library grows.

## Artwork and Cleanup

- Preserve cover art unless the user asks to replace it.
- Keep one embedded front cover in every FLAC.
- Keep one `folder.*` image in the work folder.
- In this environment, PowerShell cover-art fetches using `$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing ...` are preapproved when the target URL is a known publisher, label, archive, or similar artwork source.
- Prefer embedded front cover art at about `1200x1200` when a good source image is available.
- Allow the standalone `folder.*` image to be higher resolution than the embedded cover when a better local source exists.
- If a useful front cover exists under another filename, rename it to `folder.*` instead of creating a duplicate.
- If a source-release folder has one shared cover file and you split that release into multiple work folders, copy that same cover into each derived work folder as `folder.*` unless there is better work-specific art.
- If no standalone front cover exists but embedded front cover art is present in the FLAC files, extract that embedded front cover into `folder.*`.
- If embedded art exists but is obviously low quality, replace it when you can find a clearly better cover.
- If the local `folder.*` image is obviously low resolution, fuzzy, heavily compressed, or smaller than the preferred embedded target, look for a better source before finishing.
- If neither embedded art nor standalone art exists, first look for a clearly matching sibling work folder from the same source release or performer set before searching externally.
- If local artwork is missing or weak, search the internet for the best clearly matching cover you can find and prefer the highest-quality trustworthy source available.
- When searching externally, prefer exact release matches over generic composer art or near-miss reissues with different cover design.
- After downloading or choosing better art, keep the higher-resolution file as `folder.*` and embed an appropriately sized front cover into every FLAC.
- Remove junk files such as `Thumbs.db`, `.DS_Store`, and obvious temporary leftovers.
- Treat `folder.*`, useful booklet PDFs, and useful TXT notes as expected non-FLAC files rather than cleanup failures.
- Remove non-FLAC files unless they are useful artwork, PDF booklets, or useful TXT notes.
- Treat missing artwork as a metadata problem that should normally be fixed.

## Audio and Integrity Rules

- If sample rate exceeds 44.1 kHz or bit depth exceeds 16-bit, recode to 44.1 kHz / 16-bit with `sox`.
- If `sox` reports possible clipping, lower the level before encoding.
- Always calculate ReplayGain for the complete work folder, not track-by-track in isolation.
- On Windows, if `metaflac --add-replay-gain` fails through shell-expanded arguments such as `*.flac` or a PowerShell array even though the files themselves are readable and writable, retry by invoking `metaflac` with an explicit argv list from Python `subprocess` or another launcher that passes each FLAC path literally.
- If a FLAC contains accidental ID3 tags, preserve the Vorbis-derived data and remove the ID3 tags.
- Treat a trailing `ID3v1` tag on a FLAC as mechanically removable corruption.
- If `flac -t` still fails after stripping trailing `ID3v1`, treat the file as source-corrupt audio that needs manual investigation or source replacement.
- Reopen edited files after writing and verify that the final tags and pictures are readable.
- Test every FLAC with `flac -t` or `flac.exe -t`; any failure is blocking.

## Final Verification

- This is the last step.
- Treat the following items as acceptance criteria.
- Do not finish the task until every acceptance criterion below has been checked explicitly and any failures have been fixed and rechecked.
- If any acceptance criterion fails, fix the issue and rerun the full task from the start of this workflow before finishing.
- Confirm the top-level composer folder matches `composer`.
- Confirm the work folder matches `work-folder-name (performance-folder-name)`.
- Confirm every FLAC filename matches `NN) title.flac`.
- Confirm only the allowed Vorbis fields remain.
- Confirm `artist` is empty.
- Confirm `albumartist` is empty.
- Confirm `performer` is empty.
- Confirm `discnumber`, `totaldiscs`, and `totaltracks` are empty.
- Confirm track title is the title of the piece or the part of a piece.
- Confirm `album` is the album title.
- Confirm `date` is the year of release.
- Confirm `genre` is one of the approved periods/styles.
- Confirm `work` has a correct value.
- Confirm `movement`, `conductor`, `orchestra`, and `performance` have a value if appropriate.
- Confirm all other non-allowed fields are empty except `replaygain_*`, which are allowed and expected when present.
- Confirm every `tracknumber` is zero-padded to match the filename numbering scheme.
- Confirm there are no duplicate track numbers left in a work folder unless the music genuinely requires them.
- Confirm the number of FLAC files in the folder matches the expected movement count for that work.
- Confirm `album` may differ from the work-folder name when it represents the source release.
- Confirm `album` is not just the work title, work-folder name, or work-plus-performance suffix unless that exact text is verified as the real release title.
- Confirm `performance` agrees with `conductor`, `orchestra`, and `ensemble`.
- Confirm every populated credit field is supported by either the file tags or a trustworthy source reference.
- Confirm no `performance` value was inferred from folder suffixes alone.
- Confirm every FLAC has the expected embedded front cover and the folder has one `folder.*`.
- Confirm the embedded front cover is reasonably sized, preferably around `1200x1200`, unless no adequate source exists.
- Confirm the standalone `folder.*` is at least as good as the embedded cover and may be higher resolution.
- Treat standalone `folder.*` artwork as expected output, not as leftover clutter.
- Confirm every audio file is a FLAC stream, and confirm its sample rate is 44.1 kHz and its bit depth is 16-bit before finishing.
- Confirm ReplayGain exists for the processed work folder.
- Confirm ReplayGain is present for every FLAC in the processed folder, not merely some tracks.
- When the work belongs to a larger split source release, confirm sibling work folders that share that release also share the same normalized `album` value.
- Report the number of FLAC files tested and any integrity failures.
- If source confidence was mixed, report which credits were hard verified versus which were left unchanged.

## Refinement Rule

- Update this skill with new composer-name conventions, genre values, work-folder abbreviations, release-title mappings, split heuristics, and edge cases as they are discovered in the classical library.



