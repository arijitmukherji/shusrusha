# Shusrusha Docker Management Script for PowerShell
# Run this script to manage Shusrusha with Docker on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "logs", "status", "cleanup", "rebuild")]
    [string]$Action = ""
)

function Write-Header {
    Write-Host ""
    Write-Host "========================================"  -ForegroundColor Cyan
    Write-Host "   🐳 Shusrusha Docker Manager"  -ForegroundColor Cyan
    Write-Host "========================================"  -ForegroundColor Cyan
    Write-Host ""
}

function Test-Docker {
    try {
        $null = docker --version
        $null = docker info
        return $true
    }
    catch {
        Write-Host "❌ Docker not found or not running!" -ForegroundColor Red
        Write-Host "Please install Docker Desktop and make sure it's running." -ForegroundColor Yellow
        return $false
    }
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host "⚠️  No .env file found!" -ForegroundColor Yellow
        $apiKey = Read-Host "Enter your OpenAI API key (or press Enter to skip)"
        if ($apiKey) {
            "OPENAI_API_KEY=$apiKey" | Out-File -FilePath ".env" -Encoding utf8
            Write-Host "✅ Created .env file" -ForegroundColor Green
        }
        Write-Host ""
    }
}

function Start-Shusrusha {
    Write-Host "🚀 Starting Shusrusha..." -ForegroundColor Green
    docker-compose up --build -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Shusrusha is starting up!" -ForegroundColor Green
        Write-Host "🌐 URL: http://localhost:8501" -ForegroundColor Cyan
        Write-Host "⏱️  Please wait 30-60 seconds for startup" -ForegroundColor Yellow
        
        # Wait a bit and then open browser
        Start-Sleep -Seconds 5
        try {
            Start-Process "http://localhost:8501"
        }
        catch {
            Write-Host "Could not auto-open browser. Please visit http://localhost:8501" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ Failed to start Shusrusha" -ForegroundColor Red
    }
}

function Stop-Shusrusha {
    Write-Host "🛑 Stopping Shusrusha..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Shusrusha stopped" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "📊 Showing logs (Press Ctrl+C to stop)..." -ForegroundColor Cyan
    docker-compose logs -f
}

function Show-Status {
    Write-Host "📋 Container Status:" -ForegroundColor Cyan
    Write-Host ""
    docker ps -a --filter "name=shusrusha"
    Write-Host ""
    Write-Host "Docker Images:" -ForegroundColor Cyan
    docker images | Select-String "shusrusha"
    Write-Host ""
    Write-Host "Resource Usage:" -ForegroundColor Cyan
    docker stats --no-stream --format "table {{.Container}}`t{{.CPUPerc}}`t{{.MemUsage}}`t{{.NetIO}}" | Select-String "shusrusha"
}

function Clean-Docker {
    $confirm = Read-Host "⚠️  This will remove all Shusrusha containers and images! Are you sure? (y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
        docker-compose down
        docker container prune -f
        docker image prune -f
        docker rmi shusrusha-shusrusha 2>$null
        Write-Host "✅ Cleanup complete" -ForegroundColor Green
    }
}

function Rebuild-Shusrusha {
    Write-Host "🔧 Rebuilding Shusrusha..." -ForegroundColor Yellow
    docker-compose down
    docker system prune -f
    docker-compose up --build -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Rebuild complete!" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Rebuild failed" -ForegroundColor Red
    }
}

function Show-Menu {
    Write-Host "Choose an option:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. 🚀 Start Shusrusha" -ForegroundColor Green
    Write-Host "2. 🛑 Stop Shusrusha" -ForegroundColor Yellow
    Write-Host "3. 📊 View logs" -ForegroundColor Cyan
    Write-Host "4. 🔧 Rebuild" -ForegroundColor Magenta
    Write-Host "5. 📋 Show status" -ForegroundColor Blue
    Write-Host "6. 🧹 Clean up" -ForegroundColor Red
    Write-Host "7. 🌐 Open browser" -ForegroundColor Cyan
    Write-Host "8. ❌ Exit" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-8)"
    return $choice
}

# Main script
Write-Header

if (-not (Test-Docker)) {
    exit 1
}

Write-Host "✅ Docker is ready" -ForegroundColor Green
Write-Host ""

Test-EnvFile

# Handle command line argument
if ($Action) {
    switch ($Action) {
        "start" { Start-Shusrusha }
        "stop" { Stop-Shusrusha }
        "logs" { Show-Logs }
        "status" { Show-Status }
        "cleanup" { Clean-Docker }
        "rebuild" { Rebuild-Shusrusha }
    }
    exit
}

# Interactive menu
do {
    $choice = Show-Menu
    switch ($choice) {
        "1" { Start-Shusrusha }
        "2" { Stop-Shusrusha }
        "3" { Show-Logs }
        "4" { Rebuild-Shusrusha }
        "5" { Show-Status }
        "6" { Clean-Docker }
        "7" { 
            try {
                Start-Process "http://localhost:8501"
            }
            catch {
                Write-Host "Could not open browser. Please visit http://localhost:8501" -ForegroundColor Yellow
            }
        }
        "8" { 
            Write-Host "👋 Goodbye!" -ForegroundColor Green
            exit 
        }
        default { 
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red 
        }
    }
    Write-Host ""
    Read-Host "Press Enter to continue"
    Clear-Host
    Write-Header
} while ($true)
