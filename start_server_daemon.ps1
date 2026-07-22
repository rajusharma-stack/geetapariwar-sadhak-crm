param([switch]$Uninstall)

$projectRoot = "C:\Users\sraj5\OneDrive\Desktop\Geetapariwarsadhak"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$logFile = Join-Path $projectRoot "server_daemon.log"
$lockFile = "$env:TEMP\geetapariwar_daemon.lock"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $logFile "[$timestamp] $Message"
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $c.Connect('127.0.0.1', $Port)
        $c.Close()
        return $true
    } catch {
        return $false
    }
}

if (Test-Path $lockFile) {
    $existingPid = Get-Content $lockFile
    $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existingProcess -and ($existingPid -ne $PID)) {
        Write-Log "Another daemon instance is already running (PID: $existingPid). Exiting."
        exit 0
    }
}
Set-Content $lockFile $PID

Set-Location $projectRoot
Write-Log "========================================"
Write-Log "Daemon started (PID: $PID)"
Write-Log "========================================"

while ($true) {
    if (Test-PortInUse 3201) {
        Write-Log "Port 3201 is already in use. Waiting 10 seconds..."
        Start-Sleep -Seconds 10
        continue
    }
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $pythonExe
        $psi.Arguments = '-c "from waitress import serve; from app import app; serve(app, host=''0.0.0.0'', port=3201)"'
        $psi.WorkingDirectory = $projectRoot
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        Write-Log "Server started (PID: $($proc.Id))"
        $proc.WaitForExit()
        $exitCode = $proc.ExitCode
        Write-Log "Server exited (PID: $($proc.Id), ExitCode: $exitCode)."
        if ($exitCode -eq 0) {
            Write-Log "Server stopped cleanly. Daemon exiting."
            break
        }
        Write-Log "Restarting in 5 seconds..."
        Start-Sleep -Seconds 5
    } catch {
        Write-Log "Error: $_"
        Write-Log "Retrying in 10 seconds..."
        Start-Sleep -Seconds 10
    }
}
