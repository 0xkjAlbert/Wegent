# GitLab 9.6 兼容性说明

## ✅ 完全兼容

Wegent **完全支持** GitLab 9.6 版本。

## GitLab API 版本历史

- **GitLab 9.0** (2017年3月): API v4 首次引入
- **GitLab 9.5** (2017年8月): API v3 废弃
- **GitLab 9.6** (2017年9月): ✅ **仅支持 API v4**
- **GitLab 11.0**: API v3 完全移除

## Wegent 使用的 API 端点

Wegent 使用以下 GitLab API v4 端点：

### 1. 列出项目
```
GET /api/v4/projects
参数:
  - membership=true (限制为当前用户是成员的项目)
  - per_page=100 (每页结果数)
  - order_by=last_activity_at (排序)
```

**兼容性**: ✅ GitLab 9.0+ 支持

### 2. 获取项目分支
```
GET /api/v4/projects/:id/repository/branches
```

**兼容性**: ✅ GitLab 9.0+ 支持

### 3. 获取用户信息
```
GET /api/v4/user
```

**兼容性**: ✅ GitLab 9.0+ 支持

### 4. 获取项目 Diff
```
GET /api/v4/projects/:id/repository/compare
```

**兼容性**: ✅ GitLab 9.0+ 支持

## Token 权限要求

创建 Personal Access Token 时需要以下权限：
- ✅ `api` - 完整的 API 访问权限
- ✅ `read_repository` (可选) - 读取仓库内容

## 配置步骤

### 1. 创建 Personal Access Token

在 GitLab 9.6 中创建 token：

1. 访问: `https://your-gitlab-domain/-/profile/personal_access_tokens`
2. 点击 "Add new personal access token"
3. Token 名称: `wegent-integration`
4. 勾选 `api` 权限
5. 点击 "Create personal access token"
6. **重要**: 复制 token (只会显示一次)

### 2. 在 Wegent 中配置

1. 访问 Wegent 集成设置页面
2. 选择 GitLab 平台
3. 填写信息:
   - **GitLab Domain**: `your-gitlab-domain` (例如: `git.53zaixian.com`)
   - **Token**: 粘贴刚才创建的 token
4. 点击保存

## 诊断工具

如果遇到问题，可以使用 Wegent 提供的诊断脚本：

```bash
cd backend
python scripts/diagnose_gitlab.py git.53zaixian.com glpat-your-token
```

这会测试：
- ✅ API 连接性
- ✅ Token 有效性
- ✅ 项目访问权限
- ✅ GitLab 版本

## 常见问题

### Q: 提示 "GitLab token validation failed"
**A**: 检查:
1. Token 是否正确复制（没有多余空格）
2. Token 是否有 `api` 权限
3. Token 是否已过期

### Q: 无法拉取项目列表
**A**: 检查:
1. 用户是否是任何项目的成员
2. 网络连接是否正常
3. GitLab URL 是否正确

### Q: URL 中出现 `~/` 字符
**A**: 这不是 GitLab API 的问题。检查:
1. GitLab API 返回的 `http_url_to_repo` 字段格式
2. Wegent 代码没有添加 `~/` 前缀
3. 可能是浏览器显示问题

## 已知的 GitLab 9.6 限制

GitLab 9.6 是较老的版本（2017年），某些新功能不可用：
- ❌ 不支持某些新引入的 API 参数
- ❌ 不支持较新的功能（如 some GitLab Duo features）
- ✅ 但 Wegent 使用的所有核心功能都完全支持

## 升级建议

建议升级到更新的 GitLab 版本以获得：
- 更好的性能
- 更多功能
- 安全补丁
- 更好的 API 支持

推荐版本：GitLab 15.x 或更高

## 参考资料

- [GitLab API v4 文档](https://docs.gitlab.com/api/)
- [GitLab 版本历史](https://about.gitlab.com/releases/categories/releases/)
- [Projects API 文档](https://docs.gitlab.com/api/projects/)
