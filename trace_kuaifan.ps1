$ErrorActionPreference = 'SilentlyContinue'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$report = Join-Path $PSScriptRoot "kuaifan_trace_$stamp.txt"

Start-Transcript -Path $report -Force

Write-Output '=== TIME ==='
Get-Date

Write-Output '=== PUBLIC IP / LOCATION ==='
try {
    Invoke-RestMethod -Uri 'https://ipinfo.io/json' -TimeoutSec 10 |
        Select-Object ip, city, region, country, org, timezone |
        Format-List
} catch {
    Write-Output "Public IP check failed: $($_.Exception.Message)"
}

Write-Output '=== ACTIVE ADAPTERS ==='
Get-NetAdapter |
    Where-Object Status -eq 'Up' |
    Select-Object ifIndex, Name, InterfaceDescription, LinkSpeed |
    Format-Table -AutoSize

Write-Output '=== DEFAULT ROUTES ==='
Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' |
    Sort-Object { $_.RouteMetric + $_.InterfaceMetric } |
    Select-Object InterfaceAlias, NextHop, RouteMetric, InterfaceMetric |
    Format-Table -AutoSize

Write-Output '=== KUAIFAN DRIVER ==='
Get-CimInstance Win32_SystemDriver |
    Where-Object { $_.Name -eq 'speedinkf' -or $_.PathName -match 'speedin' } |
    Select-Object Name, State, StartMode, PathName |
    Format-List

Write-Output '=== GAME PROCESSES ==='
$games = Get-Process -Name MyGame_x64r -ErrorAction SilentlyContinue
$gamePids = @($games.Id)
$games |
    Select-Object Id, StartTime, MainWindowTitle |
    Format-Table -AutoSize

Write-Output '=== GAME TCP CONNECTIONS ==='
Get-NetTCPConnection |
    Where-Object { $_.OwningProcess -in $gamePids -and $_.State -eq 'Established' } |
    Sort-Object OwningProcess, RemoteAddress, RemotePort |
    Select-Object OwningProcess, LocalAddress, LocalPort, RemoteAddress, RemotePort |
    Format-Table -AutoSize

Write-Output '=== SPEEDIN/KUAIFAN INSTALL-DIRECTORY PROCESSES ==='
Get-CimInstance Win32_Process |
    Where-Object { $_.ExecutablePath -like 'C:\Program Files\speedin\*' } |
    Select-Object Name, ProcessId, ExecutablePath, CommandLine |
    Format-List

Write-Output '=== LATENCY: ROUTER ==='
ping.exe -n 20 192.168.2.1

$targets = @('42.186.28.58', '34.84.3.45', '34.146.155.186', '34.149.125.149')
foreach ($target in $targets) {
    Write-Output "=== LATENCY: $target ==="
    ping.exe -n 20 -w 1000 $target
}

Write-Output '=== ROUTE: NETEASE 42.186.28.58 ==='
tracert.exe -d -h 20 -w 800 42.186.28.58

Write-Output '=== ROUTE: GAME SERVICE 34.84.3.45 ==='
tracert.exe -d -h 20 -w 800 34.84.3.45

Stop-Transcript
Write-Host "Report saved to: $report" -ForegroundColor Green
