# fabric-to-style3d

精简的 Codex Skill：从纹样描述生成织物颜色贴图，或使用现有图片，在 Style3D 中应用、备份、另存并核验重开。

## 使用

将整个 `fabric-to-style3d` 文件夹放入 Codex 的用户 skills 目录，在新会话调用：

> 使用 $fabric-to-style3d，生成白色同色暗条云纹，并导入当前 Style3D 工程使用的全部织物正反面，另存副本。

也可只生成图片，或指定已有 PNG/JPEG。导入需要本机 Style3D、其内置 `spy` Python API 和可用桌面工具；图像生成需由使用环境提供。无需独立 Python 依赖或仓库内的密钥。

## 包含什么

- `SKILL.md`：图像要求、目标确认与导入流程。
- `scripts/apply_texture.py`：预检、备份、颜色图导入、另存、重开、报告。
- `tests/test_apply.py`：模拟 API 的安全边界与失败路径测试。

脚本入口和 job 格式见 [SKILL.md](SKILL.md)。首次运行输出新目录中的 `before.sproj`、`textured.sproj` 和 `result.json`，禁止覆盖已有输出目录。应用中失败可能留下部分修改；停止检查报告和备份，不能直接重跑。

## 能力与验证范围

仅处理颜色外观；不提供真实面料物理性能，不自动设置纹理尺寸、旋转、法线或透明度，不改变版片和缝合。平铺提示词不保证严格无缝。商业软件仍需由使用者自行合法安装授权。

原始工作流已在 Style3D 9.2.880 实测：现有11片工程，同一织物正反面贴图应用、另存与重开成功。通用脚本的测试和实机结果应分别记录，不能用模拟测试代替实机验证。其他版本需核实 API。

运行测试：`python -m unittest discover -s tests`。

## 开源

MIT 许可。仓库不包含 Style3D 程序、用户工程、账号凭据或生成服务；使用自己有权使用的图像。修改代码可按 MIT 分享和商用并保留许可声明。
