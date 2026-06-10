@echo off
cd /d D:\develop\Redis-x64-3.2.100
tasklist /FI "IMAGENAME eq redis-server.exe" 2>nul | find /I "redis-server.exe" >nul
if %errorlevel%==0 (
  echo Redis 已在运行。
  exit /b 0
)
start "Redis Server" /MIN redis-server.exe redis.windows.conf
echo Redis 已启动：127.0.0.1:6379 （密码见 redis.windows.conf 中的 requirepass）
exit /b 0
