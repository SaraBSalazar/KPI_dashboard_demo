# Re-export the read-only KPI snapshot and republish it to its existing shared link.
#
# Run by the "KPI snapshot publish" Windows scheduled task (see HOW_TO_RUN.md), or by hand:
#     powershell -ExecutionPolicy Bypass -File publish_snapshot.ps1
#
# Steps: export the HTML from the live Excel/CSV files, then ask Claude Code (headless) to
# republish it to -ArtifactUrl so the link people already have shows the new data. If any
# data file is locked (open in Excel / mid-OneDrive-sync) the exporter exits 2 and this
# script stops without publishing -- the next scheduled run picks it up instead.
#
# Everything is appended to -LogFile next to this script.
#
# All machine- and person-specific paths are parameters -- there are no sensible defaults
# to ship in a public repo, so fill in your own before running this (or pass them on the
# command line every time):
#   powershell -File publish_snapshot.ps1 -ArtifactUrl "https://claude.ai/code/artifact/..." `
#       -Python "C:\path\to\python.exe" -ClaudeExe "C:\path\to\claude.exe"
param(
    [string]$Python      = "C:\path\to\your\python.exe",
    [string]$ClaudeExe   = (Join-Path $env:USERPROFILE ".local\bin\claude.exe"),
    [string]$ArtifactUrl = "",  # the existing artifact link to republish to -- see HOW_TO_RUN.md
    [string]$LogFile     = $null  # defaults to publish_snapshot.log next to this script
)

# Not "Stop": in Windows PowerShell 5.1 a native command writing to stderr under
# $ErrorActionPreference="Stop" raises NativeCommandError and kills the script, even on a
# clean exit code. Exit codes are checked explicitly below instead.
$ErrorActionPreference = "Continue"

$DashboardDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# The Claude CLI must run from the repo root: it is the trusted workspace, and running it
# from a subfolder instead makes every tool call (the publish included) stall on a trust
# prompt that a non-interactive session can never answer.
$RepoRoot     = Split-Path -Parent (Split-Path -Parent $DashboardDir)
$SnapshotFile = Join-Path (Split-Path -Parent $DashboardDir) "Share\_artifact_snapshot.html"
if (-not $LogFile) { $LogFile = Join-Path $DashboardDir "publish_snapshot.log" }

function Write-Log($message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    # Write-Host, not Write-Output: anything written to the output stream inside a function
    # is returned by that function, so a caller expecting an exit code would get an array of
    # log lines instead and misread every result.
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Invoke-Captured($exe, $argList, $workDir) {
    <#  Run a native command and return @{ Code; Out; Err }. Start-Process (rather than a
        bare call with 2>&1) keeps PowerShell 5.1 from turning ordinary stderr output into a
        terminating NativeCommandError.  #>
    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()
    try {
        $proc = Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $workDir `
            -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        return @{
            Code = $proc.ExitCode
            Out  = (Get-Content $outFile -Raw -Encoding utf8)
            Err  = (Get-Content $errFile -Raw -Encoding utf8)
        }
    } finally {
        Remove-Item $outFile, $errFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Log "--- snapshot publish started ---"

if (-not $ArtifactUrl)           { Write-Log "ABORT: -ArtifactUrl was not set. Pass the artifact link to republish to."; exit 1 }
if (-not (Test-Path $Python))    { Write-Log "ABORT: python not found at $Python"; exit 1 }
if (-not (Test-Path $ClaudeExe)) { Write-Log "ABORT: claude CLI not found at $ClaudeExe"; exit 1 }

# 1. Export -----------------------------------------------------------------------------------
$export = Invoke-Captured $Python @("export_snapshot.py") $DashboardDir
foreach ($stream in @($export.Out, $export.Err)) {
    if ($stream) { $stream.TrimEnd() -split "`r?`n" | ForEach-Object { Write-Log "  export: $_" } }
}

if ($export.Code -eq 2) {
    Write-Log "SKIPPED: a data file was locked. Nothing published; will retry next run."
    exit 0
}
if ($export.Code -ne 0) {
    Write-Log "ABORT: export failed (exit $($export.Code)). Nothing published."
    exit 1
}
if (-not (Test-Path $SnapshotFile)) {
    Write-Log "ABORT: expected $SnapshotFile after export, but it is missing."
    exit 1
}

# 2. Republish to the existing artifact link ----------------------------------------------------
# The file is already built, so the headless session only needs the Artifact tool: one call,
# passing `url` so it updates that artifact in place instead of creating a new link.
$prompt = @'
Publish an already-built HTML file as an artifact, updating an EXISTING artifact so its link keeps working.

file_path: {0}
url: {1}

Call the Artifact tool exactly once with that file_path and url, and set favicon to the bar-chart emoji. The file is complete already: do not read, edit, rebuild or review it, and do not call any other tool.
'@ -f $SnapshotFile, $ArtifactUrl

$artifactId = ([uri]$ArtifactUrl).Segments[-1].Trim('/')
$successPattern = "Published[\s\S]{0,500}$([regex]::Escape($artifactId))"
$published = $false

# A headless session occasionally ends without running the tool (a permission prompt it
# can't answer), so try twice before giving up -- an unattended weekly run that silently
# skips is worse than one that retries.
foreach ($attempt in 1, 2) {
    Write-Log "publishing to $ArtifactUrl (attempt $attempt of 2) ..."
    # stream-json surfaces the Artifact tool's own result, which is the only trustworthy
    # proof the publish happened: `claude -p` exits 0 even when it ran no tool at all.
    $publish = Invoke-Captured $ClaudeExe @(
        "-p", $prompt, "--allowed-tools", "Artifact", "--permission-mode", "acceptEdits",
        "--output-format", "stream-json", "--verbose"
    ) $RepoRoot

    # Log the session's closing message rather than the whole JSON stream.
    foreach ($line in ($publish.Out -split "`r?`n")) {
        if (-not $line.Trim()) { continue }
        try { $obj = $line | ConvertFrom-Json } catch { continue }
        if ($obj.type -eq "result" -and $obj.result) {
            $obj.result.TrimEnd() -split "`r?`n" | ForEach-Object { Write-Log "  claude: $_" }
        }
    }
    if ($publish.Err) { $publish.Err.TrimEnd() -split "`r?`n" | ForEach-Object { Write-Log "  claude(err): $_" } }

    if ($publish.Code -eq 0 -and ($publish.Out -match $successPattern)) {
        $published = $true
        break
    }
    Write-Log "  attempt $attempt did not publish (claude exit $($publish.Code))."
    if ($attempt -lt 2) { Start-Sleep -Seconds 20 }
}

if (-not $published) {
    Write-Log ("ABORT: both attempts ended without publishing (no Artifact result for $artifactId) -- " +
               "usually a permission prompt a non-interactive run can't answer. The exported file on " +
               "disk IS up to date; publish it from an interactive Claude session, or just run this " +
               "script again.")
    exit 1
}

Write-Log "--- snapshot publish finished OK (artifact updated) ---"
exit 0
