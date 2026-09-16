import os
import sys
import time
import json
import argparse
import glob

def print_log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def process_frame(frame_path, pose_path, mock=True):
    # This function represents the Incremental Training step for one frame.
    # 1. Render current 3DGS from the given 'pose'.
    # 2. Calculate Loss between render and 'frame_img'.
    # 3. If Loss > Threshold -> Densify (add new Gaussians).
    # 4. If Loss < Threshold -> Refine (gradient descent step to optimize existing Gaussians).
    
    with open(pose_path, "r") as f:
        pose = json.load(f)
        
    if mock:
        # Simulate processing time (graceful degradation testing)
        time.sleep(0.1)
        return {"loss": 0.05, "status": "Refined"}
    else:
        # Real PyTorch training code would go here
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--session_dir", required=True, help="Path to the session data directory")
    args = parser.parse_args()

    print_log("--- Starting Real-Time Incremental 3DGS Trainer ---")
    print_log(f"Monitoring directory: {args.session_dir}")

    has_torch = False
    try:
        import torch
        if torch.cuda.is_available():
            print_log(f"PyTorch CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
            has_torch = True
        else:
            print_log("WARNING: PyTorch found but CUDA not available. Running in MOCK mode.")
    except ImportError:
        print_log("WARNING: PyTorch not installed. Running in MOCK mode for UI testing.")

    processed_frames = set()

    try:
        while True:
            # Look for new frames and poses
            poses = glob.glob(os.path.join(args.session_dir, "pose_*.json"))
            poses.sort()
            
            for pose_path in poses:
                frame_idx = os.path.basename(pose_path).replace("pose_", "").replace(".json", "")
                if frame_idx in processed_frames:
                    continue
                    
                frame_path = os.path.join(args.session_dir, f"frame_{frame_idx}.jpg")
                if not os.path.exists(frame_path):
                    continue # Wait for image to arrive
                
                # Process the new frame incrementally
                result = process_frame(frame_path, pose_path, mock=not has_torch)
                print_log(f"Processed frame {frame_idx} | Action: {result['status']} | Loss: {result['loss']}")
                
                processed_frames.add(frame_idx)
                
            time.sleep(0.1) # Sleep briefly to prevent high CPU usage
            
    except KeyboardInterrupt:
        print_log("Real-time training stopped.")

if __name__ == "__main__":
    main()
