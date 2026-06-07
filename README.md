These two skill i made for codex, the AI from OpenAI. On my windows machine i put them in C:\Users\[user]\.codex\skills. 

## Shared Dependencies

Both skills rely on:

- `Python 3.12`
- `mutagen`
- `metaflac`
- `flac` or `flac.exe` for integrity testing with `-t`
- `sox` when audio must be recoded to 44.1 kHz / 16-bit
- Windows PowerShell for the normal workflow in this environment

## `flac-folder-maintenance`

In addition to the shared dependencies, this skill may also use:

- `ffprobe` or `ffmpeg` for audio/container inspection when needed
- Internet access for fetching cover art when local artwork is missing or weak
- Existing FLAC tags and embedded artwork, since the workflow is read-first
- Optional temporary helper files created during cleanup and verification

## `classical-flac-folder-maintenance`

In addition to the shared dependencies, this skill also expects:

- `py -3.12`, or a direct Python 3.12 interpreter path if the launcher is unavailable
- `scripts\classical_folder_helper.py` from the skill package
- Internet access for cover art and release-title verification when local data is incomplete
- Existing FLAC tags, sibling work folders, and release-level artwork as source context

## Key Differences

- `flac-folder-maintenance` allows `artist` and `albumartist` handling for non-classical release structures.
- `classical-flac-folder-maintenance` depends on the helper script and a classical composer/work/performance folder model.
- `flac-folder-maintenance` may use `ffprobe`/`ffmpeg`; the classical skill does not list them as part of its normal workflow.
- `classical-flac-folder-maintenance` is more dependent on artwork reuse across sibling work folders and on consistent release clustering.

## Notes

- Neither skill declares a formal package manifest.
- The dependency lists above are operational, based on the instructions in each `SKILL.md`.
