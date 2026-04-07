# Public Safe System

This project is a real-time computer vision system that monitors a video feed to detect people breaching a designated "danger zone". It uses YOLOv8 for detection and FastAPI for real-time web socket communication.

## Running via Docker

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your system.

### Build the Docker Image
To build the docker image, run the following command in the root directory:
```bash
docker build -t public-safe-system .
```

### Run the Docker Container
Once built, you can run the container and expose port 8000:
```bash
docker run -d -p 8000:8000 --name public-safe-app public-safe-system
```
*(Optional: If you need to mount data or config directories dynamically so they are saved to your host machine, you can use volumes like `-v $(pwd)/data:/app/data`)*

#### Running with SSL
If you wish to use the `cert.pem` and `key.pem` files to run via HTTPS, you can override the Docker command:
```bash
docker run -d -p 443:443 \
    -v $(pwd)/cert.pem:/app/cert.pem \
    -v $(pwd)/key.pem:/app/key.pem \
    --name public-safe-app \
    public-safe-system \
    uvicorn server.main:app --host 0.0.0.0 --port 443 --ssl-keyfile /app/key.pem --ssl-certfile /app/cert.pem
```

## Accessing the Project
Once the server is running, you can access:
- **Dashboard:** http://localhost:8000/
- **Edge View:** http://localhost:8000/edge
