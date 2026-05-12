# Codex++

<p align="center">
  <img src="docs/images/codex-plus-plus.png" alt="Codex++ 图标" width="256">
</p>

Codex++ 是一个面向 OpenAI Codex App 的外部增强启动器。它不修改 Codex App 原始安装文件，而是通过外部 launcher 启动 Codex，并使用 Chromium DevTools Protocol 向渲染进程注入增强脚本。

## 原作者与来源

本项目参考并二次封装自 BigPizzaV3 大佬的开源项目：

- 原项目地址：[https://github.com/BigPizzaV3/CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus)
- 原作者：BigPizzaV3

感谢原作者提供 Codex++ 的核心思路、启动逻辑、CDP 注入方案和会话删除能力。本仓库主要同步上游代码，并整理 macOS / Windows 便携发布包，方便普通用户直接下载使用。

## 目录

- [功能](#功能)
- [痛点](#痛点)
- [解决效果](#解决效果)
- [下载](#下载)
- [工作方式](#工作方式)
- [环境要求](#环境要求)
- [Windows 使用](#windows-使用)
  - [便携版 exe](#便携版-exe)
  - [图形菜单安装/卸载](#图形菜单安装卸载)
  - [命令行安装](#命令行安装)
  - [命令行卸载](#命令行卸载)
- [自动更新](#自动更新)
- [macOS 使用](#macos-使用)
- [直接启动](#直接启动)
- [数据与备份](#数据与备份)
- [Windows 自动接管（可选）](#windows-自动接管可选)
- [常见问题](#常见问题)
- [开发](#开发)

## 功能

当前功能：

- 在会话列表悬停显示“删除”按钮
- 删除前确认，支持撤销
- 优先尝试服务端删除；不可用时删除本地 Codex SQLite 会话记录
- 在顶部菜单栏加入 `Codex++` 菜单
- 支持插件选项解锁
- 支持特殊插件强制安装
- 支持会话删除
- 支持 Markdown 导出
- 支持用户脚本管理
- 支持项目移动辅助
- 支持后端状态指示与修复入口
- 支持 Windows 快捷方式安装/卸载
- 支持 Windows x64 portable `.exe`
- 支持 macOS `.app`
- 支持基于 GitHub Release 检查和更新 Codex++

## 痛点

API Key 登录模式下，Codex 原生插件入口会提示需要登录 ChatGPT，导致插件功能无法正常使用：

![API Key 模式下插件入口不可用](docs/images/pain-plugin-disabled.png)

同时，Codex 原生会话列表只有归档入口，没有真正的删除按钮：

![原生会话列表缺少删除能力](docs/images/pain-no-delete-button.png)

## 解决效果

Codex++ 启动后会解锁插件入口，并在会话列表悬停时显示删除按钮：

![Codex++ 解锁插件入口并添加删除按钮](docs/images/solution-plugin-and-delete.png)

顶部菜单栏会出现 `Codex++`，点击后可以打开配置界面：

![Codex++ 后端状态指示灯](docs/images/backend-status-indicator.png)

![Codex++ 配置界面](docs/images/settings-panel.png)

## 下载

预打包文件已放在 GitHub Releases：

- macOS Apple Silicon：[Codex++-macOS-arm64.zip](https://github.com/a110q/codexplus/releases/download/v1.0.5.1/Codex%2B%2B-macOS-arm64.zip)
- Windows x64 portable：[Codex++-Windows-x64-portable.zip](https://github.com/a110q/codexplus/releases/download/v1.0.5.1/Codex%2B%2B-Windows-x64-portable.zip)

Release 页面：[https://github.com/a110q/codexplus/releases/tag/v1.0.5.1](https://github.com/a110q/codexplus/releases/tag/v1.0.5.1)

## 工作方式

Codex++ 使用外部启动方式运行 Codex：

1. 启动 Codex App，并附加 `--remote-debugging-port` 和 `--remote-allow-origins`。
2. 启动本地 helper 服务，保留健康检查和运行生命周期。
3. 通过 CDP 注入 `renderer-inject.js`。
4. 渲染端通过 CDP bridge 调用本地删除、导出、用户脚本等服务；默认不开放 HTTP 删除/撤销入口，避免本机其他页面误触发删除类操作。
5. 启动 Codex 时会继承现有 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`；如果这些环境变量未设置，会自动探测常见本地代理端口。

这种方式不会修改 Codex 的 `app.asar`，也不需要往 Codex 安装目录写 DLL。

## 环境要求

- Python 3.11+
- Windows 或 macOS
- 已安装 Codex App

安装依赖：

```bash
python -m pip install -e .
```

运行测试：

```bash
python -m pip install -e .[test]
python -m pytest -q
```

## Windows 使用

### 便携版 exe

1. 下载 `Codex++-Windows-x64-portable.zip`
2. 解压整个文件夹
3. 确保 Windows 已安装 Codex App
4. 双击文件夹里的 `Codex++.exe`

不要只复制单个 `Codex++.exe`。Windows 便携包依赖同目录内的 `python/`、`app/` 和 `vendor/` 文件夹。

### 图形菜单安装/卸载

双击项目根目录的：

```text
setup.bat
```

然后按菜单选择：

```text
[1] Install Codex++
[2] Uninstall Codex++
[3] Update Codex++
[4] Exit
```

### 命令行安装

在项目目录执行：

```bash
python -m codex_session_delete setup
```

安装后会在桌面生成：

```text
Codex++.lnk
```

双击该快捷方式启动 Codex++。

### 命令行卸载

可以在系统“设置 -> 应用 -> 已安装的应用”里卸载 `Codex++`。

也可以在项目目录执行：

```bash
python -m codex_session_delete remove
```

如需同时删除 Codex++ 自己的日志和备份数据：

```bash
python -m codex_session_delete remove --remove-data
```

## 自动更新

Codex++ 会在启动时检查本仓库 GitHub Release。如果发现比本地版本更新的 Release，会在控制台提示版本号、Release 地址和更新命令；检查失败不会影响 Codex++ 启动。

手动检查更新：

```bash
python -m codex_session_delete check-update
```

从最新 GitHub Release 更新：

```bash
python -m codex_session_delete update
```

更新流程：

1. 请求 `https://api.github.com/repos/a110q/codexplus/releases/latest`。
2. 比较最新 Release tag 与本地版本。
3. 优先下载 Release 中的 `.whl` asset。
4. 执行 `python -m pip install --upgrade <wheel>`。
5. 自动重新执行 `python -m codex_session_delete setup`，刷新快捷方式、Windows 卸载项或 macOS app bundle。

## macOS 使用

1. 下载 `Codex++-macOS-arm64.zip`
2. 解压得到 `Codex++.app`
3. 将 `Codex++.app` 放到 `/Applications` 或任意目录
4. 双击 `Codex++.app` 启动

如果 macOS 提示应用来自未知开发者，可以在“系统设置 -> 隐私与安全性”中允许运行，或在终端执行：

```bash
xattr -dr com.apple.quarantine /Applications/Codex++.app
```

当前 macOS 包为 Apple Silicon arm64 构建。

## 直接启动

不安装快捷方式时，也可以直接运行：

```bash
python -m codex_session_delete launch
```

常用参数：

```bash
python -m codex_session_delete launch \
  --app-dir "/Applications/OpenAI Codex.app" \
  --debug-port 9229 \
  --helper-port 57321
```

Windows 也可以手动指定 Codex 安装目录：

```bash
python -m codex_session_delete launch \
  --app-dir "C:/Program Files/WindowsApps/OpenAI.Codex_xxx/app" \
  --debug-port 9229 \
  --helper-port 57321
```

## 数据与备份

Codex++ 默认读取 Codex 本地数据库：

```text
~/.codex/state_5.sqlite
```

删除前会把相关记录备份到：

```text
~/.codex-session-delete/backups
```

隐藏启动失败日志位于：

```text
~/.codex-session-delete/launcher.log
```

Windows 对应路径通常在：

```text
%USERPROFILE%\.codex-session-delete\launcher.log
```

## Windows 自动接管（可选）

默认情况下 Codex++ 只在你从 `Codex++` 快捷方式启动时生效。如果你从开始菜单、任务栏或系统原生入口直接启动 Codex，那一次不会有注入，`Codex++` 菜单和插件解锁都不会出现。

Windows 可以注册一个常驻 watcher 解决这个问题。它会每 3 秒探测一次本机 CDP 端口，发现 Codex 在跑但 CDP 没起来，会先短暂等待并二次确认，确认仍没有 CDP 后再把这一批 Codex 进程杀掉、通过 launcher 重拉一次带注入的版本。

安装：

```bash
python -m codex_session_delete watch-install
```

卸载：

```bash
python -m codex_session_delete watch-remove
```

临时开关：

```bash
python -m codex_session_delete watch-disable
python -m codex_session_delete watch-enable
```

日志：

```text
%USERPROFILE%\.codex-session-delete\watcher.log
```

## 常见问题

### 双击 Codex++ 没反应

先查看日志：

```text
%USERPROFILE%\.codex-session-delete\launcher.log
```

常见原因：

- Codex App 没有安装或路径变化
- 9229 端口被占用
- Python 环境不可用
- Windows portable 包没有完整解压

### 技能推荐加载失败

如果技能页提示 `git fetch failed`、`unable to access 'https://github.com/openai/skills.git/'` 或无法连接 GitHub，通常是本机网络不能直连 GitHub。Codex++ 启动时会优先继承现有代理环境变量；如果未设置，会自动探测常见本地代理端口。也可以手动指定：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
python -m codex_session_delete launch
```

### Codex++ 菜单没出现

确认是从 `Codex++` 快捷方式启动，而不是直接启动原版 Codex。

也可以检查 Codex 是否带了 CDP 参数：

```text
--remote-debugging-port=9229
```

### Windows portable 能不能只发 exe

不能。`Codex++.exe` 是便携启动器，运行时依赖同目录的 Python runtime、依赖库和项目代码。请完整分发 `Codex++-Windows-x64-portable` 文件夹或 zip。

## 开发

运行测试：

```bash
python -m pytest -q
```

项目结构：

```text
codex_session_delete/
  cli.py                 CLI 入口
  launcher.py            启动 Codex 并注入脚本
  cdp.py                 CDP 通信与 bridge
  helper_server.py       本地 helper 服务
  markdown_exporter.py   Markdown 导出服务
  storage_adapter.py     本地 SQLite 删除/撤销
  user_scripts.py        用户脚本管理
  updater.py             Release 更新
  watcher.py             Windows 常驻 watcher
  windows_installer.py   Windows 快捷方式与卸载项
  macos_installer.py     macOS app bundle 安装
  inject/renderer-inject.js

scripts/
  build_windows_portable.py

tests/
  自动化测试
```

## 说明

Codex++ 是外部增强工具，不修改 Codex App 原始文件。Codex App 更新后，如果页面结构变化，可能需要更新注入脚本。

本仓库是参考原作者项目整理和封装的版本。核心创意与主要实现来自 BigPizzaV3 的 [CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus)。如需了解原始项目、提交 issue 或查看最新上游进展，请优先访问原仓库。
