# 🐳 Docker on Windows - Complete Setup Guide

## 📋 What You Get with Docker

✅ **Cross-platform compatibility** - Works on any Windows version  
✅ **Isolated environment** - No Python installation conflicts  
✅ **Consistent performance** - Same experience across all machines  
✅ **Easy updates** - Just rebuild the container  
✅ **Multiple deployment options** - Development, production, etc.  

## 🚀 Quick Start Options

### Option 1: One-Click Setup (Easiest)
```cmd
# Double-click this file:
docker-quickstart.bat
```
- Automatically checks Docker
- Creates .env file for you
- Starts Shusrusha
- Opens browser automatically

### Option 2: Interactive Manager (Recommended)
```cmd
# Double-click this file:
docker-windows.bat
```
- Full menu system
- Start/stop controls
- Log viewing
- Status monitoring
- Cleanup tools

### Option 3: PowerShell Users
```powershell
# Run in PowerShell:
.\docker-manager.ps1

# Or with parameters:
.\docker-manager.ps1 start
.\docker-manager.ps1 stop
.\docker-manager.ps1 logs
```

### Option 4: Manual Commands
```cmd
# Basic startup:
docker-compose up --build -d

# View logs:
docker-compose logs -f

# Stop:
docker-compose down
```

## 📁 File Structure

Your shusrusha directory should have:
```
shusrusha/
├── 📄 Dockerfile                  # Main container config
├── 📄 docker-compose.yml          # Standard setup
├── 📄 docker-compose.dev.yml      # Development setup  
├── 📄 docker-compose.prod.yml     # Production setup
├── 🚀 docker-quickstart.bat       # One-click setup
├── 🔧 docker-windows.bat          # Interactive manager
├── 💻 docker-manager.ps1          # PowerShell manager
├── 📄 nginx.conf                  # Production web server
├── 📄 .env                        # Your API keys (create this)
├── 📄 app.py                      # Main application
├── 📄 requirements-app.txt        # Dependencies
└── 📁 lib/                        # Utility modules
```

## 🎯 Which Option to Choose?

| Use Case | Best Option | Why |
|----------|-------------|-----|
| **First time user** | `docker-quickstart.bat` | Fully automated setup |
| **Regular usage** | `docker-windows.bat` | Easy management interface |
| **PowerShell user** | `docker-manager.ps1` | Native PowerShell experience |
| **Developer** | `docker-compose.dev.yml` | Live code reloading |
| **Production** | `docker-compose.prod.yml` | Nginx, SSL, optimization |

## ⚡ Performance Tips

### For Development:
```cmd
# Use development compose for live reload:
docker-compose -f docker-compose.dev.yml up --build
```

### For Production:
```cmd
# Use production compose with nginx:
docker-compose -f docker-compose.prod.yml up --build -d
```

### Resource Limits:
```cmd
# Limit memory and CPU:
docker run --memory=2g --cpus=1.5 shusrusha
```

## 🔧 Common Docker Commands

### Management:
```cmd
# See running containers:
docker ps

# View all containers:
docker ps -a

# Follow logs:
docker-compose logs -f

# Restart service:
docker-compose restart

# Remove everything:
docker-compose down --volumes --rmi all
```

### Troubleshooting:
```cmd
# Check Docker status:
docker info

# Test Docker installation:
docker run hello-world

# Clean up system:
docker system prune -a

# Rebuild from scratch:
docker-compose build --no-cache
```

## 🌐 Accessing Your Application

Once running, access Shusrusha at:
- **Local**: http://localhost:8501
- **Network**: http://YOUR_IP:8501 (if sharing)
- **Production**: https://yourdomain.com (with nginx setup)

## 🔒 Security Notes

### Development:
- Uses standard HTTP on localhost
- API keys in .env file (not committed to git)

### Production:
- HTTPS with SSL certificates
- Nginx reverse proxy
- Rate limiting and security headers
- Non-root container user

## 📊 Monitoring

### View Resource Usage:
```cmd
# Real-time stats:
docker stats

# Container health:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs with timestamps:
docker-compose logs -f -t
```

### Health Checks:
All containers include health checks that verify:
- Application is responding
- Dependencies are available
- System resources are adequate

## 🆘 Troubleshooting

### Docker Desktop Issues:
1. **Restart Docker Desktop**
2. **Check Windows features**: Hyper-V, WSL2
3. **Update Docker Desktop** to latest version
4. **Restart computer** if needed

### Container Issues:
```cmd
# Check logs for errors:
docker-compose logs shusrusha

# Rebuild clean:
docker-compose down
docker system prune -a
docker-compose up --build

# Run interactively for debugging:
docker run -it shusrusha /bin/bash
```

### Network Issues:
```cmd
# Check port availability:
netstat -ano | findstr :8501

# Use different port:
docker run -p 8502:8501 shusrusha
```

## 💡 Pro Tips

1. **Use batch files** for consistent commands
2. **Set up aliases** for frequent operations  
3. **Monitor resource usage** with `docker stats`
4. **Use volumes** for persistent data
5. **Enable BuildKit** for faster builds:
   ```cmd
   set DOCKER_BUILDKIT=1
   ```

## 🎉 Ready to Go!

Pick your preferred method and start using Shusrusha with Docker. The containerized approach eliminates most setup issues and provides a professional deployment experience.

**Need help?** Check the specific guide for your chosen method or run the interactive managers for guided setup!
