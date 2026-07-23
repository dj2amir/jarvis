# ============================================================
#  JARVIS — Buildozer Android Spec
#  Used by .github/workflows/build.yml to create APK
# ============================================================

[app]

# App name and package
title = JARVIS
package.name = jarvis
package.domain = com.dj2amir
version = 0.1.0

# Source code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,mp3,txt,yaml,yml,json

# Version codes
version.code = 1
version.regex = __version__\\s*=\\s*['\"](.*?)['\"]
version.filename = %(source.dir)s/core/__init__.py

# Requirements (Android-compatible subset)
# NOTE: full requirements.txt has heavy C-ext packages (opencv, chromadb)
# that may not compile for Android. This is a lighter set.
# Must be a single comma-separated line (YAML doesn't support \ continuation)
requirements = python3==3.11.9, openai, numpy, edge-tts, python-dotenv, pyyaml, requests, rich, psutil, charset-normalizer, certifi, idna, urllib3

# Permissions
android.permissions = INTERNET, \
    RECORD_AUDIO, \
    CAMERA, \
    READ_EXTERNAL_STORAGE, \
    WRITE_EXTERNAL_STORAGE

# Android API level
android.api = 34
android.minapi = 24
android.sdk = 34
android.ndk = 23b

# App orientation (portrait for phone)
orientation = portrait

# Icon
# icon = assets/face/jarvis-icon.png

# Presplash (loading screen)
# presplash = assets/face/splash.png

# Other settings
osx.python_version = 3
fullscreen = 1
android.wakelock = 1
android.allow_backup = 0
android.keep_screen_on = 1


[buildozer]

log_level = 2
warn_on_root = 1
# archs = arm64-v8a, armeabi-v7a
archs = arm64-v8a
