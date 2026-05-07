# PowerShell Deployment Script

# Exit on error
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying IPL Agentic AI Coaching System to Cloud Run..."

# Load environment variables from .env file
if (Test-Path ".env") {
    Write-Host "📋 Loading environment variables from .env file..."
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Check required environment variables
if (-not $env:PROJECT_ID) {
    Write-Host "❌ Please set PROJECT_ID first"
    exit 1
}

$IMAGE = "gcr.io/$($env:PROJECT_ID)/ipl-coaching-api"
$SERVICE = "ipl-coaching-api"

# Build Docker image
Write-Host "📦 Building Docker image..."
docker build -t $IMAGE .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed"
    exit 1
}

# Push image
Write-Host "⬆️ Pushing Docker image..."
docker push $IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed"
    exit 1
}

# Deploy to Cloud Run
Write-Host "☁️ Deploying to Cloud Run..."

$envVars = "GEMINI_API_KEY=$($env:GEMINI_API_KEY),GEMINI_MODEL=gemini-2.0-flash,ENV=production"

& gcloud run deploy $SERVICE `
    --image $IMAGE `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --max-instances 10 `
    --set-env-vars $envVars

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run deployment failed"
    exit 1
}

# Output service URL
Write-Host "✅ Deployment successful!"
Write-Host "🔗 Live URL:"
& gcloud run services describe $SERVICE `
    --region us-central1 `
    --format "value(status.url)"