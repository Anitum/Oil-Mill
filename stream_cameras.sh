#!/bin/bash

# Configuration
BASE_DIR="/var/www/html/hls"
CAMERAS=(201 301 401 501 601 701 801)
RTSP_BASE="rtsp://admin:anand%4024@103.206.172.58:5554/Streaming/Channels"

# Simple FFmpeg options for 10-minute caching
FFMPEG_OPTS="-c:v copy \
    -c:a aac \
    -f hls \
    -hls_time 10 \
    -hls_list_size 60 \
    -hls_flags delete_segments+append_list \
    -rtsp_transport tcp"

# Create base directory
mkdir -p "$BASE_DIR"

# Start streaming for each camera
for camera_id in "${CAMERAS[@]}"; do
    camera_dir="$BASE_DIR/camera$camera_id"
    mkdir -p "$camera_dir"
    
    ffmpeg -i "$RTSP_BASE/$camera_id" \
        $FFMPEG_OPTS \
        "$camera_dir/camera$camera_id.m3u8" &
done

# Keep script running
while true; do
    sleep 1
done 