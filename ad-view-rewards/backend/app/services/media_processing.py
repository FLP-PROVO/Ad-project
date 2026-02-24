import subprocess
from pathlib import Path


class MediaProcessingError(Exception):
    pass


def probe_video_duration_seconds(file_path: Path) -> int:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(file_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        duration_raw = result.stdout.strip()
        return int(float(duration_raw))
    except (subprocess.SubprocessError, ValueError) as exc:
        raise MediaProcessingError("ffprobe failed or invalid video file") from exc
