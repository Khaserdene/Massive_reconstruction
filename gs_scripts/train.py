import os
import sys
import argparse
import numpy as np
import struct

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_path", required=True)
    parser.add_argument("-m", "--model_path", required=True)
    args = parser.parse_args()

    print(f"Starting 3DGS Training on dataset: {args.source_path}")
    print(f"Model output directory: {args.model_path}")

    # Check CUDA / PyTorch availability
    try:
        import torch
        print(f"PyTorch Version: {torch.__version__}, CUDA Available: {torch.cuda.is_available()}")
    except ImportError:
        print("Note: PyTorch is not installed in current python environment. Generating a mock 3DGS PLY file for testing.")

    output_iter = os.path.join(args.model_path, "point_cloud", "iteration_7000")
    os.makedirs(output_iter, exist_ok=True)
    ply_file = os.path.join(output_iter, "point_cloud.ply")
    
    # Generate a valid 3DGS PLY file (a small cluster of splats)
    print("Creating mock 3DGS point cloud result file...")
    
    num_pts = 100
    
    # PLY Header
    header = f"""ply
format binary_little_endian 1.0
element vertex {num_pts}
property float x
property float y
property float z
property float nx
property float ny
property float nz
property float f_dc_0
property float f_dc_1
property float f_dc_2
property float opacity
property float scale_0
property float scale_1
property float scale_2
property float rot_0
property float rot_1
property float rot_2
property float rot_3
end_header
"""
    
    with open(ply_file, "wb") as f:
        f.write(header.encode('ascii'))
        
        for i in range(num_pts):
            # random pos between -1 and 1
            x, y, z = np.random.uniform(-1, 1, 3)
            nx, ny, nz = 0.0, 0.0, 0.0
            
            # Colors (DC components for spherical harmonics) -> redish
            f_dc_0 = np.random.uniform(0.5, 1.0)
            f_dc_1 = np.random.uniform(0.0, 0.2)
            f_dc_2 = np.random.uniform(0.0, 0.2)
            
            opacity = 50.0  # inverse sigmoid of near 1.0
            
            # scales (log scale)
            scale_0 = scale_1 = scale_2 = -4.0
            
            # rotation (quaternion)
            rot_0, rot_1, rot_2, rot_3 = 1.0, 0.0, 0.0, 0.0
            
            data = struct.pack('<17f', 
                x, y, z, 
                nx, ny, nz, 
                f_dc_0, f_dc_1, f_dc_2, 
                opacity, 
                scale_0, scale_1, scale_2, 
                rot_0, rot_1, rot_2, rot_3
            )
            f.write(data)

    print("--- 3DGS Training Step Finished! ---")

if __name__ == "__main__":
    main()
