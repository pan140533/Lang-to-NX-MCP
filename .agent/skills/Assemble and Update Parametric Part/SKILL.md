## Skill: Assemble and Update Parametric Part

### 何时使用
当用户要求将带参数的 PRT 文件装配到指定位置，并更新其表达式值时使用此 Skill。

### 工具调用示例

**用户说**：“把 bracket.prt 装到 main.prt 的原点位置，让 d1=100，d2=50”

**LLM 应调用**：
nx_assemble_and_update(
assembly_path="C:\asm\main.prt",
part_path="C:\parts\bracket.prt",
position_x=0.0, position_y=0.0, position_z=0.0,
expressions_json='[{"name":"d1","value":100.0},{"name":"d2","value":50.0}]'
)

text

### 参数约束
- `position_*`：浮点数，单位为毫米
- `expressions_json`：JSON 数组字符串，每个元素包含 `name`（字符串）和 `value`（浮点数）
- `copy_before_update`：默认 `True`。会先把 `part_path` 复制一份到 `output/models/`，
  再在副本上改参、拍平和装配，**原部件不会被修改**；只有显式传 `False` 才会直接改原部件
- `flatten_assembly`：默认 `True`，即**彻底拍平**（分两步，见下）。设 `False` 则完整保留
  原始装配树
- `cleanup_descendants`：默认 `True`。彻底拍平之后删掉已经没人引用的派生子孙 .prt
  （工作副本 + 为解析子组件而复制的兄弟部件）。只删本次生成、位于 `output/` 之内、
  且不被成品引用的文件；**母版与最终交付物永不删除**。设 `False` 可保留中间文件
- 方向矩阵默认为单位矩阵（无旋转），仅在需要旋转时显式指定 9 个参数
- 路径必须使用**双反斜杠**转义或正斜杠

### 执行顺序
复制副本 → 改表达式 → **拍平副本** → 装配 → **拍平装配体** → **清理派生子孙 .prt**

两步拍平缺一不可：

1. **拍平副本**：副本自己可能是装配体（如 `DangKuai.prt` 内含 `Q_screws_cb`），先把它的
   子部件几何合并进它，副本成为自洽单文件；这也让下一步能把它当作普通部件导入。
2. **拍平装配体**：装配完成后，把刚装进去的组件再合并进装配体根部件。
   少了这一步，交付物仍然是「父装配体 + 子部件」两个 .prt，装配关系没有消除。

最终交付的 `assembly_path` 是一个**零组件**的单一 .prt，几何、特征、表达式全部在内，
`output/` 里也不会再留下中间副本或兄弟部件。

拍平也可单独调用：`nx_assemble_to_model(part_path=..., output_path=...)`。
注意两点：
- **限制**：组件的部件如果**自己也是装配体**，NX 的「导入部件」无法合并它
  （报 `Update undo happened`）——需要**自底向上**逐个拍平；`nx_assemble_and_update`
  会自动按这个顺序做，直接调用本工具时请自己保证顺序。
- 该工具**不会**删除任何子孙 prt（它面对的是用户自己的部件文件）；清理只发生在
  `nx_assemble_and_update` 里，且只针对它自己派生出来的副本。
任何一步不成立都整体不保存，不会留下缺失几何的半成品。

### 扁平化后的表达式命名
NX 在导入时会给**重名表达式**加后缀以避免冲突，例如：
`DangKuai_L` → `DangKuai_L'0`（子部件的则是 `...'2'0`）。数值不变，只是名字变了。
拍平后要按名字改参，需先确认实际名称。

### 返回值
- `source_part_path`：原部件（只读，未被修改）
- `working_part_path`：改参、拍平并参与装配用的副本路径。
  清理开启且拍平成功时**该文件已被删除**（几何已吸收进成品）
- `assembly_path`：最终成品（**已拍平为单一部件，零组件**）
- `flatten`：副本拍平阶段明细（`imported` 导入的子部件及位姿、`removed` 移除的组件、
  `bodies_before`/`bodies_after`、`already_flat`、`unresolved`、`nested_subassemblies`）
- `flatten_assembly`：装配体拍平阶段明细（字段同上）
- `cleanup`：清理明细（`removed` 已删除的派生 .prt、`skipped_outside_output`、
  `kept_working_part`）。未清理时为 `null`

### 禁止事项
- 不要生成 NXOpen API 代码，始终通过 MCP 工具调用
- 不要在参数中传入中文路径（NX 11 批处理模式对非 ASCII 支持有限）