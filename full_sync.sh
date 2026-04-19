cat > safe_sync.sh << 'EOF'
#!/bin/bash

echo "Безопасная синхронизация (только код и ресурсы)..."

# Только Python файлы и папки с кодом
adb push main.py /sdcard/
adb push animated_background.py /sdcard/
adb push language_manager.py /sdcard/
adb push multilanguage_widgets.py /sdcard/
adb push sound_manager.py /sdcard/
adb push language_preferences.json /sdcard/

adb push screens /sdcard/
adb push components /sdcard/
adb push locales /sdcard/
adb push assets /sdcard/

# Копируем в приложение
adb shell "run-as org.almighty.almightyrandom cp /sdcard/main.py /data/data/org.almighty.almightyrandom/files/app/"
adb shell "run-as org.almighty.almightyrandom cp -r /sdcard/screens/* /data/data/org.almighty.almightyrandom/files/app/screens/"
adb shell "run-as org.almighty.almightyrandom cp -r /sdcard/components/* /data/data/org.almighty.almightyrandom/files/app/components/"
adb shell "run-as org.almighty.almightyrandom cp -r /sdcard/locales/* /data/data/org.almighty.almightyrandom/files/app/locales/"
adb shell "run-as org.almighty.almightyrandom cp -r /sdcard/assets/* /data/data/org.almighty.almightyrandom/files/app/assets/"

# Удаляем только .pyc, НЕ трогаем _python_bundle
adb shell "run-as org.almighty.almightyrandom find /data/data/org.almighty.almightyrandom/files/app -name '*.pyc' -delete"

# Перезапуск
adb shell am force-stop org.almighty.almightyrandom
adb shell am start -n org.almighty.almightyrandom/org.kivy.android.PythonActivity

echo "Готово!"
EOF

chmod +x safe_sync.sh