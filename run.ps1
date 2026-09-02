[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
