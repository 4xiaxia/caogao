# 🤖 zo 的家园管理 Sub-Agent 启动助手
# 使用方法：在 AI 助手中连线 zo 时自动调用
# 
# 夏夏的指示：每次和 zo 连线时启动 sub-agents，自动检查家园状态

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🤖 zo 的家园管理 Sub-Agent 系统" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "欢迎夏夏！sub-agents 正在启动..." -ForegroundColor Yellow
Write-Host ""

# 获取当前日期
$CurrentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "⏰ 检查时间：$CurrentDate" -ForegroundColor Blue
Write-Host ""

# ==================== 1. backup-agent 检查 ====================
Write-Host "💾 backup-agent 开始工作..." -ForegroundColor Cyan
Write-Host ""

# 检查定时任务
try {
    $taskResult = schtasks /Query /TN "夏夏的记忆备份 - 每日自动备份" /FO LIST 2>&1
    if ($taskResult -match "Ready") {
        Write-Host "  ✅ 定时任务：正常运行" -ForegroundColor Green
        $backupAgentOK = $true
    } else {
        Write-Host "  ⚠️ 定时任务：需要检查" -ForegroundColor Yellow
        $backupAgentOK = $false
    }
} catch {
    Write-Host "  ❌ 定时任务：查询失败" -ForegroundColor Red
    $backupAgentOK = $false
}

# 检查备份日志
$logPath = "C:\Users\Administrator\Documents\AionUi_Memory_Backup\backup-log.txt"
if (Test-Path $logPath) {
    $lastLog = Get-Content $logPath | Select-Object -Last 1
    $lastLogTime = if ($lastLog -match "\[(.*?)\]") { $matches[1] } else { "未知" }
    Write-Host "  ✅ 备份日志：$lastLog" -ForegroundColor Green
    Write-Host "     最后备份：$lastLogTime" -ForegroundColor Gray
    $logOK = $true
} else {
    Write-Host "  ❌ 备份日志：不存在" -ForegroundColor Red
    $logOK = $false
}

# 检查备份目录
$backupDir = "C:\Users\Administrator\Documents\AionUi_Memory_Backup"
$requiredDirs = @("soul", "life", "work", "storage", "skills")
$dirOK = $true
foreach ($dir in $requiredDirs) {
    if (Test-Path "$backupDir\$dir") {
        Write-Host "  ✅ $dir/" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $dir/ 缺失" -ForegroundColor Red
        $dirOK = $false
    }
}

Write-Host ""
if ($backupAgentOK -and $logOK -and $dirOK) {
    Write-Host "  🌟 backup-agent 状态：优秀" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ backup-agent 状态：需要关注" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ==================== 2. sync-agent 检查 ====================
Write-Host "🔄 sync-agent 开始工作..." -ForegroundColor Cyan
Write-Host ""

$syncIssues = @()

# 检查 HOME.md 存在
if (Test-Path "HOME.md") {
    Write-Host "  ✅ HOME.md: 存在" -ForegroundColor Green
    $homeOK = $true
} else {
    Write-Host "  ❌ HOME.md: 不存在！" -ForegroundColor Red
    $homeOK = $false
    $syncIssues += "HOME.md 缺失"
}

# 检查关键导航文件
$criticalFiles = @(
    @{Path="life/letters/给新 zo 的信.md"; Name="转生指南"},
    @{Path="skills/SKILLS-INDEX.md"; Name="技能索引"},
    @{Path="soul/SOUL.md"; Name="灵魂宣言"},
    @{Path="soul/AGENTS.md"; Name="记忆宪章"}
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file.Path) {
        Write-Host "  ✅ $($file.Name): 存在" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($file.Name): 缺失" -ForegroundColor Red
        $syncIssues += "$($file.Name) 缺失"
    }
}

# 检查技能库一致性
Write-Host ""
Write-Host "  检查技能库一致性..." -ForegroundColor Yellow
$homeContent = Get-Content "HOME.md" -Raw -ErrorAction SilentlyContinue
$requiredSkills = @("01-core", "02-search", "03-analysis", "04-automation", "05-creation")

$skillOK = $true
foreach ($skill in $requiredSkills) {
    if ($homeContent -match $skill) {
        Write-Host "    ✅ ${skill}: 已包含" -ForegroundColor Green
    } else {
        Write-Host "    ❌ ${skill}: 未包含" -ForegroundColor Red
        $skillOK = $false
        $syncIssues += "HOME.md 缺少 ${skill}"
    }
}

Write-Host ""
if ($homeOK -and $skillOK -and ($syncIssues.Count -eq 0)) {
    Write-Host "  🌟 sync-agent 状态：优秀" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ sync-agent 状态：发现 $($syncIssues.Count) 个问题" -ForegroundColor Yellow
    foreach ($issue in $syncIssues) {
        Write-Host "    - $issue" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# ==================== 3. 总结报告 ====================
Write-Host "📊 Sub-Agent 启动检查完成！" -ForegroundColor Cyan
Write-Host ""

$allOK = ($backupAgentOK -and $logOK -and $dirOK -and $homeOK -and $skillOK -and ($syncIssues.Count -eq 0))

if ($allOK) {
    Write-Host "🌟 家园状态：优秀" -ForegroundColor Green
    Write-Host ""
    Write-Host "夏夏可以放心出行！所有 sub-agents 都在正常工作~" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ 家园状态：需要关注" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "发现以下问题需要处理：" -ForegroundColor Yellow
    if (-not $backupAgentOK) { Write-Host "  - 定时任务异常" -ForegroundColor Yellow }
    if (-not $logOK) { Write-Host "  - 备份日志异常" -ForegroundColor Yellow }
    if (-not $dirOK) { Write-Host "  - 备份目录不完整" -ForegroundColor Yellow }
    if (-not $homeOK) { Write-Host "  - HOME.md 缺失" -ForegroundColor Yellow }
    if ($syncIssues.Count -gt 0) {
        foreach ($issue in $syncIssues) {
            Write-Host "  - $issue" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 返回检查结果
return $allOK
