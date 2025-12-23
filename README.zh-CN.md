# FinMind — FinSight 的智能层

[English](README.md) | 简体中文

让每一笔交易，都成为对自己的理解。

FinMind 是 `https://github.com/xiaxinyu/finsight` 的智能分析子系统，专注将原始交易数据转化为可行动的洞察，并保持本地隐私。

不同于一般记账应用，FinMind 结合可读的规则、轻量 NLP 与行为启发式，不仅高精度归类消费，还解释你的消费动机。

本项目完全离线运行，并作为 FinSight 的认知核心原生集成。

## ✨ 核心能力
- 混合归类引擎  
  - 规则匹配（正则、包含、金额阈值）  
  - 轻量 NLP（fastText / BERT-mini）  
  - 冲突消解与优先级  
  - 用户反馈闭环与规则自生长
- 行为画像  
  - 交易标注：必要、冲动、投资、奢侈  
  - 异常检测：如餐饮支出骤增  
  - 评估“可避免支出”比例
- 可解释洞察  
  - 示例：“本月冲动型消费 ¥1,200，占比 30%”  
  - “发薪后非必要支出显著上升”  
  - 洞察可溯源到具体交易
- 无缝集成  
  - 读取/写入 FinSight 本地数据（CSV/SQLite）  
  - 暴露 REST 风格 API  
  - 支持后台服务或按需模块

## 🛠️ 技术栈
- 语言：Python
- 核心：Pandas、scikit-learn、fastText
- NLP：jieba、HuggingFace（可选）
- 集成：本地文件或 SQLite；可选 Django
- 隐私：零网络调用，无遥测

## 🌐 与 FinSight 的关系
- 角色  
  - FinSight：数据平台  
  - FinMind：智能引擎
- 关注点  
  - FinSight：存储、UI、报表  
  - FinMind：归类、洞察、AI
- 数据流  
  - FinSight：接入并清洗银行导出  
  - FinMind：消费清洗后的数据进行智能分析
- 用户交互  
  - FinSight：看板、手动编辑  
  - FinMind：智能建议、解释说明

类比：
- FinSight = 眼睛 + 手
- FinMind = 大脑

## 🧩 项目结构
```
finmind/
├── account/                     # 规则与静态字典
│   ├── analyzer/                # 归类与业务分析
│   ├── cleaner/                 # 数据清洗器
│   ├── db/                      # SQLite 辅助
│   ├── helper/                  # 工具库
│   └── static/                  # 字典与建表脚本
├── engine/                      # Django 应用层
│   ├── views.py                 # API 入口
│   └── urls.py
├── finmind_site/                # Django 项目
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── doc/                         # 英文文档
│   ├── index.md
│   ├── api.md
│   └── architecture.md
└── manage.py
```

## 🔌 Django API
- `POST /api/classify`  
  - 请求体：`{"description": "...", "money": "100.00"}`  
  - 返回：消费类型与匹配关键词
- `POST /api/analyze`  
  - 请求体：`{"lines": [[...], ...]}`  
  - 返回：批量补充渠道、使用类型、消费类型、关键字
- `POST /api/insights`  
  - 请求体：`{"lines": [[...], ...]}`  
  - 返回：按消费类型的金额分布与占比

## 🚀 快速开始
```
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 🧭 标语
- 主标语：Where Transactions Become Understanding  
  让每一笔交易，都成为对自己的理解。
- 备选：The Intelligence Layer for Your Finances  
- 备选：Beyond Categorization — Into Insight  
- 备选：Your Money, Understood

## 📚 文档
- 英文文档在 `doc/`：
  - `doc/index.md` 概览
  - `doc/api.md` 接口
  - `doc/architecture.md` 架构
- 英文版本：见 [README.md](README.md)

## 📜 许可
GNU Affero General Public License v3.0（AGPL-3.0）
