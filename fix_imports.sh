#!/bin/bash
while true; do
    find /mnt/c/Almighty_random_APK/.buildozer -name "*.pyx" 2>/dev/null | while read file; do
        if ! grep -q "from ctypes import c_long as long" "$file" 2>/dev/null; then
            if grep -q "long" "$file" 2>/dev/null; then
                echo "Исправляем: $file"
                sed -i '1i from ctypes import c_long as long' "$file" 2>/dev/null
            fi
        fi
    done

    find /mnt/c/Almighty_random_APK/.buildozer -name "*.pxi" 2>/dev/null | while read file; do
        if ! grep -q "from ctypes import c_long as long" "$file" 2>/dev/null; then
            if grep -q "long" "$file" 2>/dev/null; then
                echo "Исправляем: $file"
                sed -i '1i from ctypes import c_long as long' "$file" 2>/dev/null
            fi
        fi
    done

    sleep 3
done