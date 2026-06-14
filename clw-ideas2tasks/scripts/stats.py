#!/usr/bin/env python3
"""
stats.py - 效能數據與速率分析
分析任務完成趨勢，計算週期時間，生成燃盡圖
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import re

# 加入目前路徑以導入 state_sync
sys.path.insert(0, str(Path(__file__).parent))
from state_sync import TASKS_DIR, read_task_status, read_frontmatter_field

def parse_date(date_str: str):
    """解析日期字串為 datetime 物件"""
    if not date_str:
        return None
    # 嘗試多種格式
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def calculate_velocity_stats(days: int = 7) -> dict:
    """計算速率統計"""
    now = datetime.now()
    stats = {
        "completed_last_7_days": 0,
        "completed_last_30_days": 0,
        "cycle_times": [],
        "daily_completions": defaultdict(int),  # date -> count
        "total_analyzed": 0
    }
    
    for project_dir in sorted(TASKS_DIR.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("_"):
            continue
        tasks_dir = project_dir / "tasks"
        if not tasks_dir.exists():
            continue
        
        for task_file in sorted(tasks_dir.glob("T*.md")):
            content = task_file.read_text(encoding="utf-8", errors="replace")
            status = read_task_status(task_file)
            
            if status != "done":
                continue
            
            stats["total_analyzed"] += 1
            
            # 讀取 created 和 updated 日期
            created_str = read_frontmatter_field(content, "created")
            updated_str = read_frontmatter_field(content, "updated")
            
            created_date = parse_date(created_str)
            updated_date = parse_date(updated_str)
            
            if updated_date:
                # 計算每天完成數
                date_key = updated_date.strftime("%Y-%m-%d")
                stats["daily_completions"][date_key] += 1
                
                # 計算過去 7/30 天的完成數
                days_ago = (now - updated_date).days
                if days_ago <= 7:
                    stats["completed_last_7_days"] += 1
                if days_ago <= 30:
                    stats["completed_last_30_days"] += 1
                
                # 計算週期時間
                if created_date:
                    cycle_days = (updated_date - created_date).days
                    if cycle_days >= 0:
                        stats["cycle_times"].append(cycle_days)
    
    return stats

def generate_burndown_chart(stats: dict, days: int = 14) -> str:
    """生成 Mermaid xychart-beta 燃盡圖"""
    now = datetime.now()
    daily = stats.get("daily_completions", {})

    dates = []
    completions = []
    for i in range(days):
        date = now - timedelta(days=days-1-i)
        date_str = date.strftime("%Y-%m-%d")
        dates.append(date_str[5:])
        completions.append(daily.get(date_str, 0))

    if not completions or sum(completions) == 0:
        return "📊 數據不足以計算燃盡圖"

    x_labels = '["' + '", "'.join(dates) + '"]'
    values = "[" + ", ".join(str(c) for c in completions) + "]"

    max_val = max(max(completions), 10)

    recent_week = sum(completions[-7:])
    prev_week = sum(completions[-14:-7]) if len(completions) >= 14 else 0
    total = sum(completions)
    avg = total / len(completions) if completions else 0

    if recent_week > prev_week:
        trend = "📈 成長中"
    elif recent_week < prev_week:
        trend = "📉 下降中"
    else:
        trend = "➡️ 持平"

    chart = f"""
```mermaid
xychart-beta
    title "過去 14 天任務完成趨勢"
    x-axis {x_labels}
    y-axis "完成數" 0 --> {max_val}
    line {values}
```

📊 總計: {total} | 日均: {avg:.1f} | 本週: {recent_week} | {trend}"""

    return chart

def generate_stats_report() -> str:
    """生成完整的統計報告"""
    stats = calculate_velocity_stats()
    
    # 基本統計
    last_7 = stats.get("completed_last_7_days", 0)
    last_30 = stats.get("completed_last_30_days", 0)
    cycle_times = stats.get("cycle_times", [])
    
    # 週期時間統計
    if cycle_times:
        avg_cycle = sum(cycle_times) / len(cycle_times)
        sorted_times = sorted(cycle_times)
        mid = len(sorted_times) // 2
        median_cycle = sorted_times[mid] if len(sorted_times) % 2 == 1 else (sorted_times[mid-1] + sorted_times[mid]) / 2
    else:
        avg_cycle = median_cycle = 0
    
    # 組裝報告
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 📈 效能分析")
    lines.append("")
    lines.append(f"| 指標 | 數值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 過去 7 天完成 | {last_7} |")
    lines.append(f"| 過去 30 天完成 | {last_30} |")
    lines.append(f"| 平均週期時間 | {avg_cycle:.1f} 天 |")
    lines.append(f"| 週期時間中位數 | {median_cycle:.1f} 天 |")
    lines.append("")
    
    # 燃盡圖
    chart = generate_burndown_chart(stats)
    lines.append(chart)
    lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    report = generate_stats_report()
    print(report)