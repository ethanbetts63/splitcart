
from PIL import Image
import os

def resize_image(input_path, output_path, width):
    with Image.open(input_path) as img:
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), Image.Resampling.LANCZOS)
        img.save(output_path, "WEBP")

def main():
    image_dir = os.path.join("frontend", "src", "assets")
    images_to_resize = [
        "confused_shopper.webp",
        "splitcart_symbol_v6.webp",
        "king_kong.webp"
    ]
    widths = [320, 640, 768, 1024, 1280]

    for image_name in images_to_resize:
        input_path = os.path.join(image_dir, image_name)
        if os.path.exists(input_path):
            base, ext = os.path.splitext(image_name)
            for width in widths:
                output_filename = f"{base}-{width}w{ext}"
                output_path = os.path.join(image_dir, output_filename)
                resize_image(input_path, output_path, width)
                print(f"Created {output_path}")
        else:
            print(f"Could not find {input_path}")

if __name__ == "__main__":
    main()
