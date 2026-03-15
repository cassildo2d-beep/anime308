import os
import asyncio


# =====================================================
# GERAR THUMB
# =====================================================

async def generate_thumbnail(filepath):

    thumb_path = filepath + ".jpg"

    cmd = [
        "ffmpeg",
        "-ss", "00:00:05",
        "-i", filepath,
        "-vframes", "1",
        "-vf", "scale=320:-1",
        "-q:v", "3",
        thumb_path,
        "-y"
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    await process.wait()

    if os.path.exists(thumb_path):
        return thumb_path

    return None


# =====================================================
# UPLOAD SIMPLES
# =====================================================

async def upload_video(userbot, filepath, message, storage_chat_id):

    await message.edit_text("📤 Enviando vídeo...")

    thumb = await generate_thumbnail(filepath)

    file_name = os.path.basename(filepath)

    if file_name.endswith(".mp4.mp4"):
        file_name = file_name.replace(".mp4.mp4", ".mp4")

    caption_name = file_name.rsplit(".", 1)[0]

    sent = await userbot.send_video(
        chat_id=storage_chat_id,
        video=filepath,
        thumb=thumb,
        file_name=file_name,
        caption=f"🎬 {caption_name}",
        supports_streaming=True
    )

    if thumb and os.path.exists(thumb):
        os.remove(thumb)

    return sent.id
