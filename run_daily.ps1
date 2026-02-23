# 毎朝 Pharma Daily Brief を送信する PowerShell スクリプト
# このスクリプトを Windows タスクスケジューラから毎朝実行してください

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Python のパス（必要に応じて変更）
$python = "python"

& $python send_brief.py
