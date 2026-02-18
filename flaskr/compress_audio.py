import io
import os
import subprocess
import tempfile
from pathlib import Path

TARGET_BYTES = 24 * 1024 * 1024  # 24 MiB

def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def _duration_seconds(media_path: str) -> float:
    # video duration in seconds
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        media_path,
    ]
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    return float(out)

def compress_audio(file_obj: io.BytesIO, filename: str, target_bytes: int = TARGET_BYTES) -> io.BytesIO:
    """
    we take an uploaded video/audio in BytesIO, and output a compressed OGG/Opus audio in BytesIO
    """
    file_obj.seek(0)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        in_path = td / filename
        out_path = td / "audio.ogg"

        in_path.write_bytes(file_obj.read())

        dur = _duration_seconds(str(in_path))
        if dur <= 0:
            raise ValueError("Could not determine media duration")

        # bits/sec = target_bytes * 8 / seconds
        target_bps = int(target_bytes * 8 / dur)

        # dividing by 1000 to bps -> Kbps, and constraining everything to be in [12,96]
        target_kbps = max(12, min(96, target_bps // 1000))

        cmd = [
            "ffmpeg", "-y",
            "-i", str(in_path),
            "-vn",                 # no video
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "libopus",
            "-b:a", f"{target_kbps}k",
            "-application", "voip",
            str(out_path),
        ]
        _run(cmd)

        data = out_path.read_bytes()

    bio = io.BytesIO(data)
    bio.name = "audio.ogg"
    bio.seek(0)
    return bio

def split_audio_ogg_bytes(audio_file: io.BytesIO, filename: str, chunk_seconds: int = 15 * 60) -> list[tuple[io.BytesIO, float]]:
    """
    we split an OGG/Opus audio BytesIO into chunks of chunk_seconds.
    """
    audio_file.seek(0)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        in_path = td / filename
        out_dir = td / "chunks"
        out_dir.mkdir(parents=True, exist_ok=True)

        in_path.write_bytes(audio_file.read())

        pattern = str(out_dir / "chunk_%03d.ogg")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(in_path),
            "-f", "segment",
            "-segment_time", str(chunk_seconds),
            "-reset_timestamps", "1",
            "-c", "copy",
            pattern,
        ]
        _run(cmd)

        chunk_paths = sorted(out_dir.glob("chunk_*.ogg"))
        if not chunk_paths:
            return []

        chunks: list[tuple[io.BytesIO, float]] = []
        offset = 0.0

        for p in chunk_paths:
            data = p.read_bytes()
            bio = io.BytesIO(data)
            bio.name = p.name
            bio.seek(0)

            chunks.append((bio, offset))

            offset += _duration_seconds(str(p))

    return chunks