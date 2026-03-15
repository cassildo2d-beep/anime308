import os
import asyncio
import json

# =====================================================
# PEGAR METADATA REAL DO VÍDEO
# =====================================================
async def get_video_metadata(filepath: str):
    """
    Retorna a duração em segundos, largura e altura do vídeo.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        filepath
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if stderr:
        err_msg = stderr.decode().strip()
        if err_msg:
            print(f"[WARN] ffprobe stderr: {err_msg}")

    try:
        data = json.loads(stdout.decode())
    except json.JSONDecodeError:
        print("[ERROR] Não foi possível ler metadata do vídeo.")
        return 0, 0, 0

    # Duração
    duration = 0
    try:
        raw_duration = data.get("format", {}).get("duration", 0)
        if raw_duration and raw_duration != "N/A":
            duration = int(float(raw_duration))
    except Exception:
        duration = 0

    # Dimensões
    width = 0
    height = 0
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            width = stream.get("width", 0) or 0
            height = stream.get("height", 0) or 0
            break

    return duration, width, height

# =====================================================
# GERAR THUMBNAIL
# =====================================================
async def generate_thumbnail(filepath: str, time_offset: int = 5, width: int = 320):
    """
    Gera thumbnail do vídeo.
    `time_offset` é o segundo que vai capturar a imagem (default: 5s)
    """
    if not os.path.exists(filepath):
        return None

    thumb_path = f"{filepath}_thumb.jpg"

    cmd = (
        f'ffmpeg -ss {time_offset} -i "{filepath}" '
        f'-vframes 1 -vf "scale={width}:-1" -q:v 3 "{thumb_path}" -y'
    )

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.communicate()

    return thumb_path if os.path.exists(thumb_path) else None

# =====================================================
# UPLOAD COMPLETO
# =====================================================
async def upload_video(userbot, filepath: str, message, storage_chat_id):
    await message.edit_text("📤 Preparando vídeo...")

    # ✅ Metadata
    duration, width, height = await get_video_metadata(filepath)
    thumb = await generate_thumbnail(filepath)

    file_name = os.path.basename(filepath)
    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")

    caption_name = file_name.rsplit(".", 1)[0]

    # ✅ Envio do vídeo
    sent = await userbot.send_video(
        chat_id=storage_chat_id,
        video=filepath,
        duration=duration or None,
        width=width or None,
        height=height or None,
        thumb=thumb,
        file_name=file_name,
        caption=f"🎬 {caption_name}",
        supports_streaming=True
    )

    # ✅ Limpar thumbnail temporária
    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
