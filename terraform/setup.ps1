# Terraform Setup Script for Windows
# This script downloads and installs Terraform

param(
    [string]$TerraformVersion = "1.7.0",
    [string]$InstallPath = "C:\terraform"
)

Write-Host "Terraform Setup Script" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "WARNING: This script should be run as Administrator for best results" -ForegroundColor Yellow
    Write-Host "Attempting to continue without admin rights..." -ForegroundColor Yellow
    Write-Host ""
}

# Create install directory
if (-not (Test-Path $InstallPath)) {
    Write-Host "Creating directory: $InstallPath" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# Download Terraform
$DownloadUrl = "https://releases.hashicorp.com/terraform/$TerraformVersion/terraform_${TerraformVersion}_windows_amd64.zip"
$ZipPath = Join-Path $env:TEMP "terraform_$TerraformVersion.zip"
$ExtractPath = Join-Path $InstallPath "terraform_$TerraformVersion"

Write-Host "Downloading Terraform $TerraformVersion..." -ForegroundColor Cyan
Write-Host "URL: $DownloadUrl" -ForegroundColor Gray

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -ErrorAction Stop
    Write-Host "✓ Downloaded successfully to $ZipPath" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to download Terraform" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Extract Terraform
Write-Host "Extracting Terraform..." -ForegroundColor Cyan

try {
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force -ErrorAction Stop
    Write-Host "✓ Extracted successfully to $ExtractPath" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to extract Terraform" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Add to PATH
$TerraformExe = Join-Path $ExtractPath "terraform.exe"

if (Test-Path $TerraformExe) {
    Write-Host "✓ Terraform executable found at $TerraformExe" -ForegroundColor Green
    
    # Add to current session PATH
    $env:PATH = "$ExtractPath;$env:PATH"
    
    Write-Host ""
    Write-Host "To make Terraform available permanently:" -ForegroundColor Yellow
    Write-Host "1. Add $ExtractPath to your system PATH environment variable" -ForegroundColor Yellow
    Write-Host "2. Or create a symlink: mklink C:\terraform\terraform.exe $TerraformExe" -ForegroundColor Yellow
    Write-Host ""
    
    # Verify installation
    Write-Host "Verifying Terraform installation..." -ForegroundColor Cyan
    & $TerraformExe version
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Terraform installed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Green
        Write-Host "1. cd terraform" -ForegroundColor Gray
        Write-Host "2. terraform init -upgrade" -ForegroundColor Gray
        Write-Host "3. terraform validate" -ForegroundColor Gray
        Write-Host "4. terraform plan -var-file=environments/development/terraform.tfvars" -ForegroundColor Gray
    } else {
        Write-Host "✗ Terraform verification failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ Terraform executable not found" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
