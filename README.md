These two skill i made for codex, the AI from OpenAI. On my windows machine i put them in C:\Users\[user]\.codex\skills. It depens on a few external tools:

  - Python 3.12
  - mutagen for FLAC/Vorbis comment and picture editing
  - metaflac for metadata inspection, picture import/export, and ReplayGain
  - flac / flac.exe for integrity testing with -t
  - sox if files need to be recoded to 44.1 kHz / 16-bit
  - scripts\classical_folder_helper.py from the same skill package for mechanical cleanup
  - PowerShell on Windows for running the workflow and file operations

  Conditional / workflow dependencies:

  - Internet access for fetching replacement cover art when local art is missing or weak
  - Existing FLAC tags and embedded artwork, since the skill is read-first and preserves source context
  - A Windows Python launcher or a direct interpreter path if py -3.12 is unavailable
