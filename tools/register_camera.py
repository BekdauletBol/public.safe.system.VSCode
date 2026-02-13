import argparse, json, os, uuid

def register(camera_id):
    path = f"configs/{camera_id}.json"
    config = {
        "camera_id": camera_id,
        "device_uuid": str(uuid.uuid4()),
        "target_res": [640, 480],
        "target_fps": 30
    }
    with open(path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"Camera {camera_id} registered.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-id", required=True)
    args = parser.parse_args()
    register(args.camera_id)