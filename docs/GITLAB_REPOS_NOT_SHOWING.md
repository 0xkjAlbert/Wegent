# GitLab 仓库不显示问题排查指南

## 问题描述
API 测试成功，但 Wegent 界面仓库选择器不显示 GitLab 仓库。

## 快速诊断工具

### 1. 使用调试脚本（推荐）

```bash
cd /workspace/13/Wegent/backend

# 运行调试脚本
python scripts/debug_gitlab_repos.py git.53zaixian.com glpat-your-token
```

这个脚本会：
- ✅ 模拟 Wegent 后端的 API 调用
- ✅ 测试两种认证方式（Bearer 和 Private-Token）
- ✅ 显示返回的仓库格式
- ✅ 展示 Wegent 如何处理数据

### 2. 使用快速测试脚本

```bash
cd /workspace/13/Wegent/backend

python scripts/quick_gitlab_test.py git.53zaixian.com glpat-your-token
```

## 常见问题排查

### 步骤 1：检查后端日志

```bash
# 查看 Wegent 后端日志
docker-compose logs -f backend | grep -i gitlab

# 应该看到类似这样的日志：
# [GitLab] Fetching repositories for user xxx from git.53zaixian.com
# [GitLab] Successfully fetched N repositories for user xxx from git.53zaixian.com
```

**如果看到错误日志**，例如：
```
[GitLab] Failed to fetch repositories from git.53zaixian.com: ...
```

这表示 API 调用失败。

### 步骤 2：检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 切换到 **Console** 标签
3. 刷新页面，尝试加载仓库列表
4. 查找错误信息

**常见错误**：
- `401 Unauthorized`: Token 无效或权限不足
- `Failed to fetch`: 网络问题或 CORS 错误
- `500 Internal Server Error`: 后端错误

### 步骤 3：检查网络请求

1. 打开浏览器开发者工具（F12）
2. 切换到 **Network** 标签
3. 刷新页面
4. 找到 `/api/git/repositories` 请求
5. 查看：
   - **Status Code**: 应该是 200
   - **Response**: 应该包含仓库列表

**如果请求失败**，查看 Response 中的错误信息。

### 步骤 4：检查用户配置

确保在 Wegent 设置中正确配置了 GitLab：

1. 访问：**设置** → **集成配置**
2. 检查 GitLab 配置：
   - **GitLab Domain**: `git.53zaixian.com`（不要加 https://）
   - **Token**: 正确的 Personal Access Token
   - **Type**: 选择 `GitLab`

### 步骤 5：清除缓存并重试

```bash
# 1. 清除后端 Redis 缓存
cd /workspace/13/Wegent
docker-compose exec backend python -c "
import asyncio
from app.models.user import User
from app.services.repository import repository_service
from app.api.dependencies import get_db

async def clear_cache():
    db = next(get_db())
    # 获取您的用户（需要根据实际情况修改）
    user = db.query(User).filter(User.user_name == 'your_username').first()
    if user:
        cleared = await repository_service.clear_user_cache(user)
        print(f'Cleared cache for: {cleared}')
    db.close()

asyncio.run(clear_cache())
"

# 2. 重启后端
docker-compose restart backend

# 3. 在浏览器中刷新页面并重试
```

## 可能的原因和解决方案

### 原因 1：Token 权限不足 ❌

**症状**：
- API 测试失败，返回 401 或 403
- 后端日志显示认证错误

**解决方案**：
1. 登录 GitLab: `https://git.53zaixian.com/-/profile/personal_access_tokens`
2. 创建新 Token，确保勾选 ✅ `api` 权限
3. 在 Wegent 设置中更新 Token

### 原因 2：用户不是任何项目的成员 ❌

**症状**：
- API 返回空数组 `[]`
- 调试脚本显示 "No repositories found"

**解决方案**：
1. 在 GitLab 中，确保您是至少一个项目的成员
2. 或者请管理员将您添加到项目

### 原因 3：GitLab URL 配置错误 ❌

**症状**：
- 连接超时或拒绝连接
- 后端日志显示网络错误

**解决方案**：
确保 GitLab Domain 格式正确：
- ✅ 正确: `git.53zaixian.com`
- ❌ 错误: `https://git.53zaixian.com`
- ❌ 错误: `git.53zaixian.com/`

### 原因 4：后端代码错误（已修复） ✅

**症状**：
- API 调用成功但仓库不显示
- 后端没有相关日志

**原因**：
之前的代码在 API 失败时会静默跳过错误，不记录日志。

**已修复**：
现在会记录详细的日志，包括成功和失败的情况。

### 原因 5：缓存问题 ❌

**症状**：
- 之前配置错误，现在已修复但仍不显示
- API 测试成功，但界面仍不显示

**解决方案**：
1. 点击仓库选择器中的刷新按钮 🔄
2. 或者清除 Redis 缓存（见步骤 5）

## 调试流程图

```
开始
  ↓
运行调试脚本 → 成功?
  ↓              ↓
 失败           检查后端日志
  ↓              ↓
检查Token权限    有错误?
  ↓              ↓
修复Token      → 是 → 查看错误详情
                   ↓
                解决错误
                   ↓
清除缓存并重试
  ↓
检查浏览器控制台
  ↓
检查网络请求
  ↓
问题解决 ✅
```

## 需要更多信息？

如果以上步骤都无法解决问题，请收集以下信息：

1. **调试脚本的输出**：
   ```bash
   python scripts/debug_gitlab_repos.py git.53zaixian.com your-token > debug_output.txt 2>&1
   ```

2. **后端日志**：
   ```bash
   docker-compose logs backend | grep -i gitlab > backend_logs.txt
   ```

3. **浏览器网络请求**：
   - F12 → Network → 找到 `/api/git/repositories` 请求
   - 右键 → Copy as cURL

4. **用户配置信息**（隐藏敏感信息）：
   - GitLab Domain（可以隐藏具体域名）
   - Token 类型（Personal Access Token 或 OAuth）
   - 是否是项目成员

将这些信息提供给 Wegent 团队以获得进一步帮助。
