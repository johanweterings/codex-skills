---
name: flac-folder-maintenance
description: Direct FLAC release-folder cleanup, Vorbis comment inspection, metadata editing, artwork normalization, filename/layout maintenance, and integrity verification using Python/Mutagen plus flac.exe or metaflac when useful. Use when Codex needs to read, understand, modify, clean, rename, validate, or verify FLAC files, with Vorbis comments as the source of truth and any ID3 tags removed.
---

# FLAC Folder Maintenance

Use this skill for manual tag and folder work on FLAC releases.

## Scope

- Read and write FLAC Vorbis comments directly with Python 3.12 and `mutagen`.
- Prefer `mutagen.flac.FLAC` for comments and embedded pictures.
- You may use `metaflac` for FLAC metadata inspection, tag editing, picture import/export, and ReplayGain operations when it is available and more direct than Python.
- Treat all files in a folder as one release unless the user explicitly says otherwise.
- Assume read/write access to the target folder and its subfolders when the skill is applied.
- You may create, edit, and delete temporary helper files in the target folder while applying or verifying this skill; remove those temporary files before finishing unless the user asks to keep them.
- Within the target workspace or release folder, you do not need extra user confirmation for normal create, update, rename, move, or delete operations that are part of the cleanup workflow.
- Use `ffprobe` or `ffmpeg` only when audio or container inspection is needed.
- Keep the workflow manual-only until the user asks for automation.

## Workflow

1. Inspect the file type and current tag versions before editing.
2. Read existing tags first; do not overwrite blindly.
3. Interpret FLAC metadata as Vorbis comments plus pictures.
4. Read existing comments first, then remove any Vorbis comment field outside the allowed metadata set.
5. Calculate and write ReplayGain for the full folder or release as one treatment.
6. After writing, reopen the file and verify the result.
7. Synchronize filenames and folder layout from the final verified tags.
8. Restore normal inherited filesystem access on rewritten or replaced files so standard user applications can reopen them.
9. Run cleanup checks for leftover temporary/system files.
10. Test every FLAC file with lac -t or lac.exe -t before finishing; treat any non-zero exit code as a blocking integrity problem.

## Editing rules

- Prefer in-place tag updates over full rewrites.
- Change only the frames, comments, or values requested, except always enforce the allowed Vorbis comment field set during cleanup.
- Always calculate and write `replaygain_*` fields for every processed release, unless the user explicitly asks to remove them.
- Preserve cover art unless the user asks to replace it.
- If cover art exists, keep it embedded and also save one `folder.*` image in the release folder.
- It is fine for the saved `folder.*` image to be larger than 1200x1200; do not downscale a larger original cover just to match the embedded-art target.
- Strip accidental trailing whitespace from textual fields when editing them.
- If any ID3 tags are present on a FLAC file, remove them only after preserving the Vorbis-derived data.
- Keep `artist` as the track artist on every file.
- Leave `albumartist` empty on non-compilations.
- For split, collaboration, or remix releases credited to a fixed release artist but with varying track artists, keep `albumartist` as the credited release artist instead of changing it to `Compilation`.
- Set `albumartist = Compilation` only when the release is a real compilation, usually because track artists differ across the folder.
- Do not treat remixes, featuring credits, or guest artists in the title as a compilation by themselves.

## Naming rules

- Normalize titles and folder names by removing source or container suffixes such as `-flac`, `-wav`, `-promo`, and similar packaging markers when they are not part of the actual release title.
- Remove year markers from folder and title names when they are release metadata in parentheses, unless the year is intentionally part of the release title.
- Remove catalogue-number prefixes from album titles, folder names, and filenames when they appear as metadata rather than part of the title, for example `(AF068) Radical Meditation EP` -> `Radical Meditation EP`.
- Replace `[` and `]` with `(` and `)`.
- Convert `(inhoud1)[inhoud2]` to `(inhoud1 - inhoud2)`.
- Replace `&` with `and` in titles, folder names, and other release text unless the string is clearly in another language.
- Apply `&` to `and` normalization consistently across Vorbis tags, folder names, and filenames; for example `Afrika Bambaataa & Soulsonic Force With Shango` -> `Afrika Bambaataa and Soulsonic Force With Shango`.
- Expand common English abbreviations in release text when they are just shortened display forms rather than intentional styling, across tags, folder names, and filenames; for example `Vol.` -> `Volume`, `Feat.` -> `Featuring`, and `feat.` -> `featuring`.
- Apply English title capitalization: lowercase function words such as articles, coordinating conjunctions, and short prepositions (`a`, `an`, `and`, `as`, `at`, `but`, `by`, `for`, `from`, `in`, `of`, `on`, `or`, `the`, `to`, `with`) unless they are the first or last word of the title or subtitle segment.
- Expand track-part abbreviations in titles and filenames, so `Pt. 1` becomes `part 1` and similar `Pt.` markers are normalized to `part`.
- When a track title uses a comma-separated part suffix, rewrite it into parentheses, for example `The Beings, Pt. 6` -> `The Beings (part 6)`.
- When expanding `Vol.` in titles, folder names, and filenames, normalize it to `Volume N` with no preceding comma, for example `Selected Ambient Works, Vol. 2` -> `Selected Ambient Works Volume 2`.
- Preserve normal apostrophe casing when title-casing, for example `Valentine's`, `Didn't`, `Couldn't`, and `Shouldn't`, and never produce forms such as `Valentine'S` or `Didn'T`.
- Invert personal names to `Surname, Firstname` when that format is appropriate, but leave non-person names unchanged.
- Known personal-name inversion: `Robin Guthrie` -> `Guthrie, Robin` in tags, folder names, and filenames.
- Keep band or project names unchanged when they are not personal names.
- Preserve names like `Fad Gadget` and `Firm, the` as-is when that is the intended form.
- Drop `Records` from label names when it is part of the label's display name, for example `Warner Bros. Records` -> `Warner Bros.`.

## Folder and file layout

- Rename the top-level folder to the artist name for non-compilations.
- Put the album in a subfolder under that artist folder.
- Rename the top-level folder to `Various Artists` for compilations.
- Put the compilation album in a subfolder under the `Various Artists` folder.
- Rename files as `track) title` for non-compilations.
- Rename files as `track) artist - title` for compilations.
- After any `title`, `artist`, `album`, `albumartist`, or `tracknumber` change, re-check the corresponding filename and folder name; tags and filesystem layout must not drift apart.
- For compilations, keep the track artist in filenames even when only the title changed; never shorten `track) artist - title` to `track) title`.
- For Windows filesystems, handle case-only renames with a temporary intermediate filename when needed.
- Use `folder.*` as the filename for the cover image in the album folder.
- If a cover image already exists under another name, rename it to `folder.*` instead of creating a duplicate.
- Save a back-cover image as `back.*` when one is present and useful.
- Keep one release per artist folder.
- Treat album subfolders as the release unit, not the top-level artist or compilation folder.
- When a tag value contains path separators or other filesystem-invalid characters, preserve the tag value but use a safe folder or filename spelling, for example `Ai/mB` as metadata and `Ai-mB` as a folder name.
- Sanitize filesystem names only, not tag values: replace or avoid Windows-invalid characters (`<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*`) and collapse accidental repeated spaces in paths.

## Metadata normalization

- Normalize `tracknumber` to always use leading zeros. Use 2 digits for tracks 1-99 and 3 digits for 100+.
- Treat `date` as the original release year, not the remaster year.
- If a later release or remaster is explicitly part of the title, keep it in the title.
- Set `genre` to exactly one value; do not use combined forms such as `Electro/Disco`.
- `genre` must not be empty. If `genre` is missing or blank, browse Discogs for the release and set the single best value from the release data before finishing.
- Maintain a growing allowed-genre list in this skill as values are confirmed. Current allowed values include `Ambient`, `Drum and Bass`, `Electro`, `Electronic`, `Hip-Hop`, `IDM`, and `Techno`.
- When a source gives a combined genre, choose the single best value from the allowed list; for example `Electro/Disco` -> `Electro`.
- Remove `(bonus track)` from titles and filenames; preserve the track itself, only remove the bonus marker text.
- Lowercase version descriptors inside titles and filenames, including examples such as `(darren nye remix)`, `(instrumental)`, `(dub version)`, `(vocal)`, and similar mix/version/remix descriptors.
- Treat the full parenthesized phrase as a lowercase version descriptor when it ends in `mix`, `remix`, `version`, `edit`, `take`, `dub`, `instrumental`, `vocal`, or similar version words, even when the phrase is a long descriptive subtitle.
- Apply version-descriptor casing globally after title capitalization; do not let title-case logic re-capitalize words inside these descriptor parentheses.
- Apply this rule to examples such as `Mi-Loony-Um! (A Floating Butterfly Stings Like A Bee Mix)` -> `Mi-Loony-Um! (a floating butterfly stings like a bee mix)`, `Solstice (Warwick Bassmonkey Mix)` -> `Solstice (warwick bassmonkey mix)`, `Gamma Goblins (It's Turtles All The Way Down Mix)` -> `Gamma Goblins (it's turtles all the way down mix)`, `Spiritual Antiseptic (Minty Fresh Confidence Mix)` -> `Spiritual Antiseptic (minty fresh confidence mix)`, `LSD (World Sheet Of Closed String Mix)` -> `LSD (world sheet of closed string mix)`, and `Angelic Particles (Buckminster Fullerine Mix)` -> `Angelic Particles (buckminster fullerine mix)`.
- Always calculate ReplayGain as one treatment per folder or release, not per track independently.
- Keep only these Vorbis comment fields with values: `replaygain_*`, `title`, `artist`, `album`, `date` (year), `tracknumber` (track), `genre`, and, when justified by release structure, `albumartist`.
- Treat `date` as the year field; store only the release year unless the user explicitly asks for a fuller date.
- Remove or empty `comment`; the comment field must not contain a value.
- Remove custom/nonessential fields such as `organization`, `url`, `label`, `cat#`, and similar source/store metadata.

## Cleanup rules

- Remove non-image, non-PDF, and non-TXT files from the target folder tree.
- Remove `Info.txt` and `Folder.auCDtect.txt` when present.
- Remove unneeded system/cache files such as `Thumbs.db`, `.DS_Store`, desktop metadata files, and temporary downloaded candidate files after verification.
- Remove album subfolders such as `Artwork` after checking them for useful images first.
- If an album subfolder contains a usable front cover, rename it to `folder.*` in the album folder.
- If an album subfolder contains a usable back cover, rename it to `back.*` in the album folder.
- Keep other useful text notes such as `tracklist.txt`.
- Treat missing artwork as a metadata problem; artwork is expected to be present.
- When checking cover art, inspect the full-size source image, especially Bandcamp image URLs opened from the cover, rather than assuming the page thumbnail or saved folder art is the best available copy. Prefer the best available front cover for the saved `folder.*` file, even when it is larger than 1200x1200.
- For embedded front cover art inside the FLAC files, prefer something around 1200x1200 rather than embedding an unnecessarily large original image.
- Search for a better front cover even when an existing embedded or folder cover is present but smaller than 1200x1200.
- Prefer Bandcamp first when searching for cover art. If no Bandcamp cover can be found, use the best available resolution from another reliable source.
- You may download cover art from any source needed to find the best available front cover, not only Bandcamp or MusicBrainz/Cover Art Archive.
- You do not need extra user confirmation before downloading cover art or other release images needed to complete the artwork workflow, as long as the environment permits the download.
- Replace the local `folder.*` and embedded front cover when a downloaded cover is a better match for the release and has a better resolution.

## Audio quality rules

- If sample rate exceeds 44.1 kHz or bit depth exceeds 16-bit, recode to 44.1 kHz / 16-bit with `sox`.
- If `sox` reports possible clipping, lower the level before encoding.
- Ensure all FLAC files are encoded at level 8; re-encode if needed.

## Final verification

- Reopen all edited FLAC files and verify the final Vorbis comments, embedded pictures, filenames, and normal user-readable filesystem access.
- Confirm there are no mixed-case version descriptors in parenthesized version phrases that should be lowercase.
- Confirm non-compilation filenames match `track) title` from final tags.
- Confirm compilation filenames retain `track) artist - title` from final tags.
- Confirm only allowed Vorbis fields remain, textual fields have no accidental leading/trailing whitespace, and each FLAC has the expected embedded front cover.
- Confirm rewritten or replaced FLAC files inherit normal access from the release folder; on Windows, reset ACLs if needed so applications such as foobar2000 and Mp3tag do not hit Access denied.
- Run lac -t or lac.exe -t on every FLAC in the processed release or batch and report the count tested plus any failures.

## Refinement rule

- Update this skill with concrete frame mappings, normalization rules, and edge cases as they are discovered.


