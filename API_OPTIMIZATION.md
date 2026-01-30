# API Quota 优化方案

## 核心问题

1. **API Quota 浪费**：
   - 每个关键词变体都单独调用API（如"AAPL", "Apple", "$AAPL"分别调用）
   - 如果搜索"AAPL"产生4个变体，就会调用4次API
   - 浪费了75%的API配额

2. **重复数据**：
   - 同一个tweet可能匹配多个变体（如"AAPL"和"$AAPL"）
   - 去重是在API调用之后，已经浪费了quota

## 解决方案

### 方案1: 合并查询（推荐）✅
**使用OR操作符在一个API调用中查询所有变体**

优点：
- 减少API调用次数：从N次减少到1次
- 节省quota：减少75-90%的API使用
- 更快：一次调用比多次调用快

实现：
```python
# 之前：每个variation单独调用
for variation in variations:
    query = f"({variation})"
    api_tweets = await query_x_api(query)

# 优化后：合并所有variations
all_variations = " OR ".join([f"({v})" for v in variations])
query = f"({all_variations})"
api_tweets = await query_x_api(query)
```

### 方案2: 查询缓存
**缓存最近的查询结果，避免重复查询**

优点：
- 相同查询直接返回缓存
- 减少API调用
- 更快响应

实现：
- 使用内存缓存（如dict）或Redis
- TTL: 5-15分钟（tweets时效性强）
- Key: 查询字符串的hash

### 方案3: 智能去重
**查询前去重，避免查询重复内容**

优点：
- 减少不必要的查询
- 节省quota

实现：
- 检查缓存中是否已有相同查询
- 合并相似查询（如"AAPL"和"$AAPL"本质上相同）

### 方案4: 批量处理
**一次处理多个关键词**

优点：
- 减少API调用次数
- 更好的quota利用率

## 实施优先级

1. ✅ **合并查询** - 立即实施，效果最明显
2. ⚠️ **查询缓存** - 次要优化，需要额外存储
3. ⚠️ **智能去重** - 辅助优化

## 预期效果

### 优化前：
- 搜索"AAPL"（4个变体）→ 4次API调用
- 搜索2个关键词（各4个变体）→ 8次API调用
- Quota使用：高

### 优化后：
- 搜索"AAPL"（4个变体）→ 1次API调用（合并）
- 搜索2个关键词（各4个变体）→ 2次API调用（每个关键词1次）
- Quota使用：减少75-87.5%

## 注意事项

1. **Twitter API查询长度限制**：查询字符串有长度限制（~512字符）
2. **OR查询可能返回更多结果**：需要适当调整max_results
3. **缓存失效**：tweets时效性强，缓存时间不宜过长
