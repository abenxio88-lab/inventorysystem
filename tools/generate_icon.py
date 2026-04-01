from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "msinventory.ico")

# Create a simple square icon with initials "MS" and a colored background
size = (256, 256)
img = Image.new("RGBA", size, (24, 128, 177, 255))
draw = ImageDraw.Draw(img)

# Try to use a default font; fallback to built-in if unavailable
try:
    font = ImageFont.truetype("arial.ttf", 140)
except Exception:
    font = ImageFont.load_default()

text = "MS"
try:
    # Pillow >=8: use textbbox for accurate measurements
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
except Exception:
    try:
        w, h = font.getsize(text)
    except Exception:
        w, h = 100, 100
draw.text(((size[0]-w)/2, (size[1]-h)/2), text, font=font, fill=(255,255,255,255))

# Save as .ico with multiple sizes
img.save(OUT, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Icon written to:", OUT)
