#!/bin/bash
# تثبيت ffmpeg
apt-get update && apt-get install -y ffmpeg

# تشغيل البوت
python3 telegram_music_recognizer_bot.py
