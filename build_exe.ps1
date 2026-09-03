param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$mode = if ($OneFile) { "--onefile" } else { "--onedir" }

$args = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    $mode,
    "--name", "mh_helper",
    "--add-data", "img_templates;img_templates",
    "--add-data", "qiyuan_table.json;.",
    "--hidden-import", "pygetwindow",
    "--hidden-import", "win32gui",
    "--hidden-import", "win32con",
    "--hidden-import", "pynput.keyboard._win32",
    "--hidden-import", "pynput.mouse._win32",
    "state_machine.py"
)

Write-Host "Running: pyinstaller $($args -join ' ')"
pyinstaller @args
