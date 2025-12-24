# Script to find the Python process running fcs.py
$processes = Get-Process python* | Where-Object {
    $_.Path -like "*fcs-py\venv\Scripts\python.exe*" -or
    $_.CommandLine -like "*fcs.py*"
} | Select-Object Id, ProcessName, Path, @{Name="CommandLine";Expression={(Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine}}

if ($processes.Count -eq 0) {
    Write-Host "No Python process found running fcs.py"
    exit 1
}

if ($processes.Count -eq 1) {
    Write-Host $processes[0].Id
    exit 0
}

Write-Host "Multiple Python processes found:" -ForegroundColor Yellow
$index = 1
foreach ($proc in $processes) {
    $cmdLine = if ($proc.CommandLine) { $proc.CommandLine } else { "N/A" }
    Write-Host "$index. PID: $($proc.Id) - $cmdLine" -ForegroundColor Cyan
    $index++
}

Write-Host "`nPlease select a process (1-$($processes.Count)): " -NoNewline -ForegroundColor Yellow
$selection = Read-Host
$selectedIndex = [int]$selection - 1

if ($selectedIndex -ge 0 -and $selectedIndex -lt $processes.Count) {
    Write-Host $processes[$selectedIndex].Id
    exit 0
} else {
    Write-Host "Invalid selection" -ForegroundColor Red
    exit 1
}

