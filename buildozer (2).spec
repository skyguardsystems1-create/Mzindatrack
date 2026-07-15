[app]
title = MzindaTrack
package.name = mzindatrack
package.domain = org.mzindatrack
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ico,json
source.include_patterns = assets/*,data/*,*.py
source.exclude_exts = spec,md,yml,yaml
source.exclude_dirs = tests, bin, __pycache__, .git, .github, .buildozer
version = 1.0.0

# IMPORTANT: Do NOT include 'android' as a pip requirement. It's built by p4a.
# Only include pure Python packages and libraries buildozer can cross-compile
requirements = python3==3.10.13,kivy==2.2.1,requests,plyer,pyjnius

presplash.filename = data/presplash.png
icon.filename = assets/icon.png
orientation = portrait
fullscreen = 0

# Android permissions
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# API levels
android.api = 30
android.minapi = 21
android.ndk = 28c
android.ndk_api = 21

# Build flags
android.skip_update = False
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
android.apptheme = @style/Theme.AppCompat
android.archs = arm64-v8a
android.copy_libs = 1
android.use_androidx = True

# Python-for-Android settings
p4a.branch = master
p4a.bootstrap = sdl2

# Additional android configuration
android.window_background_color = #0a0f1e
android.logcat_filters = *:S python:D
android.debug = 1

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
