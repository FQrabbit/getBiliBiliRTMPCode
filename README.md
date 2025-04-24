# B站直播推流码获取工具

## 功能说明
本工具用于获取B站直播的推流码（RTMP地址和串流密钥），方便开发者调试直播相关功能。

## 使用方法

### 第一步：获取Cookie
1. 打开B站直播开通页面：[https://link.bilibili.com/p/center/index#/my-room/start-live](https://link.bilibili.com/p/center/index#/my-room/start-live)
2. 按 `F12` 或 `Ctrl+Shift+I` 打开开发者工具
3. 切换到 **Network（网络）** 选项卡
4. 刷新页面（`F5`）
5. 在请求列表中找到任意一个 `POST` 请求（通常为 `room/v1/Room/startLive`）
6. 点击该请求，在 **Headers（标头）** 中找到 `Cookie` 字段
7. 复制整个Cookie字符串（从`buvid3=`开始到结尾）
![获取Cookie示例图](/doc/cookie.png)
### 第二步：运行程序
将复制的Cookie粘贴到程序输入中，并填写房间号(长房间号)，点击锁定，选择开播。

---

## 手动编译指南

### 环境要求
- Python 3.10+
- PyInstaller

### 编译步骤
```bash
# 安装依赖
pip install pyinstaller requests pyperclip

# 单文件打包（推荐）
pyinstaller --onefile --windowed --name getBiliBiliRTMPCode getBiliBiliRTMPCode.py

# 生成的EXE文件位于 dist/ 目录下
```

---

## 免责声明

⚠️ **法律与道德声明**
1. 本工具仅限**技术学习与研究**用途，禁止用于任何违反哔哩哔哩用户协议的行为
2. 开发者不对滥用本工具造成的账号封禁等后果负责
3. 请勿将获取的推流码用于未授权的多平台转播等违规行为
4. 根据《计算机软件保护条例》，使用者需自行承担法律风险

**重要提示**：
哔哩哔哩直播推流码属于敏感信息，请遵守[《哔哩哔哩直播服务协议》](https://live.bilibili.com/p/html/live-app-help/index.html#/live-protocol)。持续高频访问接口可能导致账号风控，请谨慎使用。

---


