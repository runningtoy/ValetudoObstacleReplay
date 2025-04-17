#!/bin/bash

echo "Starte wiederholte Ausführung alle 2 Minuten..."

while true; do
    echo "[INFO] $(date): Starte Skript..."
    python3 /app/valetudo_obstacle_image.py
    echo "[INFO] $(date): Fertig. Warte 2 Minuten..."
    sleep 120
done
