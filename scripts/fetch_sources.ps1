$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourcesRoot = Join-Path $projectRoot 'sources'
$loghubPath = Join-Path $sourcesRoot 'loghub'

New-Item -ItemType Directory -Path $sourcesRoot -Force | Out-Null
if (Test-Path (Join-Path $loghubPath '.git')) {
    git -C $loghubPath pull --ff-only
} elseif (-not (Test-Path $loghubPath)) {
    git clone --depth 1 https://github.com/logpai/loghub.git $loghubPath
} else {
    throw "Le chemin existe mais n'est pas un clone Git : $loghubPath"
}
