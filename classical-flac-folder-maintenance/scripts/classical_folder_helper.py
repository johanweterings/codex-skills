#!/usr/bin/env python3
from __future__ import annotations

import argparse
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from mutagen.flac import FLAC, Picture


ALLOWED_FIELDS = {
    "album",
    "albumartist",
    "composer",
    "conductor",
    "date",
    "ensemble",
    "genre",
    "movement",
    "orchestra",
    "performance",
    "performer",
    "replaygain_album_gain",
    "replaygain_album_peak",
    "replaygain_track_gain",
    "replaygain_track_peak",
    "title",
    "tracknumber",
    "work",
}
JUNK_FILENAMES = {"thumbs.db", ".ds_store"}
UNWANTED_EXTENSIONS = {".wav", ".url", ".mhtml", ".html"}
CURATED_CONTAINER_MARKERS = (
    "retrospective",
    "anthology",
    "box set",
    "box",
    "collection",
    "selections",
    "highlights",
    "overview",
    "sampler",
)
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ENSEMBLE_KEYWORDS = (
    "orchestra",
    "philharmonic",
    "philharmonia",
    "philharmoniker",
    "symphony",
    "choir",
    "chorus",
    "capella",
    "consort",
    "ensemble",
    "players",
    "fretwork",
    "monks",
    "collegium",
)
INVALID_FS_CHARS = '<>:"/\\|?*'


@dataclass
class Change:
    kind: str
    path: Path
    detail: str


def sanitize_fs_name(value: str) -> str:
    translated = value.replace(":", " - ")
    translated = translated.translate(str.maketrans({char: "-" for char in INVALID_FS_CHARS if char != ":"}))
    translated = re.sub(r"\s+", " ", translated).strip().rstrip(".")
    return translated


def looks_like_composer_dir(name: str) -> bool:
    if name == "Anonymous":
        return True
    if "(" in name or ")" in name:
        return False
    return bool(re.match(r"^[^,]+,\s*[^,]+$", name))


def is_bucket_dir(path: Path) -> bool:
    return path.is_dir() and len(path.name) == 1 and path.name.isalpha()


def composer_dirs(root: Path) -> list[Path]:
    results: list[Path] = []
    if looks_like_composer_dir(root.name):
        results.append(root)
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if looks_like_composer_dir(child.name):
            results.append(child)
            continue
        if is_bucket_dir(child):
            for grandchild in sorted(child.iterdir()):
                if grandchild.is_dir() and looks_like_composer_dir(grandchild.name):
                    results.append(grandchild)
    return results


def iter_flacs(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.flac") if p.is_file())


def normalize_tracknumber(value: str) -> str | None:
    if not value or not value.isdigit():
        return None
    number = int(value)
    width = 2 if number < 100 else 3
    normalized = f"{number:0{width}d}"
    if normalized == value:
        return None
    return normalized


def picture_extension(mime: str | None) -> str:
    if not mime:
        return ".img"
    return MIME_TO_EXT.get(mime.lower()) or mimetypes.guess_extension(mime) or ".img"


def mime_for_extension(path: Path) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/jpeg")


def is_ensemble_name(value: str) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in ENSEMBLE_KEYWORDS)


def split_folder_suffix(folder_name: str) -> tuple[str, str | None]:
    if folder_name.endswith(")") and " (" in folder_name:
        work, suffix = folder_name.rsplit(" (", 1)
        return work, suffix[:-1]
    return folder_name, None


def canonical_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def same_name(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    left_tokens = sorted(re.findall(r"[a-z0-9]+", left.lower()))
    right_tokens = sorted(re.findall(r"[a-z0-9]+", right.lower()))
    return left_tokens == right_tokens


def similar_work_prefix(prefix: str, work: str) -> bool:
    left = canonical_text(prefix)
    right = canonical_text(work)
    if len(left) < 8 or len(right) < 8:
        return False
    return left in right or right in left


def parse_components(value: str) -> list[str]:
    return [part.strip() for part in value.split(" - ") if part.strip()]


def first_value(audio: FLAC, key: str) -> str | None:
    values = audio.get(key)
    if not values:
        return None
    return values[0].strip() or None


def filename_title(path: Path) -> str:
    name = path.stem
    match = re.match(r"^\d{1,3}[.)]\s*(.+)$", name)
    if match:
        return match.group(1).strip()
    return name.strip()


def looks_like_movement_only(title: str) -> bool:
    return bool(re.match(r"^(?:[IVX]+\.|[0-9]+\.)\s", title))


def choose_display_performance(folder_suffix: str | None, audio: FLAC, composer: str | None = None) -> str | None:
    if folder_suffix:
        return folder_suffix
    performer = first_value(audio, "performer")
    conductor = first_value(audio, "conductor")
    artist = first_value(audio, "artist")
    parts: list[str] = []
    if performer:
        parts.extend(parse_components(performer) if " - " in performer else [performer])
    if conductor and conductor not in parts:
        parts.append(conductor)
    if artist and artist not in parts and not looks_like_composer_dir(artist) and not same_name(artist, composer or first_value(audio, "composer")):
        parts.append(artist)
    if not parts:
        return None
    return " - ".join(parts)


def choose_single_track_work(path: Path, audio: FLAC) -> str:
    contentgroup = first_value(audio, "contentgroup")
    if contentgroup:
        return contentgroup
    title = first_value(audio, "title") or filename_title(path)
    file_title = filename_title(path)
    if looks_like_movement_only(title) and file_title != title:
        title = file_title
    match = re.match(r"^(.*?)(?:\s+[IVX]+\.\s+.+|\s+[0-9]+\.\s+.+)$", title)
    if match and len(match.group(1)) > 8:
        return match.group(1).strip()
    return re.sub(r"\s+\([^)]*\)$", "", title).strip()


def shared_contentgroup(flacs: list[Path]) -> str | None:
    values = {first_value(FLAC(path), "contentgroup") for path in flacs}
    values.discard(None)
    if len(values) == 1:
        return next(iter(values))
    return None


def shared_tag_value(flacs: list[Path], key: str) -> str | None:
    values = {first_value(FLAC(path), key) for path in flacs}
    values.discard(None)
    if len(values) == 1:
        return next(iter(values))
    return None


def looks_like_curated_compilation(folder: Path, flacs: list[Path]) -> bool:
    haystacks = [folder.name.lower()]
    for field in ("album", "contentgroup"):
        value = shared_tag_value(flacs, field)
        if value:
            haystacks.append(value.lower())
    return any(marker in haystack for haystack in haystacks for marker in CURATED_CONTAINER_MARKERS)


def should_split_album_folder(folder: Path, flacs: list[Path]) -> bool:
    if len(flacs) <= 1:
        return False
    if looks_like_curated_compilation(folder, flacs):
        return False
    if shared_contentgroup(flacs):
        return False
    has_tracknumbers = False
    has_numbered_filenames = False
    for path in flacs:
        audio = FLAC(path)
        if first_value(audio, "tracknumber"):
            has_tracknumbers = True
        if re.match(r"^\d{1,3}[.)]\s+", path.name):
            has_numbered_filenames = True
    inferred_works = {choose_single_track_work(path, FLAC(path)) for path in flacs}
    duplicate_tracknumbers = len({(FLAC(path).get("tracknumber") or [""])[0] for path in flacs if (FLAC(path).get("tracknumber") or [""])[0]}) < len(
        [(FLAC(path).get("tracknumber") or [""])[0] for path in flacs if (FLAC(path).get("tracknumber") or [""])[0]]
    )
    return (not has_tracknumbers and not has_numbered_filenames) or (duplicate_tracknumbers and len(inferred_works) > 1)


def unique_dir(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.name} [{counter}]")
        if not candidate.exists():
            return candidate
        counter += 1


def infer_group_field(name: str) -> tuple[str, str]:
    if is_ensemble_name(name):
        if any(token in name.lower() for token in ("orchestra", "philharmonic", "philharmonia", "philharmoniker", "symphony")):
            return "orchestra", name
        return "ensemble", name
    return "performer", name


def infer_performance_tags(audio: FLAC, folder_suffix: str | None, composer: str) -> dict[str, str]:
    result: dict[str, str] = {}
    display = choose_display_performance(folder_suffix, audio, composer)
    if not display:
        return result
    result["performance"] = "; ".join(parse_components(display))
    components = parse_components(display)
    existing_performer = first_value(audio, "performer")
    existing_conductor = first_value(audio, "conductor")
    existing_orchestra = first_value(audio, "orchestra")
    existing_ensemble = first_value(audio, "ensemble")
    existing_artist = first_value(audio, "artist")
    if len(components) == 1:
        if existing_orchestra and same_name(existing_orchestra, components[0]):
            field, value = "orchestra", existing_orchestra
        elif existing_ensemble and same_name(existing_ensemble, components[0]):
            field, value = "ensemble", existing_ensemble
        elif existing_performer and same_name(existing_performer, components[0]):
            field, value = "performer", existing_performer
        else:
            field, value = infer_group_field(components[0])
        result[field] = value
        return result
    if existing_conductor and existing_conductor in components:
        result["conductor"] = existing_conductor
    last = components[-1]
    if is_ensemble_name(last):
        field, value = infer_group_field(last)
        result[field] = value
        lead_components = components[:-1]
        if "conductor" not in result and len(lead_components) == 1:
            result["conductor"] = lead_components[0]
            lead_components = []
        performers: list[str] = []
        parsed_existing_performer = parse_components(existing_performer) if existing_performer else []
        if parsed_existing_performer and any(is_ensemble_name(part) for part in parsed_existing_performer):
            parsed_existing_performer = []
        if parsed_existing_performer and parsed_existing_performer != components:
            performers = parsed_existing_performer
        elif lead_components and len(components) == 3 and first_value(audio, "title") and "concerto" in first_value(audio, "title").lower():
            performers = [lead_components[0]]
            if "conductor" not in result and len(lead_components) > 1:
                result["conductor"] = lead_components[1]
        elif lead_components and "conductor" in result:
            performers = [part for part in lead_components if part != result["conductor"]]
        elif lead_components and len(components) == 4:
            if "conductor" not in result:
                result["conductor"] = lead_components[-1]
            performers = lead_components[:-1]
        elif lead_components and "conductor" not in result:
            field, value = infer_group_field(lead_components[0])
            result[field] = value
            performers = lead_components[1:]
        if performers:
            result["performer"] = "; ".join(performers)
        elif existing_artist and existing_artist != composer and not is_ensemble_name(existing_artist):
            result["performer"] = existing_artist
        return result
    if existing_performer and existing_performer != display:
        result["performer"] = existing_performer
    else:
        result["performer"] = "; ".join(components)
    if existing_conductor and existing_conductor not in result.get("performer", ""):
        result["conductor"] = existing_conductor
    return result


def retitle(track_title: str, work_tag: str) -> tuple[str, str | None]:
    title = track_title.strip()
    for separator in (": ", " - "):
        prefix, found, rest = title.partition(separator)
        if found and similar_work_prefix(prefix, work_tag):
            cleaned = rest.strip()
            return cleaned, cleaned
    trimmed = re.sub(r"\s+\([^)]*\)$", "", title).strip()
    if trimmed != title and similar_work_prefix(trimmed, work_tag):
        return work_tag, None
    return title, None


def target_filename(tracknumber: str, title: str) -> str:
    return f"{tracknumber}) {sanitize_fs_name(title)}.flac"


def trailing_id3v1_present(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            handle.seek(-128, 2)
            return handle.read(3) == b"TAG"
    except OSError:
        return False


def strip_trailing_id3v1(path: Path, dry_run: bool) -> list[Change]:
    if not trailing_id3v1_present(path):
        return []
    if not dry_run:
        data = path.read_bytes()
        path.write_bytes(data[:-128])
    return [Change("strip_id3v1", path, "remove trailing ID3v1 tag from FLAC")]


def rename_path(source: Path, target: Path, dry_run: bool, kind: str, detail: str) -> list[Change]:
    if source == target:
        return []
    changes = [Change(kind, target, detail)]
    if dry_run:
        return changes
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        source.rename(target)
    return changes


def find_sibling_art_source(folder: Path) -> Path | None:
    flacs = sorted(folder.glob("*.flac"))
    if not flacs:
        return None
    audio = FLAC(flacs[0])
    performer = first_value(audio, "performer")
    ensemble = first_value(audio, "ensemble")
    orchestra = first_value(audio, "orchestra")
    conductor = first_value(audio, "conductor")
    date = first_value(audio, "date")
    best: tuple[int, Path] | None = None
    for sibling in sorted(p for p in folder.parent.iterdir() if p.is_dir() and p != folder):
        art = next((p for p in sibling.iterdir() if p.is_file() and p.stem.lower() == "folder"), None)
        sibling_flacs = sorted(sibling.glob("*.flac"))
        if not art or not sibling_flacs:
            continue
        other = FLAC(sibling_flacs[0])
        score = 0
        if performer and first_value(other, "performer") == performer:
            score += 4
        if ensemble and first_value(other, "ensemble") == ensemble:
            score += 4
        if orchestra and first_value(other, "orchestra") == orchestra:
            score += 4
        if conductor and first_value(other, "conductor") == conductor:
            score += 3
        if date and first_value(other, "date") == date:
            score += 1
        if score > 0 and (best is None or score > best[0]):
            best = (score, art)
    return best[1] if best else None


def build_folder_performance(audio: FLAC) -> str | None:
    components: list[str] = []
    performer = first_value(audio, "performer")
    conductor = first_value(audio, "conductor")
    orchestra = first_value(audio, "orchestra")
    ensemble = first_value(audio, "ensemble")
    if performer:
        components.extend(part.strip() for part in performer.split(";") if part.strip())
    if conductor:
        components.append(conductor)
    if orchestra:
        components.append(orchestra)
    elif ensemble:
        components.append(ensemble)
    if components:
        return " - ".join(components)
    performance = first_value(audio, "performance")
    if performance:
        return " - ".join(part.strip() for part in performance.split(";") if part.strip())
    return None


def normalize_folder_name(folder: Path, dry_run: bool) -> list[Change]:
    flacs = sorted(folder.glob("*.flac"))
    if not flacs:
        return []
    audio = FLAC(flacs[0])
    work = first_value(audio, "work")
    if not work:
        return []
    folder_name = sanitize_fs_name(work)
    performance = build_folder_performance(audio)
    if performance:
        folder_name = f"{folder_name} ({sanitize_fs_name(performance)})"
    target = folder.parent / folder_name
    if target == folder:
        return []
    current_work, current_suffix = split_folder_suffix(folder.name)
    if current_suffix:
        return []
    if sanitize_fs_name(current_work) == sanitize_fs_name(work) and not performance:
        return []
    target = unique_dir(target)
    return rename_path(folder, target, dry_run, "rename_folder", f"{folder.name} -> {target.name}")


def move_direct_flacs(composer_dir: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for path in sorted(composer_dir.glob("*.flac")):
        audio = FLAC(path)
        work = choose_single_track_work(path, audio)
        performance = choose_display_performance(None, audio, composer_dir.name)
        folder_name = sanitize_fs_name(work)
        if performance:
            folder_name = f"{folder_name} ({sanitize_fs_name(performance)})"
        target_dir = unique_dir(composer_dir / folder_name)
        target_file = target_dir / path.name
        changes.extend(rename_path(path, target_file, dry_run, "move_flac", f"create work folder for {work}"))
    return changes


def split_album_folder(composer_dir: Path, folder: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    _, folder_suffix = split_folder_suffix(folder.name)
    for path in sorted(folder.glob("*.flac")):
        audio = FLAC(path)
        work = choose_single_track_work(path, audio)
        performance = choose_display_performance(folder_suffix, audio, composer_dir.name)
        folder_name = sanitize_fs_name(work)
        if performance:
            folder_name = f"{folder_name} ({sanitize_fs_name(performance)})"
        target_dir = unique_dir(composer_dir / folder_name)
        target_file = target_dir / path.name
        changes.extend(rename_path(path, target_file, dry_run, "split_work", f"split source album folder {folder.name}"))
    if dry_run:
        if not list(folder.glob("*.flac")):
            changes.append(Change("remove_empty_dir", folder, "remove emptied source album folder"))
        return changes
    if folder.exists() and not any(folder.iterdir()):
        folder.rmdir()
        changes.append(Change("remove_empty_dir", folder, "remove emptied source album folder"))
    return changes


def restructure_batch(root: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for composer_dir in composer_dirs(root):
        changes.extend(move_direct_flacs(composer_dir, dry_run))
    if not dry_run:
        for composer_dir in composer_dirs(root):
            for folder in sorted(p for p in composer_dir.iterdir() if p.is_dir()):
                flacs = sorted(folder.glob("*.flac"))
                if flacs and should_split_album_folder(folder, flacs):
                    changes.extend(split_album_folder(composer_dir, folder, dry_run))
    else:
        for composer_dir in composer_dirs(root):
            for folder in sorted(p for p in composer_dir.iterdir() if p.is_dir()):
                flacs = sorted(folder.glob("*.flac"))
                if flacs and should_split_album_folder(folder, flacs):
                    changes.extend(split_album_folder(composer_dir, folder, dry_run))
    return changes


def infer_tracknumber(path: Path, audio: FLAC, index: int, total: int) -> str:
    current = first_value(audio, "tracknumber")
    if current:
        return normalize_tracknumber(current) or current
    match = re.match(r"^(\d{1,3})[.)]\s+", path.name)
    if match:
        return normalize_tracknumber(match.group(1)) or match.group(1)
    number = 1 if total == 1 else index
    width = 2 if number < 100 else 3
    return f"{number:0{width}d}"


def apply_tag_normalization(folder: Path, flacs: list[Path], dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    composer = folder.parent.name
    work_display, folder_suffix = split_folder_suffix(folder.name)
    contentgroup = shared_contentgroup(flacs)
    existing_work = shared_tag_value(flacs, "work")
    work_tag = existing_work or contentgroup or work_display
    for index, path in enumerate(sorted(flacs), start=1):
        audio = FLAC(path)
        current_title = first_value(audio, "title") or filename_title(path)
        title, movement = retitle(current_title, work_tag)
        if len(flacs) == 1:
            title = work_tag
            movement = None
        tags = {
            "composer": composer,
            "work": work_tag,
            "title": title,
            "tracknumber": infer_tracknumber(path, audio, index, len(flacs)),
        }
        for field in ("album", "date", "genre", "albumartist"):
            value = first_value(audio, field)
            if value:
                tags[field] = value
        tags.update(infer_performance_tags(audio, folder_suffix, composer))
        if movement:
            tags["movement"] = movement
        elif "movement" in audio:
            del audio["movement"]
        changed_fields: list[str] = []
        for field, value in tags.items():
            current = first_value(audio, field)
            if current != value:
                audio[field] = [value]
                changed_fields.append(field)
        for field in list(audio.keys()):
            if field not in ALLOWED_FIELDS:
                del audio[field]
                changed_fields.append(f"remove:{field}")
        if changed_fields and not dry_run:
            audio.save()
        if changed_fields:
            changes.append(Change("retag", path, ", ".join(changed_fields)))
        target = path.with_name(target_filename(tags["tracknumber"], tags["title"]))
        changes.extend(rename_path(path, target, dry_run, "rename_file", f"{path.name} -> {target.name}"))
    return changes


def ensure_folder_art(folder: Path, dry_run: bool) -> list[Change]:
    if any(p.is_file() and p.stem.lower() == "folder" for p in folder.iterdir()):
        return []
    flac_files = sorted(folder.glob("*.flac"))
    if not flac_files:
        return []
    audio = FLAC(flac_files[0])
    picture = next((pic for pic in audio.pictures if getattr(pic, "type", None) == 3), None)
    if picture is None and audio.pictures:
        picture = audio.pictures[0]
    if picture is not None:
        target = folder / f"folder{picture_extension(picture.mime)}"
        if not dry_run:
            target.write_bytes(picture.data)
        return [Change("folder_art", target, f"extract from {flac_files[0].name}")]
    sibling_art = find_sibling_art_source(folder)
    if sibling_art is None:
        return []
    target = folder / sibling_art.name
    if not dry_run:
        target.write_bytes(sibling_art.read_bytes())
    return [Change("copy_folder_art", target, f"copy from sibling folder {sibling_art.parent.name}")]


def ensure_embedded_art(folder: Path, dry_run: bool) -> list[Change]:
    art_files = [p for p in folder.iterdir() if p.is_file() and p.stem.lower() == "folder"]
    if not art_files:
        return []
    art_path = art_files[0]
    art_bytes = art_path.read_bytes()
    mime = mime_for_extension(art_path)
    changes: list[Change] = []
    for path in sorted(folder.glob("*.flac")):
        audio = FLAC(path)
        if audio.pictures:
            continue
        if not dry_run:
            picture = Picture()
            picture.type = 3
            picture.mime = mime
            picture.data = art_bytes
            audio.clear_pictures()
            audio.add_picture(picture)
            audio.save()
        changes.append(Change("embed_art", path, f"embed {art_path.name}"))
    return changes


def remove_junk_files(root: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name.lower() in JUNK_FILENAMES or path.suffix.lower() in UNWANTED_EXTENSIONS:
            if not dry_run:
                path.unlink()
            changes.append(Change("remove_junk", path, "delete junk file"))
    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda item: len(item.parts), reverse=True):
        try:
            children = sorted(path.iterdir())
        except FileNotFoundError:
            continue
        if children and all(child.is_file() and child.stem.lower() == "folder" for child in children):
            for child in children:
                if not dry_run:
                    child.unlink()
                changes.append(Change("remove_orphan_art", child, "delete orphan folder artwork"))
    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda item: len(item.parts), reverse=True):
        if path == root:
            continue
        try:
            empty = not any(path.iterdir())
        except FileNotFoundError:
            empty = False
        if empty:
            if not dry_run:
                path.rmdir()
            changes.append(Change("remove_empty_dir", path, "delete empty directory"))
    return changes


def normalize_work_folders(root: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for composer_dir in composer_dirs(root):
        for folder in sorted(p for p in composer_dir.iterdir() if p.is_dir()):
            flacs = sorted(folder.glob("*.flac"))
            if not flacs:
                continue
            changes.extend(apply_tag_normalization(folder, flacs, dry_run))
            if not dry_run:
                flacs = sorted(folder.glob("*.flac"))
            changes.extend(ensure_folder_art(folder, dry_run))
            changes.extend(ensure_embedded_art(folder, dry_run))
            changes.extend(normalize_folder_name(folder, dry_run))
    return changes


def run(root: Path, dry_run: bool) -> list[Change]:
    changes: list[Change] = []
    for path in iter_flacs(root):
        changes.extend(strip_trailing_id3v1(path, dry_run))
    changes.extend(restructure_batch(root, dry_run))
    changes.extend(normalize_work_folders(root, dry_run))
    changes.extend(remove_junk_files(root, dry_run))
    return changes


def print_report(changes: Iterable[Change], dry_run: bool) -> None:
    changes = list(changes)
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"{mode} changes: {len(changes)}")
    for change in changes:
        print(f"{change.kind}\t{change.path}\t{change.detail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize classical FLAC batches into composer/work/performance folders."
    )
    parser.add_argument("target_folder", type=Path, help="Root folder to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.target_folder.resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Target folder does not exist or is not a directory: {root}")
    changes = run(root, args.dry_run)
    print_report(changes, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
