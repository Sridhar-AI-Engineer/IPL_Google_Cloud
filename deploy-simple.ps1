$ErrorActionPreference = "Stop"

Write-Host "Loading environment from .env file..."
$envContent = Get-Content ".env"
foreach ($line in $envContent) {
    if ($line -match '^([^=]+)=(.+)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$key" -Value $value
    }
}

Write-Host "PROJECT_ID: $env:PROJECT_ID"
Write-Host "Building Docker image using Cloud Build..."

$IMAGE = "gcr.io/$($env:PROJECT_ID)/ipl-coaching-api"
$SERVICE = "ipl-coaching-api"

gcloud builds submit --tag $IMAGE --project $env:PROJECT_ID

$envVars = @(
    "GEMINI_API_KEY=$($env:GEMINI_API_KEY)"
    "GEMINI_MODEL=gemini-2.0-flash"
    "ENV=production"
) -join ","

Write-Host "Deploying to Cloud Run..."
gcloud run deploy $SERVICE --image $IMAGE --platform managed --region us-central1 --allow-unauthenticated --memory 2Gi --cpu 2 --max-instances 10 --set-env-vars $envVars --project $env:PROJECT_ID

Write-Host "Getting service URL..."
gcloud run services describe $SERVICE --region us-central1 --format "value(status.url)" --project $env:PROJECT_ID
