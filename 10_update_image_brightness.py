import cv2
import numpy as np
import os


def adjust_gamma(image, gamma=1.0):
    """Applies gamma correction to an image."""
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

# CARLA 10 does not support changing sun config
# --- Configuration ---
input_folder = 'carla_traffic_light'  # The folder containing your dark images
output_folder = 'brightened_results'  # Where the new images will go
gamma_value = 1.1  # Adjust this (higher = brighter)
valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

# --- Main Process ---

# 1. Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Created folder: {output_folder}")

# 2. Loop through all files in the input folder
files_processed = 0
for filename in os.listdir(input_folder):
    if filename.lower().endswith(valid_extensions):
        # Build the full file paths
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Load the image
        img = cv2.imread(input_path)

        if img is not None:
            # Apply gamma correction
            brightened_img = adjust_gamma(img, gamma=gamma_value)

            # Save to the output folder
            cv2.imwrite(output_path, brightened_img)
            print(f"Processed: {filename}")
            files_processed += 1
        else:
            print(f"Skipping (could not read): {filename}")

print(f"\nDone! Processed {files_processed} images.")
print(f"You can find them in the '{output_folder}' directory.")