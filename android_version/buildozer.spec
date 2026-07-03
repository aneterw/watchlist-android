[app]
title = yfinance Watchlist
package.name = watchlist
package.domain = org.sapiensai
source.dir = .
source.include_exts = py,kv,json,png,jpg,gif
source.include_patterns = assets/*,images/*
version = 1.0.0
requirements = python3,kivy,yfinance,pandas,numpy
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a,armeabi-v7a
orientation = portrait
fullscreen = 0
presplash.filename =
icon.filename =
permission.INTERNET = true
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 0
