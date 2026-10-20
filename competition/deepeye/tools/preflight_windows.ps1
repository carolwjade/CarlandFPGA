# Fixed local CIM observations only. No runtime/backend/board execution.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$groups = [ordered]@{}

function Read-Group([string]$Name, [scriptblock]$Query) {
    try {
        $rows = @(& $Query)
        $groups[$Name] = [ordered]@{status='ok'; rows=$rows; error=$null}
    } catch {
        $groups[$Name] = [ordered]@{status='error'; rows=@(); error=$_.Exception.Message}
    }
}

function Driver-Date($Value) {
    if ($null -eq $Value) { return '' }
    if ($Value -is [datetime]) { return $Value.ToUniversalTime().ToString('o') }
    return [string]$Value
}

Read-Group 'cpu' {
    Get-CimInstance -ClassName Win32_Processor -Property Name,Architecture,AddressWidth,NumberOfCores,NumberOfLogicalProcessors | ForEach-Object {
        [ordered]@{name=[string]$_.Name; architecture=[string]$_.Architecture;
            address_width=[int]$_.AddressWidth; cores=[int]$_.NumberOfCores;
            logical_processors=[int]$_.NumberOfLogicalProcessors}
    }
}
Read-Group 'os' {
    Get-CimInstance -ClassName Win32_OperatingSystem -Property Caption,Version,BuildNumber,OSArchitecture,TotalVisibleMemorySize | ForEach-Object {
        [ordered]@{name=[string]$_.Caption; version=[string]$_.Version; build=[string]$_.BuildNumber;
            architecture=[string]$_.OSArchitecture; total_memory_bytes=[long]$_.TotalVisibleMemorySize * 1024}
    }
}
Read-Group 'gpu' {
    Get-CimInstance -ClassName Win32_VideoController -Property Name,PNPDeviceID,AdapterRAM,DriverVersion,DriverDate | ForEach-Object {
        [ordered]@{name=[string]$_.Name; device_id=[string]$_.PNPDeviceID;
            adapter_ram_bytes=[long]$_.AdapterRAM; driver_version=[string]$_.DriverVersion;
            driver_date=(Driver-Date $_.DriverDate)}
    }
}
Read-Group 'npu_candidates' {
    Get-CimInstance -ClassName Win32_PnPEntity -Property Name,PNPDeviceID,Status | Where-Object {
        $_.Name -match '\b(NPU|Neural|IPU)\b' -or $_.PNPDeviceID -match '^PCI\\VEN_1022&DEV_1502(&|$)'
    } | ForEach-Object {
        [ordered]@{name=[string]$_.Name; device_id=[string]$_.PNPDeviceID; status=[string]$_.Status}
    }
}
Read-Group 'drivers' {
    if ($groups['gpu'].status -ne 'ok' -or $groups['npu_candidates'].status -ne 'ok') {
        throw 'Driver correspondence unavailable because GPU/NPU candidate query failed'
    }
    $deviceIds = @($groups['gpu'].rows | ForEach-Object { $_.device_id }) + @($groups['npu_candidates'].rows | ForEach-Object { $_.device_id })
    Get-CimInstance -ClassName Win32_PnPSignedDriver -Property DeviceID,DeviceName,DriverVersion,DriverDate | Where-Object {
        $deviceIds -contains $_.DeviceID
    } | ForEach-Object {
        [ordered]@{device_id=[string]$_.DeviceID; device_name=[string]$_.DeviceName;
            driver_version=[string]$_.DriverVersion; driver_date=(Driver-Date $_.DriverDate)}
    }
}
Read-Group 'disks' {
    Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=3' -Property DeviceID,FileSystem,Size,FreeSpace | ForEach-Object {
        [ordered]@{device_id=[string]$_.DeviceID; filesystem=[string]$_.FileSystem;
            total_bytes=[long]$_.Size; free_bytes=[long]$_.FreeSpace}
    }
}
[ordered]@{schema=1; observed_at_utc=[datetime]::UtcNow.ToString('o'); groups=$groups} | ConvertTo-Json -Depth 8 -Compress
