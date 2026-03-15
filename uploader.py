import os
import asyncio
import json
from typing import Optional, Tuple


# =====================================================
# PEGAR METADATA REAL
# =====================================================
async def get_video_metadata(filepath: str) -> Tuple[int, int, int]:
    """Retorna (duração em segundos, largura, altura)"""
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
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
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
    except Exception:
        duration = 0

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            width = stream.get("width") or 0
            height = stream.get("height") or 0
            break

    return duration, width, height


# =====================================================
# GERAR THUMB
# =====================================================

async def generate_thumbnail(filepath):

    thumb_path = filepath + ".jpg"

    cmd = (
        f'ffmpeg -ss 00:00:05 -i "{filepath}" '
        f'-vframes 1 -vf "scale=320:-1" -q:v 3 "{thumb_path}" -y'
    )

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    await process.communicate()

    if os.path.exists(thumb_path):
        return thumb_path

    return None



# =====================================================
# UPLOAD COMPLETO COM INFO
# =====================================================
async def upload_video(userbot, filepath: str, message, storage_chat_id: int) -> Optional[int]:
    """Faz upload de vídeo com thumb, duração e metadata"""
    await message.edit_text("📤 Preparando vídeo...")

    # 🔥 Pegar metadados e gerar thumbnail simultaneamente
    duration, width, height, thumb = 0, 0, 0, None
    try:
        duration, width, height, thumb = await asyncio.gather(
            get_video_metadata(filepath),
            generate_thumbnail(filepath)
        )
        if isinstance(duration, tuple):
            duration, width, height = duration  # descompacta tuple
    except Exception as e:
        print(f"[upload_video] Erro durante preparação: {e}")

    file_name = os.path.basename(filepath)

    # 🔥 Limpeza do nome
    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")
    caption_name = os.path.splitext(file_name)[0]

    try:
        sent = await userbot.send_video(
            chat_id=storage_chat_id,
            video=filepath,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            file_name=file_name,
            caption=f"🎬 {caption_name}",
            supports_streaming=True
        )
    except Exception as e:
        print(f"[upload_video] Erro no envio: {e}")
        return None
    finally:
        # 🔥 Remove thumb se existir
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

    return getattr(sent, "id", None)
