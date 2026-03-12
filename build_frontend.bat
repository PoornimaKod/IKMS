@echo off
echo Building frontend...
cd frontend

REM Run the Vite build process
call npm run build
if %errorlevel% neq 0 (
    echo Error building frontend.
    cd ..
    exit /b %errorlevel%
)

cd ..

echo.
echo Copying frontend files to backend static directory...
xcopy /E /I /Y frontend\dist\* src\app\static\

echo.
echo Built and copied successfully!
