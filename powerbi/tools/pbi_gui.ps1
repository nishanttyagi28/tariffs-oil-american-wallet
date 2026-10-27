# Helpers to drive Power BI Desktop on the interactive console session: focus/maximize, keys, clicks, screenshots.
# Usage: . .\powerbi\tools\pbi_gui.ps1 ; Show-Pbi ; Save-Screen E:\path.png
Add-Type -AssemblyName System.Windows.Forms, System.Drawing, UIAutomationClient, UIAutomationTypes
if (-not ('PbiUser32' -as [type])) {
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class PbiUser32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, int f, int e);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
}
[void][PbiUser32]::SetProcessDPIAware()

function Get-PbiProc { Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1 }

function Show-Pbi {
  $p = Get-PbiProc; if (-not $p) { return $false }
  # Alt tap lets SetForegroundWindow succeed from a background process
  [PbiUser32]::keybd_event(0x12,0,0,0); [PbiUser32]::keybd_event(0x12,0,2,0)
  [void][PbiUser32]::ShowWindow($p.MainWindowHandle, 3)
  [void][PbiUser32]::SetForegroundWindow($p.MainWindowHandle)
  Start-Sleep -Milliseconds 600; [System.Windows.Forms.SendKeys]::SendWait("{ESC}"); Start-Sleep -Milliseconds 200; return $true
}

function Save-Screen([string]$Path) {
  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
  New-Item -ItemType Directory -Force (Split-Path $Path) | Out-Null
  $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
}

function Click-At([int]$x, [int]$y) {
  [void][PbiUser32]::SetCursorPos($x, $y); Start-Sleep -Milliseconds 120
  [PbiUser32]::mouse_event(2,0,0,0,0); [PbiUser32]::mouse_event(4,0,0,0,0)
}

function Send-Keys([string]$k) { [System.Windows.Forms.SendKeys]::SendWait($k) }

function Find-Uia([string]$Name, [int]$TimeoutSec = 5) {
  $root = [System.Windows.Automation.AutomationElement]::RootElement
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $Name)
  $t = (Get-Date).AddSeconds($TimeoutSec)
  do {
    $ids = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | ForEach-Object Id)
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($w in $wins) {
      if ($ids -notcontains $w.Current.ProcessId) { continue }
      $e = $w.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
      if ($e) { return $e }
    }
    Start-Sleep -Milliseconds 500
  } while ((Get-Date) -lt $t)
  return $null
}

function Invoke-Uia([string]$Name, [int]$TimeoutSec = 5) {
  $e = Find-Uia $Name $TimeoutSec; if (-not $e) { return $false }
  try { $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); return $true }
  catch { $r = $e.Current.BoundingRectangle; Click-At ([int]($r.X + $r.Width/2)) ([int]($r.Y + $r.Height/2)); return $true }
}

function Goto-Page([string]$Display) {
  $root = [System.Windows.Automation.AutomationElement]::FromHandle((Get-PbiProc).MainWindowHandle)
  $c1 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $Display)
  $c2 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TabItem)
  $tab = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.AndCondition($c1, $c2)))
  if (-not $tab) { return $false }
  $r = $tab.Current.BoundingRectangle
  Click-At ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2))
  [void][PbiUser32]::SetCursorPos(5, 450); return $true
}

function Close-Pbi([switch]$Save) {
  $p = Get-PbiProc; if (-not $p) { return "not running" }
  if ($Save) { Show-Pbi | Out-Null; Send-Keys '^s'; Start-Sleep 8 }
  [void]$p.CloseMainWindow()
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep 2
    if (-not (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)) { return "closed" }
    $btn = if ($Save) { Find-Uia 'Save' 1 } else { Find-Uia "Don't save" 1 }
    if ($btn) { try { $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() } catch {} }
  }
  return "still running"
}

function Open-Pbi([string]$Pbip, [int]$TimeoutSec = 240) {
  Start-Process $Pbip
  $t = (Get-Date).AddSeconds($TimeoutSec)
  do { Start-Sleep 5; $p = Get-PbiProc } while ((-not $p -or $p.MainWindowTitle -notmatch 'TradeWar') -and (Get-Date) -lt $t)
  return [bool]$p
}


function Collapse-Panes {
  # collapse the Data and Visualizations side panes (report view) so the canvas gets the full width
  Show-Pbi | Out-Null
  foreach ($nm in 'Data', 'Visualizations') {
    $root = [System.Windows.Automation.AutomationElement]::FromHandle((Get-PbiProc).MainWindowHandle)
    $c1 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $nm)
    $c2 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)
    $hits = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.AndCondition($c1, $c2)))
    $btn = $hits | Where-Object { $_.Current.ClassName -match 'toggle-button' -and -not $_.Current.IsOffscreen -and $_.Current.BoundingRectangle.Y -lt 200 } |
           Sort-Object { $_.Current.BoundingRectangle.X } -Descending | Select-Object -First 1
    if ($btn) { try { $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
                catch { $r = $btn.Current.BoundingRectangle; Click-At ([int]($r.X + $r.Width/2)) ([int]($r.Y + $r.Height/2)) }
                Start-Sleep 2 }
  }
}
function Apply-External {
  Show-Pbi | Out-Null; Send-Keys '{ESC}'
  if (-not (Invoke-Uia 'Apply external changes' 10)) { return $false }
  Start-Sleep 3
  $root = [System.Windows.Automation.AutomationElement]::RootElement
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, 'Apply external changes')
  $ids = @(Get-Process PBIDesktop | ForEach-Object Id)
  foreach ($w in $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)) {
    if ($ids -notcontains $w.Current.ProcessId) { continue }
    $all = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
    $btn = $all | Where-Object { $_.Current.ClassName -notmatch 'action-button' -and $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button } | Select-Object -Last 1
    if ($btn) { $r = $btn.Current.BoundingRectangle; Click-At ([int]($r.X + $r.Width/2)) ([int]($r.Y + $r.Height/2)); Start-Sleep 20; return $true }
  }
  return $false
}


