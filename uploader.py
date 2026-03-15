import os
import asyncio
import json
from typing import Optional, Tuple


async def get_video_metadata(filepath: str) -> Tuple[int, int, int]:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        data = json.loads(stdout.decode())
    except Exception as e:
        print(f"[get_video_metadata] Erro: {e}")
        return 0, 0, 0

    duration = 0
    width = 0
    height = 0

    try:
        raw_duration = data.get("format", {}).get("duration", 0)
        if raw_duration and raw_duration != "N/A":
            duration = int(float(raw_duration))
    except:
        duration = 0

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            width = stream.get("width") or 0
            height = stream.get("height") or 0
            break

    return duration, width, height


async def generate_thumbnail(filepath: str, time: int = 5, width: int = 320) -> Optional[str]:
    thumb_path = filepath + ".jpg"
    cmd = (
        f'ffmpeg -ss {time} -i "{filepath}" '
        f'-vframes 1 -vf "scale={width}:-1" -q:v 3 "{thumb_path}" -y'
    )

    try:
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await process.communicate()
        if os.path.exists(thumb_path):
            return thumb_path
    except Exception as e:
        print(f"[generate_thumbnail] Erro: {e}")

    return None


async def upload_video(userbot, filepath: str, message, storage_chat_id: int) -> Optional[int]:
    await message.edit_text("📤 Preparando vídeo...")

    # Pega metadados e thumbnail
    try:
        metadata, thumb = await asyncio.gather(
            get_video_metadata(filepath),
            generate_thumbnail(filepath)
        )
        duration, width, height = metadata
    except Exception as e:
        print(f"[upload_video] Erro durante preparação: {e}")
        duration, width, height, thumb = 0, 0, 0, None

    file_name = os.path.basename(filepath)
    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")
    caption_name = os.path.splitext(file_name)[0]

    # Mostra duração no caption
    duration_text = f"{duration // 60}:{duration % 60:02d}"
    caption = f"🎬 {caption_name}\n⏱ Duração: {duration_text}"

    # Envio do vídeo com thumbnail
    try:
        sent = await userbot.send_video(
            chat_id=storage_chat_id,
            video=filepath,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb if thumb and os.path.exists(thumb) else None,
            file_name=file_name,
            caption=caption,
            supports_streaming=True
        )
    except Exception as e:
        print(f"[upload_video] Erro no envio: {e}")
        return None
    finally:
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

    return getattr(sent, "id", None)
