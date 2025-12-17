import subprocess
from pathlib import Path
from app.core.logger import logger


class TranscoderService:
    def transcodeToHls(self, input_path: str, output_path: str) -> bool:
        """Run ffmpeg to generate HLS without invoking a shell."""
        try:
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-c:v",
                "h264",
                "-c:a",
                "aac",
                "-strict",
                "-2",
                "-start_number",
                "0",
                "-hls_time",
                "10",
                "-hls_list_size",
                "0",
                "-f",
                "hls",
                str(out_path),
            ]
            res = subprocess.run(cmd, check=False)

            return res.returncode == 0
        except Exception as e:
            logger.error("Transcoding error: %s", e)
            return False
