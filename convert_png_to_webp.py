#!/usr/bin/env python3
"""
Script to convert all .png files to .webp in specified directories.
Uses aggressive lossy compression for maximum space savings.
"""
import os
from PIL import Image
import glob

def convert_png_to_webp(directory):
    """Convert all .png files in directory and subdirs to .webp"""
    png_files = glob.glob(os.path.join(directory, '**', '*.png'), recursive=True)
    converted = 0

    for png_path in png_files:
        webp_path = png_path.replace('.png', '.webp')

        # Skip if .webp already exists
        if os.path.exists(webp_path):
            print(f"Skipping {png_path} - .webp already exists")
            continue

        try:
            # Open and convert image
            with Image.open(png_path) as img:
                # Convert to RGBA if not already (for transparency support)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                # Save as webp with very aggressive lossy compression for much smaller files
                img.save(webp_path, 'WEBP', quality=40, method=6)
                print(f"Converted {png_path} -> {webp_path}")
                converted += 1
        except Exception as e:
            print(f"Error converting {png_path}: {e}")

    return converted

if __name__ == '__main__':
    base_dir = 'Assets/resources/game_data/icons'

    # Convert pals directory (including skin subfolder)
    pals_dir = os.path.join(base_dir, 'pals')
    print(f"Converting .png files in {pals_dir}...")
    pals_converted = convert_png_to_webp(pals_dir)
    print(f"Converted {pals_converted} files in pals/")

    # Convert tech directory
    tech_dir = os.path.join(base_dir, 'tech')
    print(f"Converting .png files in {tech_dir}...")
    tech_converted = convert_png_to_webp(tech_dir)
    print(f"Converted {tech_converted} files in tech/")

    total = pals_converted + tech_converted
    print(f"Total converted: {total} files")
