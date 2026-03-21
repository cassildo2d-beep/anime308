import os

def format_size(size_bytes):
    """Converte bytes para MB ou GB"""
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    else:
        return f"{size_bytes / (1024**2):.2f} MB"


async def upload_video(userbot, filepath, message, storage_chat_id):
    if not os.path.exists(filepath):
        raise Exception("Arquivo não encontrado")

    await message.edit_text("📤 Enviando arquivo...")

    file_size = os.path.getsize(filepath)
    readable_size = format_size(file_size)

    filename = os.path.basename(filepath)

    caption = (
        f"📁 **{filename}**\n"
        f"💾 Tamanho: {readable_size}"
    )

    sent = await userbot.send_document(
        chat_id=storage_chat_id,
        document=filepath,
        caption=caption
    )

    return sent.id
