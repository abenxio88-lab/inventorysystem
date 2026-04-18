# Move all top-level items except MintakaEnterprise and .git into this backup folder.
# Run from repository root (PowerShell) as administrator if needed.

$root = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
# The script is inside backup_all_2026-04-18; set repo root as parent of this folder
$repo = Join-Path $root '..' | Resolve-Path -Path | Select-Object -ExpandProperty Path
Write-Host "Repo root: $repo"

$keep = @('MintakaEnterprise','.git')
Get-ChildItem -Path $repo -Force | ForEach-Object {
    $name = $_.Name
    if ($keep -contains $name) {
        Write-Host "Keeping: $name"
    } elseif ($name -eq 'backup_all_2026-04-18') {
        Write-Host "Skipping backup folder"
    } else {
        $src = Join-Path $repo $name
        $dest = Join-Path (Join-Path $repo 'backup_all_2026-04-18') $name
        Write-Host "Moving: $src -> $dest"
        try {
            Move-Item -Path $src -Destination $dest -Force -ErrorAction Stop
        } catch {
            Write-Warning ("Failed to move {0}: {1}" -f $name, $_)
        }
    }
}

Write-Host "Move complete. Remaining top-level items:"
Get-ChildItem -Path $repo -Name
