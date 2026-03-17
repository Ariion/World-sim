@echo off
title Genesis Engine - Arret
echo [..] Arret du serveur Genesis Engine...
taskkill /f /fi "WINDOWTITLE eq Genesis Server" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Genesis Tunnel" >nul 2>&1
echo [OK] Serveur arrete.
timeout /t 2 /nobreak >nul
