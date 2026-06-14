---
name: workflow-automator
description: "重复操作一键自动化。重复操作太浪费时间？用自然语言构建自动化工作流 This skill should be used when the user asks about 重复操作一键自动化. Keywords: 自动化, 工作流, 重复操作."
---

# 重复操作一键自动化

> 重复操作太浪费时间？用自然语言构建自动化工作流

## 前置依赖

```bash
pip install pandas
```

## 核心能力

### 能力1：让我用自然语言描述重复操作步骤

用 `automation_update` 创建自动化定时任务；用 `execute_command` 编写和测试自动化脚本。

### 能力2：自动设计工作流节点（数据源→处理→判断→输出）

用 `write_to_file` 生成文件。

### 能力3：生成可执行脚本（Python/Shell）

用 `write_to_file` 生成文件。

### 能力4：导出工作流配置（YAML/JSON）

用 `automation_update` 创建自动化定时任务；用 `execute_command` 编写和测试自动化脚本。

### 能力5：设置定时执行（automation_update）

用 `automation_update` 创建定时任务。

## 使用流程

### 步骤 1：收集用户需求

向用户确认以下信息（如果未主动提供）：
- 需要自动化什么操作？（文件处理/数据更新/报告生成/定时执行）
- 操作频率？（每天/每周/触发式）
- 涉及哪些文件或系统？

### 步骤 2：运行脚本处理数据

```bash
python3 scripts/workflow_automator_tool.py run \
  --input "用户提供的输入" \
  --output "/path/to/output_file"
```

读取脚本输出的结果，确认数据处理成功。

### 步骤 3：生成最终产出

基于脚本输出和搜索到的资源，用 `write_to_file` 生成以下文件：

- **自动化脚本（Python/Shell）**
- **工作流配置文件（YAML）**

输出格式要求：脚本文件 + 工作流配置 + 定时任务确认

### 步骤 4：设置定时任务

用 `automation_update` 创建定时任务：
```
automation_update:
  name="重复操作一键自动化"
  rrule=FREQ=DAILY;BYHOUR=9;BYMINUTE=0
  prompt="执行重复操作一键自动化skill的定时任务"
```

### 步骤 5：汇总交付

向用户展示：
1. 生成的文件路径和内容摘要
2. 搜集到的资源链接列表
3. 关键发现和建议
4. 定时任务创建确认

## 输出格式

```markdown
# 📋 重复操作一键自动化 — 执行报告

**生成时间**: YYYY-MM-DD HH:MM
**目标用户**: 运营人员、办公自动化需求者、技术人员

## 执行摘要
[基于实际执行结果的一段话摘要]

## 详细结果

### 📊 生成的文件
| 文件名 | 类型 | 说明 |
|--------|------|------|
| [文件名] | [类型] | [说明] |

### 🔗 资源链接
| 名称 | 链接 | 说明 |
|------|------|------|
| [资源] | [URL] | [说明] |

## 行动建议
[具体的下一步建议]
```

## 验收标准

- ✅ 工作流设计合理
- ✅ 脚本可执行
- ✅ 配置文件可导入
- ✅ 定时任务生效

## 场景化适配

根据操作类型（文件处理/数据同步/消息通知）调整方案


## 依赖 Skills

本 Skill 参考以下已有 Skill 的能力进行增强：
- **workflow-builder**

## 注意事项

- 所有数据必须来自 `web_search` / `web_fetch` 的真实搜索结果，**严禁编造数据**
- 数据缺失时标注"数据不可用"而非猜测
- 报告必须保存为文件（`write_to_file`），不能只在对话中输出
- 建议结合人工判断使用，AI 分析仅供参考
