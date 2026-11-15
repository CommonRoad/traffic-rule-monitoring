import argparse
import os

import cv2
import numpy as np

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")


def adjust_gamma(image, gamma=1.0):
    """Applies gamma correction to an image."""
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)


# CARLA 0.10 does not support changing the sun configuration, so we brighten the recorded images afterwards.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brighten CARLA screenshots via gamma correction.")
    parser.add_argument("input_folder", help="Folder containing the images, e.g., output/carla/carla_traffic_light.")
    parser.add_argument("--output_folder", default="brightened_results", help="Folder for the brightened images.")
    parser.add_argument("--gamma", type=float, default=1.1, help="Gamma value (higher = brighter).")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    files_processed = 0
    for filename in sorted(os.listdir(args.input_folder)):
        if not filename.lower().endswith(VALID_EXTENSIONS):
            continue
        img = cv2.imread(os.path.join(args.input_folder, filename))
        if img is None:
            print(f"Skipping (could not read): {filename}")
            continue
        cv2.imwrite(os.path.join(args.output_folder, filename), adjust_gamma(img, gamma=args.gamma))
        print(f"Processed: {filename}")
        files_processed += 1

    print(f"\nDone! Processed {files_processed} images. Results are in '{args.output_folder}'.")
