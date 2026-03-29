# --- CONFIGURATION ---
$EXE_NAME = "SpokaneResourceHub"
$MAIN_FILE = "resource_hub_pro.py"
$ICON_FILE = "app_icon.ico" # Make sure this file exists in your folder!

Write-Host "--- Starting Build Process for $EXE_NAME ---" -ForegroundColor Cyan

# 1. Clean old build files to save space
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 2. Run PyInstaller
Write-Host "Creating Executable..." -ForegroundColor Yellow
# If you don't have an icon yet, remove the --icon line below
pyinstaller --noconfirm --onefile --windowed `
            --icon="$ICON_FILE" `
            --name "$EXE_NAME" `
            "$MAIN_FILE"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully built: dist/$EXE_NAME.exe" -ForegroundColor Green

    # 3. Git Automation (Pushes code, ignores heavy EXE)
    Write-Host "Syncing source code to GitHub..." -ForegroundColor Yellow
    git add .
    git commit -m "Auto-build and sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git push origin main

    Write-Host "--- Deployment Complete ---" -ForegroundColor Green
} else {
    Write-Host "Build Failed. Check your Python environment." -ForegroundColor Red
}