# I am lazy lmao
Write-Host "Building Docker image..."
docker build -t plex-discord-webhook .

# Stop and remove existing container if it exists
if (docker ps -a -q -f name=webhook-container) {
    Write-Host "Removing existing container..."
    docker stop webhook-container | Out-Null
    docker rm webhook-container | Out-Null
}

Write-Host "Running Docker container..."
docker run -d -p 8000:8000 --name webhook-container plex-discord-webhook

Write-Host "Build and Run job completed."