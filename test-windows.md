# Testing Shusrusha Windows Executable

## Option 1: Windows Server Core Container (Free)

### Requirements
- Docker Desktop with Windows containers enabled
- Or Windows machine with Docker

### Quick Test Command
```bash
# Pull Windows Server Core (free base image)
docker pull mcr.microsoft.com/windows/servercore:ltsc2022

# Run container with your executable
docker run -it --rm -v "$(pwd)/dist/shusrusha-windows:/app" mcr.microsoft.com/windows/servercore:ltsc2022 cmd

# Inside container:
cd /app
dir
# Test basic functionality
echo OPENAI_API_KEY=test > .env
Shusrusha.exe --help
```

## Option 2: GitHub Actions (Free CI Testing)

### Create .github/workflows/test-windows.yml
```yaml
name: Test Windows Executable
on: [push, pull_request]

jobs:
  test-windows:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - name: Test executable
      run: |
        cd dist/shusrusha-windows
        echo "OPENAI_API_KEY=test" > .env
        ./Shusrusha.exe --version
```

## Option 3: VirtualBox Windows 10 (Free)

### Download Official Windows 10 VM
1. Visit: https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/
2. Download "Windows 10 Enterprise" VM (90-day trial)
3. Import into VirtualBox (free)
4. Copy your `dist/shusrusha-windows` folder into VM

## Option 4: Azure/AWS Free Tier Windows VM

### Azure (Free $200 credit)
```bash
# Create Windows VM (free tier)
az vm create \
  --resource-group myResourceGroup \
  --name myWindowsVM \
  --image Win2022Datacenter \
  --admin-username azureuser \
  --size Standard_B1s
```

## Option 5: Local Windows via Boot Camp/Parallels
- Boot Camp (free with Mac)
- Parallels Desktop (paid)
- VMware Fusion (paid)

## Quick Test Script

Here's a test script to validate your executable:
