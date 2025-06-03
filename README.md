
# 已经改去修复弹幕库用了，此项目Archive了
而且也很好用，我也修复了连接弹幕问题和开播请求问题，晚点发release里


---

# B站直播推流码获取工具

## 🍕功能说明
本工具用于获取B站直播的推流码（RTMP地址和串流密钥），~~方便开发者调试直播相关功能~~。

## ❤️使用方法

### 第一步：获取Cookie
1. 打开B站直播后台页面：[https://link.bilibili.com/p/center/index#/my-room/start-live](https://link.bilibili.com/p/center/index#/my-room/start-live)
2. 按 `F12` 或 `Ctrl+Shift+I` 打开开发者工具
3. 切换到 **Network（网络）** 选项卡
4. 刷新页面（`F5`）
5. 在请求列表中找到任意一个 `POST` 请求（大部分`Get`请求亦可）
6. 点击该请求，在 **Headers（标头）** 中找到 `Cookie` 字段
7. 复制整个Cookie字符串（从`buvid3=`开始到结尾）
![获取Cookie示例图](/doc/cookie.png)
### 第二步：运行程序   
将复制的Cookie粘贴到程序输入中，并填写房间号(长房间号)，点击锁定，选择开播。
![程序界面](/doc/GUI.png)


## 🖥️ 命令行使用方法
嫌弃GUI太臃肿?而且也安装了python
## 📦 依赖安装
**必须安装 `requests` 模块**：
```bash
pip install requests
```

---

### 1. 修改配置文件
在运行前，请编辑 `getBiliBiliRTMPCode_CLI.py` 文件：
- **填写你的 Cookie**：替换 `common_cookies = ""` 中的内容（需用双引号包裹）。[在代码的第33行]
- **修改房间号**：将 `start_data` 和 `stop_data` 中的 `room_id` 改为你的直播间**长**房间号。[在代码的第50行与70行]

### 2. 执行命令
支持两种操作：
```bash
# 开播（获取推流码）
python getBiliBiliRTMPCode_CLI.py start

# 关播
python getBiliBiliRTMPCode_CLI.py stop
```

---

## 💡 输出示例
成功开播后会显示如下信息：
```
=== 直播推流信息 ===
1. RTMP地址: rtmp://xxxxx
2. 推流码: xxxxx
3. 完整推流地址: rtmp://xxxxx/xxxxx
4. 运营商: 电信
5. 身份码: xxxxx
```

---

## ⚠️ 注意事项
1. **Cookie 安全**：
   - 不要泄露你的 Cookie！它等同于账号密码。
   - 使用后建议清除文件中的 Cookie 或妥善保存脚本。

2. **房间号**：
   - 确保 `start_data` 和 `stop_data` 中的 `room_id` 一致。

3. **错误处理**：
   - 如果开播失败，会直接返回 B站API 的原始错误信息。



## 手动编译GUI指南

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


