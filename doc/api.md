# FinMind API

FinMind exposes a small set of JSON endpoints for classification, batch analysis, and insight generation. All endpoints are local-only and require no authentication by default.

Base URL: `http://127.0.0.1:8000/api/`

## POST /classify
Classify a single transaction using the hybrid rules engine.

Request
```json
{
  "description": "Starbucks purchase",
  "money": "38.00"
}
```

Response
```json
{
  "consumption": {
    "name": "Dining",
    "value": "DINE",
    "keyword": "星巴克"
  }
}
```

Notes
- Internally calls `ConsumptionAnalyzer.getConsumptionType` in `account/analyzer/ConsumptionAnalyzer.py`.
- Uses rule dictionaries from `account/static/consumption-type.json`.

## POST /analyze
Batch-analyze rows and attach disbursement channel, type-of-use, consumption type, and matched keyword.

Request
```json
{
  "lines": [
    ["...", "...", "...", "38.00", "...", "...", "Starbucks purchase"]
  ]
}
```

Response
```json
{
  "lines": [
    [
      "...", "...", "...", "38.00", "...", "...", "Starbucks purchase",
      "支付渠道名称", "支付渠道编码",
      "使用类型名称", "使用类型编码",
      "消费类型名称", "消费类型编码",
      "关键字"
    ]
  ]
}
```

Notes
- Internally calls `BusinessAnalyzer.calculate` in `account/analyzer/BusinessAnalyzer.py`.
- Column indices follow the analyzer defaults:
  - `descriptionColumnIndex = 6`
  - `transactionColumnIndex = 3`

## POST /insights
Compute simple explainable insights from analyzed rows (amount totals and ratios by consumption type).

Request
```json
{
  "lines": [
    ["...", "...", "...", "38.00", "...", "...", "Starbucks purchase"]
  ]
}
```

Response
```json
{
  "total": 38.0,
  "distribution": [
    {"type": "Dining", "amount": 38.0, "ratio": 1.0}
  ]
}
```

Notes
- Calls `BusinessAnalyzer.calculate` to enrich rows, then aggregates by the added “消费类型名称”.
- Returned `ratio` is `amount / total` (0.0 if total is 0).

## Error Handling
- `400 Bad Request` for invalid JSON or missing fields.
- `405 Method Not Allowed` for non-POST requests.

