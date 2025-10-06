from PIL import Image

def recolor_image(input_path, output_path, new_color_hex):
    """
    Replaces the color of non-transparent pixels in an image with a new color.

    Args:
        input_path (str): The path to the input image file.
        output_path (str): The path to save the recolored image file.
        new_color_hex (str): The new color in hexadecimal format (e.g., "#4497d7").
    """
    try:
        img = Image.open(input_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        return

    # Convert hex color to RGBA tuple
    hex_color = new_color_hex.lstrip('#')
    new_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

    data = img.getdata()
    new_data = []

    for item in data:
        # Check if the pixel is not transparent
        if item[3] > 0:
            new_data.append(new_color)
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Image successfully recolored and saved to {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recolor a PNG image.")
    parser.add_argument("input_path", help="Path to the input PNG image.")
    parser.add_argument("output_path", help="Path to save the output PNG image.")
    parser.add_argument("new_color_hex", help="The new color in hex format (e.g., '#4497d7').")

    args = parser.parse_args()

    recolor_image(args.input_path, args.output_path, args.new_color_hex)
