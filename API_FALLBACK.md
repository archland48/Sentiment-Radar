# X API 自动 Fallback 到 snscrape

## 功能说明

系统现在支持**自动fallback机制**：当X API没有响应或返回空结果时，自动切换到snscrape。

## 工作流程

### 优先级顺序：
1. **X API** (如果配置了Bearer Token)
2. **snscrape** (如果API失败或返回空结果)
3. **Mock数据** (如果两者都不可用)

### 详细流程：

```
开始搜索
  ↓
检查是否配置了 TWITTER_BEARER_TOKEN?
  ├─ 是 → 尝试调用X API
  │        ├─ API成功返回推文 → 使用API结果 ✅
  │        ├─ API返回空结果 → 标记api_failed=True → Fallback到snscrape 🔄
  │        └─ API抛出异常 → 标记api_failed=True → Fallback到snscrape 🔄
  │
  └─ 否 → 检查 USE_SNSCRAPE=true?
           ├─ 是 → 直接使用snscrape
           └─ 否 → 使用Mock数据
```

## 触发Fallback的条件

### 情况1: API返回空结果
```
Querying X API for tweets...
Found 0 tweets from X API
⚠️ X API returned no results. Falling back to snscrape...
🔄 Falling back to snscrape (X API had no results or failed)
```

### 情况2: API抛出异常
```
Querying X API for tweets...
❌ X API failed with error: [错误信息]
⚠️ Falling back to snscrape...
🔄 Falling back to snscrape (X API had no results or failed)
```

### 情况3: API认证失败
```
Twitter API authentication failed. Check your bearer token.
⚠️ Falling back to snscrape...
🔄 Falling back to snscrape (X API had no results or failed)
```

## 配置选项

### 选项1: 仅使用X API（自动fallback）
```bash
# .env
TWITTER_BEARER_TOKEN=your_token_here
# USE_SNSCRAPE 不设置或设为 false
```
**行为**: 优先使用X API，失败时自动fallback到snscrape

### 选项2: 强制使用snscrape
```bash
# .env
USE_SNSCRAPE=true
# TWITTER_BEARER_TOKEN 可以不设置
```
**行为**: 直接使用snscrape，跳过X API

### 选项3: 仅使用Mock数据
```bash
# .env
# 不设置 TWITTER_BEARER_TOKEN
# USE_SNSCRAPE=false 或不设置
```
**行为**: 使用Mock数据（用于开发测试）

## 日志输出示例

### 成功使用API：
```
Querying X API for tweets (optimized: merged queries)...
Querying X API with: (AAPL) OR (Apple) OR ($AAPL) OR (Apple Inc.) -is:retweet lang:en is:verified
Found 15 tweets in this batch
Found 15 tweets from X API (optimized: 1 API calls instead of 4)
```

### API失败，自动fallback：
```
Querying X API for tweets (optimized: merged queries)...
Querying X API with: (AAPL) OR (Apple) OR ($AAPL) OR (Apple Inc.) -is:retweet lang:en is:verified
Found 0 tweets in this batch
Found 0 tweets from X API (optimized: 1 API calls instead of 4)
⚠️ X API returned no results. Falling back to snscrape...
🔄 Falling back to snscrape (X API had no results or failed)
⚠️ WARNING: snscrape violates Twitter's Terms of Service. Use at your own risk.
Scraping tweets with snscrape (verified accounts only): (AAPL) OR (Apple) OR ($AAPL) OR (Apple Inc.) lang:en since:2024-01-23 filter:verified
Found 12 tweets using snscrape (optimized)
```

## 优势

1. **自动恢复**: API失败时自动切换，无需手动干预
2. **无缝体验**: 用户无需知道使用了哪个数据源
3. **可靠性**: 即使API不可用，系统仍能工作
4. **灵活性**: 可以通过环境变量控制行为

## 注意事项

1. **snscrape违反ToS**: 使用snscrape违反Twitter服务条款
2. **性能差异**: snscrape可能比API慢
3. **数据质量**: snscrape的数据可能不如API完整
4. **Rate Limits**: snscrape没有rate limits，但可能被Twitter检测

## 故障排查

如果fallback没有触发：

1. **检查日志**: 查看是否有 `api_failed = True` 的输出
2. **检查snscrape**: 确认 `pip install snscrape` 已安装
3. **检查环境变量**: 确认 `USE_SNSCRAPE` 未强制设为 `false`
4. **检查异常处理**: 查看是否有异常被捕获

## 代码位置

- **Fallback逻辑**: `main.py` → `search_tweets()` 函数
- **API查询**: `main.py` → `query_x_api()` 函数
- **snscrape查询**: `main.py` → `query_x_api_snscrape()` 函数
