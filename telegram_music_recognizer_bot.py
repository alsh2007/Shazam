#!/usr/bin/env python3

""" Telegram bot (single-file) that recognizes the song inside an audio/video/voice file using shazamio (Shazam reverse-engineered). Async, based on python-telegram-bot v20+.

Features:

Accepts voice, audio, video, or any document with audio

Converts input to WAV with ffmpeg

Uses shazamio to identify song title + artist

Graceful fallback message if no match


Requirements: ffmpeg, Python 3.9+, pip packages: shazamio, python-telegram-bot, aiohttp

Save this file and run: python telegram_music_recognizer_bot.py """

import os import asyncio import tempfile import subprocess from pathlib import Path from shazamio import Shazam from telegram import Update from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")  # or paste your token string here

async def convert_to_wav(input_path: Path, output_path: Path) -> bool: cmd = [ "ffmpeg", "-y", "-i", str(input_path), "-ar", "44100", "-ac", "2", "-vn", str(output_path) ] try: proc = await asyncio.create_subprocess_exec(*cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) await proc.communicate() return output_path.exists() except Exception as e: print("ffmpeg conversion failed:", e) return False

async def recognize_with_shazam(wav_path: Path) -> dict: shazam = Shazam() with open(wav_path, "rb") as f: audio_bytes = f.read() try: out = await shazam.recognize_song(audio_bytes) return out except Exception as e: print("shazam recognition error:", e) return {}

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE): msg = update.message if not msg: return

file_obj = None
file_name_hint = None

if msg.voice:
    file_obj = await msg.voice.get_file()
    file_name_hint = f"voice_{msg.voice.file_unique_id}.ogg"
elif msg.audio:
    file_obj = await msg.audio.get_file()
    file_name_hint = msg.audio.file_name or f"audio_{msg.audio.file_unique_id}"
elif msg.video:
    file_obj = await msg.video.get_file()
    file_name_hint = f"video_{msg.video.file_unique_id}.mp4"
elif msg.document:
    file_obj = await msg.document.get_file()
    file_name_hint = msg.document.file_name or f"doc_{msg.document.file_unique_id}"
elif msg.video_note:
    file_obj = await msg.video_note.get_file()
    file_name_hint = f"vnote_{msg.video_note.file_unique_id}.mp4"
else:
    await msg.reply_text("ارسل ملف صوتي/فيديو او رسالة صوتية حتى اعرف اسم الاغنية.")
    return

await msg.reply_chat_action("typing")

with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir_path = Path(tmpdir)
    in_path = tmpdir_path / file_name_hint
    out_wav = tmpdir_path / "converted.wav"

    try:
        await file_obj.download_to_drive(custom_path=str(in_path))
    except Exception as e:
        await msg.reply_text("خطأ بتنزيل الملف. حاول مرة ثانية.")
        print("download error:", e)
        return

    ok = await convert_to_wav(in_path, out_wav)
    if not ok:
        await msg.reply_text("ما اكدر احول الملف لصيغة يدعمها محرك التعرف. تأكد الملف صحيح أو اجرب صيغة ثانية.")
        return

    result = await recognize_with_shazam(out_wav)
    track = result.get("track") if isinstance(result, dict) else None

    if track:
        title = track.get("title") or "---"
        subtitle = track.get("subtitle") or "---"
        sections = track.get("sections")
        more = ""
        if isinstance(sections, list) and sections:
            for sec in sections:
                hub = sec.get("hub")
                if hub and isinstance(hub, dict):
                    providers = hub.get("providers") or []
                    for p in providers:
                        if p.get("type") == "youtube":
                            more = f"\nرابط يوتيوب ممكن: {p.get('actions', [{}])[0].get('uri', '')}"
                            break
                if more:
                    break

        reply = f"ممكن هذي الأغنية:\n- العنوان: {title}\n- الفنان: {subtitle}{more}"
        await msg.reply_text(reply)
    else:
        await msg.reply_text("ماكدر اتعرف على الاغنية. جرب صوت أو مقطع أطول أو استعمل خدمة ثانية (ACRCloud / Audd).")

def main(): if not BOT_TOKEN: print("ERROR: BOT_TOKEN env var not set. Export BOT_TOKEN=<telegram-bot-token> or edit the script.") return

app = ApplicationBuilder().token(BOT_TOKEN).build()
handler = MessageHandler(filters.ALL & (~filters.COMMAND), handle_msg)
app.add_handler(handler)

print("Starting bot...")
app.run_polling()

if name == 'main': main()

                                         
