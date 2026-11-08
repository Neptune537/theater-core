<#
.SYNOPSIS
    Kuroshio Gyre / Theater 24/7 Siren Radio Live Streamer to YouTube.
    Pipes live audio stream to YouTube RTMP with audio-reactive visualizer.
#>

param(
    [string]$StreamKey = "sxj7-8328-16dc-fj8t-8gy0",
    [string]$AudioSource = "http://127.0.0.1:8082/live.mp3",
    [string]$RtmpUrl = "rtmp://a.rtmp.youtube.com/live2"
)

$FullRtmpTarget = "$RtmpUrl/$StreamKey"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 📻 Kuroshio Gyre: Siren Radio 24/7 -> YouTube Live" -ForegroundColor Green
Write-Host " Audio Ingest:  $AudioSource" -ForegroundColor Yellow
Write-Host " RTMP Endpoint: $RtmpUrl/********" -ForegroundColor Yellow
Write-Host " Output Specs:  1920x1080 @ 30fps (H.264 / AAC 192k)" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Complex filter:
# 1. Generate deep midnight cyan background (1920x1080 @ 30fps)
# 2. Render live dynamic audio waveform (1600x400)
# 3. Center overlay waveform over the background
$filter = "color=c=0x070b12:s=1920x1080:r=30[bg];" +
          "[0:a]showwaves=s=1600x400:mode=cline:colors=0x00e5ff:scale=cbrt[wave];" +
          "[bg][wave]overlay=(W-w)/2:(H-h)/2[outv]"

while ($true) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Connecting to Siren Radio and broadcasting to YouTube Live..." -ForegroundColor Green

    & ffmpeg -re -i $AudioSource `
        -filter_complex $filter `
        -map "[outv]" -map "0:a" `
        -c:v libx264 -preset veryfast -b:v 3000k -maxrate 3500k -bufsize 7000k -pix_fmt yuv420p -g 60 `
        -c:a aac -b:a 192k -ar 44100 `
        -f flv $FullRtmpTarget

    Write-Warning "[$(Get-Date -Format 'HH:mm:ss')] Stream disconnected or interrupted. Reconnecting in 5 seconds..."
    Start-Sleep -Seconds 5
}
