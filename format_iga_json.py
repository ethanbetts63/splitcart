
import json
import os

def format_json_file():
    """
    Reads an unformatted JSON file, parses its content, and writes it
    to a new, properly formatted JSON file.
    """
    base_path = os.path.join('C:', os.sep, 'Users', 'ethan', 'coding', 'splitcart')
    input_file_path = os.path.join(base_path, 'iga_all_stores.txt')
    output_file_path = os.path.join(base_path, 'iga_all_stores_formatted.json')

    print(f"Reading from: {input_file_path}")
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            # Read the entire file content, which is expected to be a single line of JSON
            unformatted_json_string = f.read()
    except FileNotFoundError:
        print(f"ERROR: Input file not found at {input_file_path}")
        return
    except Exception as e:
        print(f"ERROR: Could not read the input file. {e}")
        return

    print("Parsing JSON data...")
    try:
        # Parse the string into a Python dictionary
        data = json.loads(unformatted_json_string)
    except json.JSONDecodeError:
        print("ERROR: The file content is not valid JSON. Could not parse.")
        return

    print(f"Writing formatted JSON to: {output_file_path}")
    try:
        # Write the Python dictionary to a new file with an indent of 4 for readability
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print("\nSuccessfully created the formatted JSON file.")
    except Exception as e:
        print(f"ERROR: Could not write to the output file. {e}")

if __name__ == "__main__":
    format_json_file()
