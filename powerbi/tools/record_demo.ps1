# Record the demo: VS Code tour of the repo, then a walk through the 7 Power BI pages.
# Needs Power BI Desktop already open on TradeWar.pbip (data loaded, side panes collapsed) and VS Code on this folder.
# Usage: powershell -File powerbi\tools\record_demo.ps1 -Out E:\da-flagship\.scratch\demo_raw.mp4
param([string]$Out = "E:\da-flagship\.scratch\demo_raw.mp4", [int]$Fps = 15, [switch]$PrepOnly)
. "$PSScriptRoot\pbi_gui.ps1"
$Repo = (Resolve-Path "$PSScriptRoot\..\..").Path
if (-not ('DemoWin' -as [type])) {
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public static class DemoWin {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  public static IntPtr Find(string part) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, p) => { if (!IsWindowVisible(h)) return true; var sb = new StringBuilder(512); GetWindowText(h, sb, 512);
      if (sb.ToString().Contains(part)) { found = h; return false; } return true; }, IntPtr.Zero);
    return found;
  }
}
"@
}

function Move-Smooth([int]$x, [int]$y, [int]$ms = 700) {
  $p = [System.Windows.Forms.Cursor]::Position; $n = [Math]::Max(8, [int]($ms / 16))
  for ($i = 1; $i -le $n; $i++) {
    $t = $i / $n; $e = $t * $t * (3 - 2 * $t)
    [void][PbiUser32]::SetCursorPos([int]($p.X + ($x - $p.X) * $e), [int]($p.Y + ($y - $p.Y) * $e)); Start-Sleep -Milliseconds 16
  }
}
function Click-Smooth([int]$x, [int]$y) { Move-Smooth $x $y; Start-Sleep -Milliseconds 150; [PbiUser32]::mouse_event(2,0,0,0,0); [PbiUser32]::mouse_event(4,0,0,0,0) }
function Tab-Center([string]$Display) {
  $root = [System.Windows.Automation.AutomationElement]::FromHandle((Get-PbiProc).MainWindowHandle)
  $c1 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $Display)
  $c2 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TabItem)
  $r = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.AndCondition($c1, $c2))).Current.BoundingRectangle
  return @([int]($r.X + $r.Width / 2), [int]($r.Y + $r.Height / 2))
}
function Open-InCode([string]$rel) { & code $Repo (Join-Path $Repo $rel) 2>&1 | Out-Null }

# ---------------------------------------------------------------- prepare (not recorded)
$notifKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings'
$prevToasts = (Get-ItemProperty $notifKey -ErrorAction SilentlyContinue).NOC_GLOBAL_SETTING_TOASTS_ENABLED
Set-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value 0 -Type DWord
$shell = New-Object -ComObject Shell.Application
$shell.MinimizeAll(); Start-Sleep 2
Show-Pbi | Out-Null
$t = Tab-Center 'Executive Summary'; Click-At $t[0] $t[1]; Start-Sleep 3
$files = 'README.md', 'dbt\models\marts\powerbi\mart_country_before_after.sql', 'sql\analysis\06_partner_rank_shift_before_after.sql',
         'ml\trade_counterfactual.py', 'powerbi\pbi_measures.py', 'docs\ml_report.md'
Open-InCode $files[0]; Start-Sleep 4
$vs = [DemoWin]::Find('da-flagship - Visual Studio Code')
if ($vs -ne [IntPtr]::Zero) { [void][PbiUser32]::ShowWindow($vs, 3); [void][PbiUser32]::SetForegroundWindow($vs) }
Start-Sleep 1; [System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep 1
[System.Windows.Forms.SendKeys]::SendWait('^k'); [System.Windows.Forms.SendKeys]::SendWait('w'); Start-Sleep 1   # close all editors
foreach ($f in $files) { Open-InCode $f; Start-Sleep 2 }
[System.Windows.Forms.SendKeys]::SendWait('{ESC}'); Start-Sleep 1
for ($i = 1; $i -lt $files.Count; $i++) { [System.Windows.Forms.SendKeys]::SendWait('^{PGUP}'); Start-Sleep -Milliseconds 300 }
[void][PbiUser32]::SetCursorPos(1560, 600); Start-Sleep 2
if ($PrepOnly) { Save-Screen "$env:USERPROFILE\da-stage\prep.png"; return }

# ---------------------------------------------------------------- record
$psi = New-Object System.Diagnostics.ProcessStartInfo 'ffmpeg'
$psi.Arguments = "-y -hide_banner -loglevel error -f gdigrab -framerate $Fps -offset_x 0 -offset_y 0 -video_size 1600x856 -draw_mouse 1 -i desktop -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p `"$Out`""
$psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.CreateNoWindow = $true
$ff = [System.Diagnostics.Process]::Start($psi); Start-Sleep 2

# VS Code: README (architecture), SQL mart, analysis query, ML code, DAX-as-code, ML report
Start-Sleep 4
for ($i = 1; $i -lt $files.Count; $i++) { [System.Windows.Forms.SendKeys]::SendWait('^{PGDN}'); Start-Sleep 3 }
# Power BI: bring Desktop up by minimizing VS Code
[void][PbiUser32]::ShowWindow($vs, 6); Start-Sleep 1
Move-Smooth 1430 480 600
$pages = 'Executive Summary', 'Global Trade Map', 'Country Deep-Dive', 'Household Economy', 'Iran War & Oil Shock', 'Global Markets Reaction', 'Forecast & Scenarios'
$first = $true
foreach ($pg in $pages) {
  $t = Tab-Center $pg; Click-Smooth $t[0] $t[1]; Start-Sleep -Milliseconds 400; Move-Smooth 1430 480 700
  if ($first) { Start-Sleep 5; $first = $false; continue }
  if ($pg -eq 'Global Trade Map') {
    Start-Sleep 5; Move-Smooth 625 426 1000; Start-Sleep 4; Move-Smooth 600 432 600; Start-Sleep 3; Move-Smooth 1430 480 900; Start-Sleep 2
  } else { Start-Sleep 8 }
}
Start-Sleep 2

# ---------------------------------------------------------------- stop + restore
$ff.StandardInput.Write('q'); $ff.StandardInput.Close(); $ff.WaitForExit(30000) | Out-Null
if ($null -eq $prevToasts) { Remove-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -ErrorAction SilentlyContinue }
else { Set-ItemProperty $notifKey -Name NOC_GLOBAL_SETTING_TOASTS_ENABLED -Value $prevToasts -Type DWord }
Write-Output "recorded $Out ($([Math]::Round((Get-Item $Out).Length / 1MB, 1)) MB)"
