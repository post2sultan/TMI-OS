$Project = "O:\TMI-OS"
$Output = "O:\TMI-OS\exports"

New-Item -ItemType Directory -Force -Path $Output | Out-Null

$Zip = Join-Path $Output ("TMI-OS-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".zip")

$SevenZip = "${env:ProgramFiles}\7-Zip\7z.exe"

if (Test-Path $SevenZip) {
    & $SevenZip a `
        -tzip `
        $Zip `
        "$Project\*" `
        -xr!.git `
        -xr!node_modules `
        -xr!__pycache__ `
        -xr!.venv `
        -xr!venv `
        -xr!dist `
        -xr!build `
        -xr!.idea `
        -xr!.vscode `
        -xr!docker\data\postgres `
        -xr!data\postgres
}
else {
    Write-Host "7-Zip not found."
}
Write-Host ""
Write-Host "Done."
Write-Host $Zip