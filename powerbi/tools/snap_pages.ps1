# Capture every report page of the open TradeWar report in Power BI Desktop.
# Usage: powershell -File powerbi\tools\snap_pages.ps1 -OutDir docs\screenshots
param([string]$OutDir = "docs\screenshots", [int]$WaitSec = 8)
. "$PSScriptRoot\pbi_gui.ps1"
$pages = [ordered]@{
  "01_exec" = "Executive Summary"; "02_map" = "Global Trade Map"; "03_deepdive" = "Country Deep-Dive";
  "04_household" = "Household Economy"; "05_oil" = "Iran War & Oil Shock"; "06_markets" = "Global Markets Reaction";
  "07_forecast" = "Forecast & Scenarios" }
if (-not (Show-Pbi)) { throw "Power BI Desktop is not open" }
Collapse-Panes
foreach ($k in $pages.Keys) {
  $root = [System.Windows.Automation.AutomationElement]::FromHandle((Get-PbiProc).MainWindowHandle)
  $c1 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $pages[$k])
  $c2 = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::TabItem)
  $tab = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.AndCondition($c1, $c2)))
  if (-not $tab) { Write-Warning "tab not found: $($pages[$k])"; continue }
  $r = $tab.Current.BoundingRectangle
  Click-At ([int]($r.X + $r.Width / 2)) ([int]($r.Y + $r.Height / 2))
  [void][PbiUser32]::SetCursorPos(5, 450)   # park mouse so no hover tooltips
  Start-Sleep ($(if ($k -eq "02_map") { [Math]::Max($WaitSec, 45) } else { $WaitSec }))
  Save-Screen (Join-Path $OutDir "$k.png"); Write-Output "saved $k"
}

