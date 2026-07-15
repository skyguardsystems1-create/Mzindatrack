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

# IMPORTANT: Don't pin python3 version - let it use the system version
# The system python 3.14.2 will be used as hostpython3
requirements = python3,kivy==2.2.1,requests,plyer,pyjnius,kivy-garden.xwebview

presplash.filename = assets/presplash.png
icon.filename = assets/icon.png
orientation = portrait
fullscreen = 0

# Android permissions
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_NETWORK_STATE

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

# WebView support
android.gradle_dependencies = 'androidx.webkit:webkit:1.6.1'

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
