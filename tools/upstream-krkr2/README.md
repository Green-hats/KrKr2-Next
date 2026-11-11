# KrKr2 macOS Actions 构建

本目录与 `.github/workflows/upstream-krkr2-macos.yml` 使用 GitHub Actions 的 `macos-15` Apple Silicon runner 编译
[2468785842/krkr2](https://github.com/2468785842/krkr2) 完整应用。
源代码和 vcpkg 都固定到工作流中记录的提交；保留上游默认运行时和 PSD 功能，关闭测试与独立工具。

推送构建分支 `devin/*-upstream-krkr2-macos` 会触发构建。
工作流合入默认分支后，也可在 Actions 中选择 **Build KrKr2 macOS ARM64 → Run workflow**。
成功后下载 `krkr2-macos-arm64` artifact，解压其中的 `krkr2-macos-arm64.zip` 获取 `krkr2.app`。
工作流也上传 `macos-build-logs`，便于调查依赖或编译失败。

产物面向 Apple Silicon，部署目标为 macOS 12.0。
应用使用临时签名，未经过 Apple 公证；工作流验证应用包、依赖、签名和 `--help` 启动，
这些检查不等于 GUI 或游戏兼容性验证。具体可用性以实际 Actions 结果为准。

`patches/macos-bundle.patch` 修正上游 macOS Info.plist 路径及 CMake 模板变量。
上游项目使用 MIT 许可，产物附带上游 LICENSE；第三方依赖仍遵循各自许可。
