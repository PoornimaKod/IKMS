#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm run build
cd ..

echo "Copying frontend files to backend static directory..."
# Create the directory if it doesn't exist
mkdir -p src/app/static

# Copy all contents of dist to static
cp -r frontend/dist/* src/app/static/

echo "Built and copied successfully!"
