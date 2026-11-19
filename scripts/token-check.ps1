# Instagram token'ını yerelde doğrular. Token gizli girilir, diske yazılmaz, sonunda bellekten silinir.
Set-Location (Split-Path $PSScriptRoot -Parent)
$s = Read-Host "Token'i yapistirip Enter'a basin" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
try {
    $t = ([Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)).Trim().Trim('"')
    # token gösterilmez; yalnızca biçim kontrolü
    Write-Host ("uzunluk: {0}, EAA ile basliyor: {1}, bosluk iceriyor: {2}" -f $t.Length, $t.StartsWith("EAA"), ($t -match '\s'))
    $env:IG_TOKEN = $t
    $t = $null
    $env:IG_USER_ID = "17841451600762749"
    python scripts/ig.py token-check
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    Remove-Item Env:IG_TOKEN -ErrorAction SilentlyContinue
}
