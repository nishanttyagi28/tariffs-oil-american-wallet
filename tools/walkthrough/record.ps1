# Record the VS Code "every file" walkthrough, one MP4 per part, from tools/walkthrough/plan.json.
# Captures only the top 1600x856 of the screen (no taskbar). Toasts are disabled while recording and restored after.
# Usage: powershell -File tools\walkthrough\record.ps1 -Parts 1,2,3,4,5 [-ZoomSteps 2]
param([int[]]$Parts = @(1, 2, 3, 4, 5), [int]$ZoomSteps = 2, [string]$RawDir = "")
$Repo = (Resolve-Path "$PSScriptRoot\..\..").Path
if (-not $RawDir) { $RawDir = Join-Path $Repo ".scratch" }
New-Item -ItemType Directory -Force $RawDir | Out-Null
Add-Type -AssemblyName System.Windows.Forms
if (-not ('WtWin' -as [type])) {
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public static class WtWin {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  public static IntPtr Find(string part) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, p) => { if (!IsWindowVisible(h)) return true; var sb = new StringBuilder(512); GetWindowText(h, sb, 512);
      if (sb.ToString().Contains(part)) { found = h; return false; } return true; }, IntPtr.Zero);
    return found;
  }
}
"@
}
function Keys([string]$k) { [System.Windows.Forms.SendKeys]::SendWait($k) }
function Esc-Send([string]$s) { ($s.ToCharArray() | ForEach-Object { if ('+^%~(){}[]'.Contains($_)) { "{$_}" } else { "$_" } }) -join '' }
function Focus-Code {
  $h = [WtWin]::Find('da-flagship - Visual Studio Code')
  if ($h -eq [IntPtr]::Zero) { throw "VS Code window for da-flagship not found" }
  # Alt tap lets SetForegroundWindow succeed from a background process
  [WtWin]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [WtWin]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
  [void][WtWin]::ShowWindow($h, 3); [void][WtWin]::SetForegroundWindow($h); Start-Sleep -Milliseconds 400
  return $h
}
function Open-File([string]$rel) {
  Keys '^p'; Start-Sleep -Milliseconds 350
  Keys (Esc-Send $rel); Start-Sleep -Milliseconds 1500
  Keys '{ENTER}'
}

$plan = Get-Content (Join-Path $PSScriptRoot 'plan.json') -Raw | ConvertFrom-Json
$titles = @{ 1 = 'Overview, config, ingest, dbt staging & intermediate'; 2 = 'dbt marts, ml sources, dbt tests, seeds';
             3 = 'SQL analyses and the ML layer'; 4 = 'Power BI generator, helper scripts and the TMDL semantic model';
             5 = 'PBIR report definition, Python tests, tools and docs' }

# temporary workspace settings for a clean, smooth walkthrough (removed afterwards)
$vsdir = Join-Path $Repo '.vscode'; $vsfile = Join-Path $vsdir 'settings.json'; $hadVs = Test-Path $vsfile
if (-not $hadVs) {
  New-Item -ItemType Directory -Force $vsdir | Out-Null
  '{ "editor.smoothScrolling": true, "workbench.list.smoothScrolling": true, "explorer.autoReveal": true, "workbench.editor.enablePreviewFromQuickOpen": true, "workbench.editor.limit.enabled": true, "workbench.editor.limit.value": 3, "workbench.startupEditor": "none", "editor.renderWhitespace": "none", "extensions.ignoreRecommendations": true, "workbench.tips.enabled": false, "python.experiments.enabled": false }' |
    Set-Content -Encoding ascii $vsfile
}
$notifKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings'
$prevToasts = (Get-ItemProperty $notifKey -ErrorAction SilentlyContinue).NOC_GLOBAL_SETTING_TOASTS_ENABLED
Set-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value 0 -Type DWord
$log = @()
try {
  (New-Object -ComObject Shell.Application).MinimizeAll(); Start-Sleep 2
  & code $Repo (Join-Path $Repo 'README.md') 2>&1 | Out-Null; Start-Sleep 5
  $h = Focus-Code; Keys '{ESC}'; Start-Sleep -Milliseconds 500
  Keys '^k'; Keys 'w'; Start-Sleep 1                       # close all editors
  for ($i = 0; $i -lt $ZoomSteps; $i++) { Keys '^='; Start-Sleep -Milliseconds 400 }
  Keys '^+p'; Start-Sleep -Milliseconds 500; Keys 'Notifications: Clear All Notifications'; Start-Sleep 1; Keys '{ENTER}'; Start-Sleep 1
  Keys '^+e'; Start-Sleep 1                                 # Explorer visible
  [void][WtWin]::SetCursorPos(1599, 899)
  foreach ($part in $Parts) {
    $items = @($plan | Where-Object { $_.part -eq $part })
    if (-not $items) { continue }
    $raw = Join-Path $RawDir ("wt_part{0}_raw.mp4" -f $part)
    $h = Focus-Code; Keys '{ESC}'
    Keys '^+p'; Start-Sleep -Milliseconds 500; Keys 'Notifications: Clear All Notifications'; Start-Sleep 1; Keys '{ENTER}'; Start-Sleep 1
    Open-File $items[0].path; Start-Sleep 2                # first file is on screen when recording starts
    $psi = New-Object System.Diagnostics.ProcessStartInfo 'ffmpeg'
    $psi.Arguments = "-y -hide_banner -loglevel error -f gdigrab -framerate 15 -offset_x 0 -offset_y 0 -video_size 1600x856 -draw_mouse 0 -i desktop -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p `"$raw`""
    $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.CreateNoWindow = $true
    $ff = [System.Diagnostics.Process]::Start($psi); $sw = [System.Diagnostics.Stopwatch]::StartNew(); Start-Sleep -Milliseconds 800
    $first = $true
    foreach ($it in $items) {
      if (-not $first) { Open-File $it.path }
      $t = [Math]::Max(0, $sw.Elapsed.TotalSeconds - 0.6)
      $log += [pscustomobject]@{ part = $part; t = [Math]::Round($t, 1); path = $it.path; note = $it.note }
      Start-Sleep -Milliseconds $(if ($first) { 2500 } else { 1900 }); $first = $false
      for ($k = 0; $k -lt $it.pgdn; $k++) { Keys '{PGDN}'; Start-Sleep -Milliseconds 1200 }
    }
    Start-Sleep 1
    $ff.StandardInput.Write('q'); $ff.StandardInput.Close(); $ff.WaitForExit(60000) | Out-Null
    Write-Output ("part {0}: {1} files, {2:N0}s -> {3}" -f $part, $items.Count, $sw.Elapsed.TotalSeconds, $raw)
  }
} finally {
  if ($null -eq $prevToasts) { Remove-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -ErrorAction SilentlyContinue }
  else { Set-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value $prevToasts -Type DWord }
  try { $null = Focus-Code; for ($i = 0; $i -lt $ZoomSteps; $i++) { Keys '^-'; Start-Sleep -Milliseconds 300 } } catch { }
  if (-not $hadVs) { Remove-Item -Recurse -Force $vsdir -ErrorAction SilentlyContinue }
  $logPath = Join-Path $RawDir ("wt_log_{0}.json" -f ($Parts -join ''))
  $log | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 $logPath
  Write-Output "log: $logPath"
}