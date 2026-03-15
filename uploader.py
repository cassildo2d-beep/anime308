import os
import asyncio
import json
from typing import Optional, Tuple
import random

# ================= METADATA ===================
async def get_video_metadata(filepath: str) -> Tuple[int, int, int]:
    """Retorna duração, largura e altura"""
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

# ================= REPROCESSAR VIDEO ===================
async def reprocess_video(filepath: str) -> str:
    """Reprocessa vídeo para streaming e duração correta"""
    output_path = filepath + ".processed.mp4"
    cmd = (
        f'ffmpeg -i "{filepath}" -c copy -movflags +faststart -y "{output_path}"'
    )
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.communicate()
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"[reprocess_video] Erro: {e}")
    return filepath  # fallback para o vídeo original se der erro

# ================= THUMB ===================
async def generate_thumbnail(filepath: str, width: int = 320) -> Optional[str]:
    """Gera thumbnail do frame mais interessante (5–15% do vídeo)"""
    duration, _, _ = await get_video_metadata(filepath)
    if duration < 5:
        time = 1
    else:
        time = max(1, int(duration * random.uniform(0.05, 0.15)))

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

# ================= UPLOAD ===================
async def upload_video(userbot, filepath: str, message, storage_chat_id: int) -> Optional[int]:
    await message.edit_text("📤 Preparando vídeo...")

    file_name = os.path.basename(filepath)
    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")
    caption_name = os.path.splitext(file_name)[0]

    # Reprocessa o vídeo
    processed_path = await reprocess_video(filepath)

    # Pega metadados e thumbnail
    try:
        metadata, thumb = await asyncio.gather(
            get_video_metadata(processed_path),
            generate_thumbnail(processed_path)
        )
        duration, width, height = metadata
    except:
        duration, width, height, thumb = 0, 0, 0, None

    caption = f"🎬 {caption_name}\n⏱ Duração: {duration // 60}:{duration % 60:02d}"

    # Envio do vídeo com thumb real
    try:
        sent = await userbot.send_video(
            chat_id=storage_chat_id,
            video=processed_path,
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
        # Remove arquivos temporários
        if thumb and os.path.exists(thumb):
            os.remove(thumb)
        if processed_path != filepath and os.path.exists(processed_path):
            os.remove(processed_path)

    return getattr(sent, "id", None)
