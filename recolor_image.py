from PIL import Image
import colorsys
import sys

def hsl_to_rgb(h, s, l):
    """Converts an HSL color value to RGB."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return int(r * 255), int(g * 255), int(b * 255)

def recolor_image(image_path, output_path, new_hsl_color):
    """
    Replaces every non-transparent pixel in an image with a new color.

    Args:
        image_path (str): The path to the input image.
        output_path (str): The path to save the new image.
        new_hsl_color (tuple): The new color in HSL format (h, s, l).
    """
    try:
        img = Image.open(image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return

    new_rgb_color = hsl_to_rgb(*new_hsl_color)
    
    width, height = img.size
    for x in range(width):
        for y in range(height):
            r, g, b, a = img.getpixel((x, y))
            if a != 0:
                img.putpixel((x, y), new_rgb_color + (a,))

    img.save(output_path)
    print(f"Image saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python recolor_image.py <input_image> <output_image> <H> <S> <L>")
        sys.exit(1)

    input_image = sys.argv[1]
    output_image = sys.argv[2]
    try:
        h = float(sys.argv[3])
        s = float(sys.argv[4])
        l = float(sys.argv[5])
    except ValueError:
        print("Error: H, S, and L must be numbers.")
        sys.exit(1)

    target_hsl = (h, s, l)
    recolor_image(input_image, output_image, target_hsl)
