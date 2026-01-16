# FinMind Architecture

## Components
- Data Dictionaries: `account/static/*.json`
- Classification: `account/analyzer/ConsumptionAnalyzer.py`
- Business Analysis: `account/analyzer/BusinessAnalyzer.py`
- DB Helpers: `account/db/SQLiteHelper.py`
- API Layer: `engine/views.py`, `engine/urls.py`
- Django Project: `finmind_site/*`

## Data Flow
1. FinSight ingests and cleans bank exports (CSV/SQLite).
2. FinMind reads cleaned rows and runs:
   - Disbursement channel resolution
   - Type-of-use resolution
   - Consumption classification
3. FinMind aggregates and produces explainable insights.
4. Frontend or scripts consume endpoints to render reports.

## Sequence (Text)
- Input rows arrive with description and amount fields.
- `BusinessAnalyzer.calculate` iterates rows:
  - Appends channel, use-type, consumption-type, keyword columns.
  - Delegates consumption classification to `ConsumptionAnalyzer`.
- `engine/views.py` endpoints:
  - `/classify`: single description + amount → consumption type
  - `/analyze`: batch rows → enriched rows
  - `/insights`: batch rows → totals and ratios by type

## Design Notes
- Rule-first, model-light: fast, deterministic, explainable.
- All data local: zero network calls; privacy by design.
- Pluggable NLP: optional enhancements when performance permits.
- Compatible with FinSight: acts as the “cognitive core”.

## Extensibility
- Add new dictionaries in `account/static` and extend analyzers.
- Insert NLP step after rule match for borderline cases.
- Extend `/insights` to compute monthly deltas, impulse scores, payday effects.

## AI Model Design (Sentiment & Classification)

### Goals
- 利用已有交易记录和规则数据，训练模型自动完成/增强交易分类。
- 针对备注、商户名等文本做情感和语义识别，辅助运营分析。
- 通过离线评估和在线监控，持续优化模型表现。

### Training Data
- 来源一：历史 Transaction 表 + ConsumeRule/ConsumeCategory（使用当前规则匹配结果作为弱监督标签）。
- 来源二：用户在前端手动修正的分类、批量分配结果（高质量标签）。
- 结构示例：
  - 输入特征：
    - 文本：transaction_desc, opponent_name, opponent_account, consume_name, bank_card_name, card_type_name。
    - 数值：amount（income_money/balance_money），日期相关特征（weekday, month）。
  - 标签：
    - 主标签：消费类别（ConsumeCategory.code），和现有规则保持一致。
    - 辅助标签（可选）：情感极性（正向/中性/负向），如“退款”、“罚款”、“违约金”等负面支出。

### Feature Engineering
- 文本预处理：
  - NFKC 归一化、全半角转换、大小写统一、空白归并（与 `_norm` 保持一致）。
  - 特殊符号、卡号、流水号脱敏或归一。
- 文本表示：
  - 方案一：使用预训练的中文 BERT/ERNIE/通用 Transformer，做微调。
  - 方案二：轻量级 TF-IDF + 线性模型，作为 baseline。
- 数值/时间特征：
  - 标准化金额（log/分桶）。
  - 周期性时间特征（weekday, hour）。

### Model Variants
- 模型 A：交易类别分类模型
  - 输入：交易描述相关文本 + 金额 + 日期特征。
  - 输出：类别 code（与 ConsumeCategory 对齐）。
  - 用途：
    - 边界/未匹配交易的自动推荐类别（替代/增强 `rule_recommend`）。
    - 新出现模式（规则尚未覆盖）的冷启动分类。
- 模型 B：情感分析/风险提示模型
  - 输入：交易描述、备注。
  - 输出：情感极性标签（正/中/负）+ 风险分（0–1）。
  - 用途：
    - Dashboard 新增“风险支出/异常支出分布”视图。
    - 为运营管理部提供针对特定负向支出（罚款、违约金、滞纳金）的聚合视图。

### Training & Evaluation
- 训练流程：
  - 周期性从数据库抽取最新标注数据（规则 + 人工纠正）。
  - 划分训练/验证/测试集，按时间切分保证评估贴近真实上线场景。
  - 训练 baseline 模型（如 Logistic Regression + TF-IDF），再替换为 Transformer。
- 评估指标：
  - 分类任务：
    - 准确率、宏平均 F1、按大类/小类的 F1。
    - Top-K 准确率（Top-3 推荐中命中正确类别的比例）。
  - 情感/风险任务：
    - F1、AUC、召回率（对负向/风险类尤其关注）。
  - 业务指标：
    - 模型推荐被用户接受的比例。
    - 未匹配交易占比随时间的下降趋势。
- 评估流程：
  - 离线评估：对历史数据做批量预测，生成混淆矩阵、PR 曲线。
  - 在线评估（可选）：
    - A/B Test：部分用户/部分交易走“模型推荐优先”，部分继续走“规则优先”，比较人工修正率。

### Deployment Plan
- 推理服务形态：
  - 内部 Python 服务（如 FastAPI）或复用 Django + `core.services` 层，暴露 `/api/agents/classify-model` 等 API。
  - 对于大模型，可使用已有的 `core.tools.qwen_api`，在本地增加一层结果缓存和后处理。
- 与现有系统的集成：
  - 在 `rule_recommend` 中增加模型通路：
    - 先调用规则 + 现有 LLM 推荐。
    - 再调用训练好的分类模型，对候选类别打分、排序或补充新的候选。
  - 在 Dashboard 新增“模型表现”模块：
    - 展示覆盖率、Top-K 准确率、近期未匹配率曲线。
  - 在“未匹配详情”弹窗中：
    - 除现有的规则/LLM 推荐外，展示模型推荐的类别及置信度。

### Monitoring & Iteration
- 监控内容：
  - 推理延迟（P95）、错误率。
  - 模型置信度分布、预测分布是否漂移。
  - 用户对推荐类别的采纳/修改行为。
- 数据闭环：
  - 将用户手动调整类别、批量分配结果回流为训练样本。
  - 定期重新训练并对比新旧模型的离线指标和在线指标。

