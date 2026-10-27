# 更新日志

## 提交规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 版本发布 | `vX.Y: 说明` | `v0.1: 测试版0.1 — 基础建模工具链` |
| Bug修复 | `修复: 问题说明` | `修复: sphere/rotate参数顺序错误` |
| 小修改 | `修改: 说明` | `修改: 更新.gitignore` |
| 优化重构 | `优化: 说明` | `优化: 重构api.py接口` |

---

## 历史版本

### v2.0 (2026-10-28)
架构重构 —— 去掉前端与 HTTP 接口，改为纯 MCP 服务器（stdio）

**变更:**
- 新增 `backend/mcp/`：FastMCP 服务器（8 个 MCP 工具）+ 执行链路 `service.py`
- 移除整个 `frontend/`（Next.js + Three.js）与 `backend/api.py`
- `run.py` 改为 MCP 入口，新增 `--check` / `--list-tools`
- `tools.json` 修正为合法 JSON（58 个工具，36 已实现）
- 修复 MCP 客户端环境下 NX 启动失败：自动补齐 `UGII_BASE_DIR` / `TMP` / 许可证变量
- 修复同名 `.prt` 导致 `SaveAs: File already exists`：输出名自动去重

### v0.1 (2026-06-20)
测试版0.1 — 基础建模工具链实现

**新增工具 (21个):**
- 文档: new_document, save_model
- 草图: create_sketch, close_sketch, create_sketch_on_face
- 绘图: draw_circle, draw_line, draw_rectangle, draw_arc, draw_polyline, draw_spline
- 体素: block, cylinder, cone, sphere, torus
- 布尔: boolean_unite, boolean_subtract, boolean_intersect
- 细节: chamfer, fillet, edge_blend, shell, hole, pocket, boss, pad, slot
- 阵列: pattern_linear, pattern_circular
- 镜像: mirror_feature
- 变换: translate, rotate
- 旋转: revolve

**待实现 (15个):**
- 扫掠: sweep (需 FreeformSurfaceCollection)
- 曲面(9): through_curves, through_curve_mesh, ruled, bounded_plane, fill_surface, offset_surface, extension, trim_surface, face_blend
- 同步(4): move_face, delete_face, replace_face, resize_face
- 其他: thread, scale, measure_distance, measure_volume, measure_mass
