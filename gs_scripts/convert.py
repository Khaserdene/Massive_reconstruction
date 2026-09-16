import os
import sys
import subprocess
import argparse
import glob
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_path", required=True, help="Path to scene directory containing frames")
    parser.add_argument("--camera", default="PINHOLE")
    parser.add_argument("--colmap_executable", default="colmap")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source_path)
    print(f"Processing COLMAP for source directory: {source_path}")

    input_images_dir = os.path.join(source_path, "input")
    if not os.path.exists(input_images_dir):
        jpgs = glob.glob(os.path.join(source_path, "*.jpg")) + glob.glob(os.path.join(source_path, "*.png"))
        if jpgs:
            os.makedirs(input_images_dir, exist_ok=True)
            for img in jpgs:
                shutil.copy(img, input_images_dir)
        else:
            print(f"No JPG/PNG images found in {source_path}")
            sys.exit(1)

    distorted_dir = os.path.join(source_path, "distorted")
    os.makedirs(distorted_dir, exist_ok=True)
    db_path = os.path.join(distorted_dir, "database.db")
    sparse_dir = os.path.join(distorted_dir, "sparse")
    os.makedirs(sparse_dir, exist_ok=True)

    print("Step 1/4: Running COLMAP Feature Extractor...")
    cmd1 = [args.colmap_executable, "feature_extractor", "--database_path", db_path, "--image_path", input_images_dir, "--ImageReader.camera_model", args.camera]
    res1 = subprocess.run(cmd1)
    if res1.returncode != 0:
        print("Feature extraction failed. Make sure 'colmap' is installed and added to PATH.")
        sys.exit(res1.returncode)

    print("Step 2/4: Running COLMAP Exhaustive Matcher...")
    cmd2 = [args.colmap_executable, "exhaustive_matcher", "--database_path", db_path]
    res2 = subprocess.run(cmd2)
    if res2.returncode != 0:
        print("Matching failed.")
        sys.exit(res2.returncode)

    print("Step 3/4: Running COLMAP Mapper...")
    cmd3 = [args.colmap_executable, "mapper", "--database_path", db_path, "--image_path", input_images_dir, "--output_path", sparse_dir]
    res3 = subprocess.run(cmd3)
    if res3.returncode != 0:
        print("Mapping failed.")
        sys.exit(res3.returncode)

    print("Step 4/4: Running COLMAP Image Undistorter...")
    model_0_dir = os.path.join(sparse_dir, "0")
    cmd4 = [args.colmap_executable, "image_undistorter", "--image_path", input_images_dir, "--input_path", model_0_dir, "--output_path", source_path, "--output_type", "COLMAP"]
    res4 = subprocess.run(cmd4)
    if res4.returncode != 0:
        print("Undistort failed.")
        sys.exit(res4.returncode)

    print("--- COLMAP Processing Finished Successfully! ---")

if __name__ == "__main__":
    main()
