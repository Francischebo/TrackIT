param(
  [switch]$Build,
  [switch]$CI,
  [switch]$Compose,
  [string]$ImageName = ''
)

$repo = (Get-Location).Path

if ($CI) {
  if ([string]::IsNullOrEmpty($ImageName)) { $ImageName = 'assets-inventory-ci:latest' }
  $dockerfile = 'Dockerfile.ci'
} else {
  if ([string]::IsNullOrEmpty($ImageName)) { $ImageName = 'assets-inventory-dev:latest' }
  $dockerfile = 'Dockerfile'
}

if ($Build) {
  Write-Host "Building Docker image $ImageName using $dockerfile..."
  docker build -t $ImageName -f $dockerfile .
}

if ($Compose) {
  Write-Host "Starting docker-compose (service: app)."
  docker-compose up --build
  exit
}

Write-Host "Running container (mounting $repo to /app) from image $ImageName..."
docker run --rm -it -v "${repo}:/app" -w /app $ImageName
