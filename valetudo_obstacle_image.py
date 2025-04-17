import requests
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import subprocess
import shutil
import time
from datetime import datetime

def cleanup_old_images(output_dir, exclude_file="latest_obstacle.jpg", max_age_hours=12):
    print("Bereinige Bilder aelter als 24h...")
    
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    deleted = 0
    for filename in os.listdir(output_dir):
        if not filename.endswith(".jpg") or filename == exclude_file:
            continue

        file_path = os.path.join(output_dir, filename)
        try:
            file_mtime = os.path.getmtime(file_path)
            if now - file_mtime > max_age_seconds:
                os.remove(file_path)
                print(f"Geloescht: {filename}")
                deleted += 1
        except Exception as e:
            print(f"Fehler beim Pruefen von {filename}: {e}")

    print(f"{deleted} alte Bild(er) geloescht.")


def generate_video_from_images(output_dir, exclude_file="latest_obstacle.jpg", output_video="obstacles_replay.mp4"):
    print("Starte Video-Erzeugung...")

    # Liste aller Bilddateien auser 'latest_obstacle.jpg'
    image_files = sorted([
        f for f in os.listdir(output_dir)
        if f.endswith(".jpg") and f != exclude_file
    ])

    if not image_files:
        print("Keine Bilddateien zum Erstellen des Videos gefunden.")
        return

    #Zwischenspeicher
    tmp_dir = os.path.join(output_dir, "tmp_video")
    os.makedirs(tmp_dir, exist_ok=True)

    # Kopieren und nummerieren
    for idx, filename in enumerate(image_files):
        src = os.path.join(output_dir, filename)
        dst = os.path.join(tmp_dir, f"frame_{idx:04d}.jpg")
        shutil.copyfile(src, dst)

    video_path = os.path.join(output_dir, output_video)

    # ffmpeg Befehl
    command = [
        "ffmpeg", "-y",
        "-framerate", "1",  # 1 Bild pro Sekunde
        "-i", os.path.join(tmp_dir, "frame_%04d.jpg"),
        "-c:v", "libx264",
        "-r", "30",  # Ausgabe-Framerate
        "-pix_fmt", "yuv420p",
        video_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"? Video erfolgreich erstellt: {video_path}")
    except subprocess.CalledProcessError as e:
        print("? Fehler bei der Videoerstellung:", e)
    finally:
        # Temporaere Bilder loeschen
        shutil.rmtree(tmp_dir)

# CONFIG
VALETUDO_HOST = "http://10.0.0.174"
MAP_ENDPOINT = f"{VALETUDO_HOST}/api/v2/robot/state/map"
IMAGE_URL_PREFIX = f"{VALETUDO_HOST}/api/v2/robot/capabilities/ObstacleImagesCapability/img/"
IMAGE_OUTPUT_DIR = "/output/"
IMAGE_NAME = "latest_disney_obstacle.jpg"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# 1. Map-Status abrufen
resp = requests.get(MAP_ENDPOINT)
if resp.status_code != 200:
    print(f"Fehler beim Abrufen der Karte: {resp.status_code}")
    exit(1)

data = resp.json()

# 2. Hindernisse filtern
entities = data.get("entities", [])
obstacles = [
    e for e in entities
    if e.get("__class") == "PointMapEntity" and e.get("type") == "obstacle"
]

if not obstacles:
    print("Keine Hindernisse gefunden.")
    exit(0)

# 3. Neuestes Hindernis (nach ID oder timestamp falls vorhanden)
latest = obstacles[-1]
obstacle_id = latest.get("metaData", {}).get("id")
if not obstacle_id:
  print("Keine gueltige Hindernis-ID gefunden!")
  exit(1)
#obstacle_type = latest.get("metaData", {}).get("type", "unbekannt")
obstacle_type = latest.get("metaData", {}).get("label", "unbekannt")
image_path_raw = latest.get("metaData", {}).get("image")


# 4. Bild laden
image_url = f"{IMAGE_URL_PREFIX}{obstacle_id}"
print(f"Lade Bild von: {image_url}")
image_resp = requests.get(image_url, stream=True)

if image_resp.status_code != 200:
    print(f"Bild konnte nicht geladen werden: {image_resp.status_code}")
    exit(1)

# 5. Bild mit Text versehen
image = Image.open(BytesIO(image_resp.content)).convert("RGB")
draw = ImageDraw.Draw(image)
#text = f"Hindernis: {obstacle_type}"
text = datetime.now().strftime("Erkannt am: %d.%m.%Y %H:%M:%S")
font_size = int(image.height * 0.05)

try:
    font = ImageFont.truetype(FONT_PATH, font_size)
except:
    font = ImageFont.load_default()

bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = 10
y = image.height - text_height - 10

draw.rectangle([x - 5, y - 5, x + text_width + 5, y + text_height + 5], fill=(0, 0, 0))
draw.text((x, y), text, font=font, fill=(255, 255, 255))

# 6. Bild speichern
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(IMAGE_OUTPUT_DIR, IMAGE_NAME)
image.save(output_path)


image_name_custom = image_path_raw.replace("/", "_")
image.save(os.path.join(IMAGE_OUTPUT_DIR, image_name_custom))

print(f"Bild gespeichert als:")
print(f" - latest_obstacle.jpg")
print(f" - {image_name_custom}")

cleanup_old_images(IMAGE_OUTPUT_DIR)
generate_video_from_images(IMAGE_OUTPUT_DIR)

