# Thanatos Windows PATH Installer
# Adds the Thanatos project directory to your User PATH environment variable
# Run this once in PowerShell: .\install_cli.ps1

$ThanatosDir = $PSScriptRoot
Write-Host "[•] Thanatos Directory: $ThanatosDir" -ForegroundColor Cyan

$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($CurrentPath -split ';' -contains $ThanatosDir) {
    Write-Host "[✓] Thanatos is already in your User PATH!" -ForegroundColor Green
} else {
    $NewPath = "$CurrentPath;$ThanatosDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "[✓] Successfully added Thanatos to your User PATH!" -ForegroundColor Green
    Write-Host "    Restart your terminal or open a new CMD/PowerShell window." -ForegroundColor Yellow
}

Write-Host "`nYou can now run anywhere:" -ForegroundColor White
Write-Host "  thanatos              # Launch full interactive CLI" -ForegroundColor Cyan
Write-Host "  thanatos -c '/status' # Run non-interactive command" -ForegroundColor Cyan
Write-Host "  thanatos --help       # View CLI options`n" -ForegroundColor Cyan
