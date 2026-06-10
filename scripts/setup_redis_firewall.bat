@echo off
:: Run as Administrator: allow Redis through Windows Firewall
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0setup_redis_firewall.ps1""'"
