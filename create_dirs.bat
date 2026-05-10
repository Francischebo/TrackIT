@echo off
setlocal enabledelayedexpansion
cd /d "C:\Users\fivid\Desktop\Nova Lite Limited\Assets & Inventory TrackIT"

if not exist "app" (
    mkdir "app"
    mkdir "app\models"
    echo Directories created
) else (
    if not exist "app\models" (
        mkdir "app\models"
    )
)

echo Bootstrap complete
