# 监控 Sentiment Radar 处理过程

## 快速监控

运行监控脚本：
```bash
./monitor.sh
```

这个脚本会：
1. ✅ 检查部署状态
2. ✅ 检查服务健康状态
3. ✅ 显示最近的日志
4. ✅ 可选：运行测试扫描并显示详细时间

## 监控内容

### 1. 部署状态
- 服务状态（HEALTHY, UNHEALTHY, etc.）
- Koyeb 状态
- 公共 URL

### 2. 服务健康
- HTTP 状态码
- 健康检查响应

### 3. 运行时日志
- 最近 50 行日志
- 包含所有处理步骤的时间戳

### 4. 测试扫描
- 发送测试请求
- 显示每个阶段的处理时间
- 识别慢的步骤

## 代码中的监控日志

应用现在会记录详细的处理时间：

### Stage 1 日志
```
🚀 [SCAN scan_xxx] Starting scan with keywords: ['AAPL'], max_tweets: 2
⏱️  [SCAN scan_xxx] Stage 1 started at 2026-01-30T...
🔍 [STAGE1] Querying X API for 1 keyword(s)...
📊 [STAGE1] Found 15 tweets in 5234.56ms
✅ [SCAN scan_xxx] Stage 1 completed in 5234.56ms
```

### Stage 2 日志
```
⏱️  [SCAN scan_xxx] Stage 2 started at 2026-01-30T...
🚀 [STAGE2] Processing 2 tweets in parallel for Deep Dive Analysis...
✅ [STAGE2] Completed 2 LLM calls in 3456.78ms (avg: 1728.39ms per tweet)
✅ [SCAN scan_xxx] Stage 2 completed in 3456.78ms
```

### 完成日志
```
🎉 [SCAN scan_xxx] Scan completed successfully!
   Stage 1: 5234.56ms (60.2%)
   Stage 2: 3456.78ms (39.8%)
   Total: 8691.34ms
```

## 如何查看日志

### 方法 1: 使用监控脚本
```bash
./monitor.sh
```

### 方法 2: 直接查看部署日志
```bash
python3 -c "
import httpx
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('AI_BUILDER_TOKEN')
response = httpx.get(
    'https://space.ai-builders.com/backend/v1/deployments/sentimentradar/logs?log_type=runtime&timeout=10',
    headers={'Authorization': f'Bearer {token}'},
    timeout=20.0
)
data = response.json()
logs = data.get('logs', '')
# Show last 100 lines
for line in logs.split('\\n')[-100:]:
    if line.strip():
        print(line)
"
```

### 方法 3: 检查应用响应
扫描完成后，响应中包含 `duration_ms`：
```json
{
  "stage1": {
    "duration_ms": 5234.56
  },
  "stage2": {
    "duration_ms": 3456.78
  },
  "total_duration_ms": 8691.34
}
```

## 识别问题

### 如果 Stage 1 慢 (> 15 秒)
- **可能原因**：
  - X API 响应慢
  - 网络延迟
  - API 限流
- **解决方案**：
  - 检查 X API 状态
  - 使用 Bearer Token（更快）
  - 减少关键词数量

### 如果 Stage 2 慢 (> 10 秒)
- **可能原因**：
  - LLM API 响应慢
  - 并行处理失败（回退到顺序）
  - 网络延迟
- **解决方案**：
  - 检查 LLM API 状态
  - 减少 tweet 数量
  - 使用更快的模型（grok-4-fast）

### 如果总时间 > 30 秒
- **可能原因**：
  - 两个阶段都慢
  - 网络问题
  - API 限流
- **解决方案**：
  - 减少到 1 个 tweet
  - 跳过所有可选操作
  - 检查网络连接

## 性能基准

### 正常性能
- Stage 1: 4-13 秒
- Stage 2: 2-8 秒
- **总计**: 6-21 秒 ✅

### 慢性能（可能超时）
- Stage 1: > 15 秒
- Stage 2: > 10 秒
- **总计**: > 30 秒 ⚠️

### 超时风险
- 如果总时间 > 25 秒，有超时风险
- 如果总时间 > 30 秒，很可能超时

## 实时监控

### 在浏览器中测试
1. 打开 https://sentimentradar.ai-builders.space
2. 打开浏览器开发者工具（F12）
3. 查看 Network 标签
4. 运行扫描
5. 查看请求时间和响应

### 使用 curl 测试
```bash
time curl -X POST https://sentimentradar.ai-builders.space/scan \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AAPL"],
    "max_tweets": 2,
    "options": {
      "skip_ai_insights": true,
      "skip_keyword_expansion": true
    }
  }'
```

## 总结

现在应用会记录：
- ✅ 每个阶段的开始和结束时间
- ✅ X API 查询时间
- ✅ LLM 调用时间
- ✅ 总处理时间
- ✅ 每个阶段的时间占比

使用 `./monitor.sh` 可以快速查看所有信息！
