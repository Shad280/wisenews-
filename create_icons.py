# PWA Icon Creation Script
# This creates simple placeholder icons for WiseNews

from PIL import Image, ImageDraw, ImageFont
import os

# Create static directory if it doesn't exist
os.makedirs('static', exist_ok=True)

# Create a simple icon design
def create_icon(size, filename):
    # Create image with blue background
    img = Image.new('RGB', (size, size), color='#2196F3')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "W" for WiseNews
    try:
        font = ImageFont.truetype("arial.ttf", size//2)
    except:
        font = ImageFont.load_default()
    
    text = "W"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the image
    img.save(filename)
    print(f"Created {filename}")

# Create required icon sizes
create_icon(192, 'static/icon-192.png')
create_icon(512, 'static/icon-512.png')

print("WiseNews icons created successfully!")
