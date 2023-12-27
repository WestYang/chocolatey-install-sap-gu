﻿$ErrorActionPreference = 'Stop'
$packageArgs = @{
  packageName    = $env:ChocolateyPackageName
  softwareName   = 'sap-gui'
  fileType       = 'exe'
  silentArgs     = '/all /silent /uninstall'
  validExitCodes = @(0,129)
}

[array]$key = Get-UninstallRegistryKey @packageArgs

if ($key.Count -eq 1) {
    $key | ForEach-Object { 
        $packageArgs['file'] = "$($_.UninstallString)"
        if ($packageArgs['fileType'] -eq 'MSI') {
            $packageArgs['silentArgs'] = "$($_.PSChildName) $($packageArgs['silentArgs'])"
            $packageArgs['file'] = ''
        }

        Uninstall-ChocolateyPackage @packageArgs
    }
}
elseif ($key.Count -eq 0) {
    Write-Warning "$env:ChocolateyPackageName has already been uninstalled by other means."
}
elseif ($key.Count -gt 1) {
    Write-Warning "$key.Count matches found!"
    Write-Warning "To prevent accidental data loss, no programs will be uninstalled."
    Write-Warning "Please alert package maintainer the following keys were matched:"
    $key | ForEach-Object {
        Write-Warning "- $_.DisplayName"
    }
}
