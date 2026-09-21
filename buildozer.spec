[app]

# (str) Title of your application
title = Vibes Only

# (str) Package name
package.name = vibesonly

# (str) Package domain (needed for android packaging)
package.domain = com.vibesonly.app

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (leave empty to include all files)
source.include_exts = py,png,jpg,kv,locale,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*

# (str) Application versioning
version = 13.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,urllib3

# (str) Custom source folders for requirements
# Allows to load custom code layout e.g. from custom git repos
# requirements.source.kivy = ../kivy

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Preserved screen orientation and keep screen awake
# preserve_screen_orientation = 0

#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25.2.9519653

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android NDK architecture (arm64-v8a, armeabi-v7a, x86, x86_64)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable AndroidX support. Required for modern libraries.
android.enable_androidx = True

# (list) Gradle dependencies to add
# android.gradle_dependencies =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
