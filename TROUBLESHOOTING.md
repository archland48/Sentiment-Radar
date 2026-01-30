# 故障排查指南 - "No tweets found" 问题

## 问题症状
搜索后显示：
```
Broad Scan Report
No tweets found matching the search criteria.
```

## 诊断步骤

### 1. 检查服务器日志
查看后端控制台输出，查找以下信息：
- `Querying X API with: [查询字符串]`
- `Found X tweets in this batch`
- `No tweets found for query: [查询字符串]`
- 任何错误消息

### 2. 检查浏览器控制台
打开浏览器开发者工具（F12）→ Console标签，查看：
- `displayResults - Full data:` - 查看完整响应
- `Broad Scan - tweets count:` - 查看推文数量
- 任何JavaScript错误

### 3. 常见原因和解决方案

#### 原因1: API查询返回空结果
**症状**: 日志显示 `No tweets found for query: ...`

**可能原因**:
- ✅ **已验证账户过滤器太严格** - `is:verified` 可能没有匹配结果
- ✅ **关键词在过去7天没有推文** - 时间范围限制
- ✅ **查询语法问题** - OR查询可能有问题

**解决方案**:
1. 尝试更通用的关键词（如 "Apple" 而不是 "AAPL"）
2. 检查服务器日志中的实际查询字符串
3. 尝试移除 `is:verified` 过滤器（临时测试）

#### 原因2: API配额限制
**症状**: 日志显示 `Rate limit reached` 或 `TooManyRequests`

**解决方案**:
- 等待15分钟后重试
- 检查Twitter Developer Portal中的API使用情况
- 考虑升级到更高API层级

#### 原因3: Bearer Token问题
**症状**: 日志显示 `Twitter API authentication failed`

**解决方案**:
1. 检查 `.env` 文件中的 `TWITTER_BEARER_TOKEN`
2. 确认token格式正确（以 `AAAAAAAAAAAAAAAAAAAAA` 开头）
3. 在Twitter Developer Portal重新生成token

#### 原因4: 查询语法错误
**症状**: 日志显示 `Twitter API bad request`

**解决方案**:
- 代码现在会自动尝试不使用verified过滤器的fallback查询
- 检查查询字符串长度（Twitter API限制~512字符）
- 如果变体太多，可能需要分批查询

### 4. 测试步骤

#### 测试1: 验证API连接
```bash
# 检查环境变量
echo $TWITTER_BEARER_TOKEN

# 或者检查.env文件
cat .env | grep TWITTER_BEARER_TOKEN
```

#### 测试2: 简化查询
尝试搜索单个简单关键词：
- "Apple" 而不是 "AAPL"
- "Tesla" 而不是 "TSLA"

#### 测试3: 检查API响应
查看服务器日志中的详细输出：
```
Querying X API with: (Apple) OR (AAPL) OR ($AAPL) OR (Apple Inc.) -is:retweet lang:en is:verified
Found 0 tweets in this batch
```

### 5. 临时解决方案

如果急需测试，可以临时移除verified过滤器：

在 `main.py` 的 `query_x_api` 函数中，将：
```python
query=f"{query} -is:retweet lang:en is:verified",
```

改为：
```python
query=f"{query} -is:retweet lang:en",
```

**注意**: 这会返回所有账户的推文，不仅仅是已验证账户。

### 6. 调试信息

代码现在会输出以下调试信息：
- ✅ 实际使用的查询字符串
- ✅ 每批找到的推文数量
- ✅ API错误详情
- ✅ 自动fallback尝试

### 7. 检查清单

- [ ] Bearer Token已正确配置在 `.env` 文件中
- [ ] Token格式正确（不是placeholder值）
- [ ] API配额未超限
- [ ] 关键词在过去7天有推文
- [ ] 查询字符串长度合理（<512字符）
- [ ] 服务器日志显示查询已执行
- [ ] 没有API认证错误

### 8. 获取帮助

如果问题持续存在，请提供：
1. 服务器日志的完整输出
2. 浏览器控制台的错误信息
3. 使用的关键词
4. API配额使用情况（Twitter Developer Portal）

## 预期行为

正常情况下，你应该看到：
```
Querying X API for tweets (optimized: merged queries)...
Querying X API with: (AAPL) OR (Apple) OR ($AAPL) OR (Apple Inc.) -is:retweet lang:en is:verified
Found 15 tweets in this batch
Found 15 tweets from X API (optimized: 1 API calls instead of 4)
```

如果看到 `Found 0 tweets`，说明查询成功但无结果，可能是：
- 没有已验证账户在 past week 发推
- 关键词匹配度低
- 需要调整搜索策略
