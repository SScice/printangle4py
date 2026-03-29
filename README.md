# printangle4py (Printangle4Linux)

这是一个基于 Python 和 `bleak` 库构建的自动化硬件监控与蓝牙打印项目。它可以无缝潜伏在你的 Linux 终端后台，实时监控并提取 Fish Shell 的历史记录，将你敲下的高价值命令通过蓝牙热敏打印机（ESC/POS 协议）实时打印出来。

## 🌟 核心功能

* **实时终端监控**：监听 `~/.local/share/fish/fish_history`，通过 `tail -f` 机制实现数据捕获。
* **蓝牙长连接与自愈**：
    * **断线重连**：内置 `_ensure_connection` 逻辑，设备断电或超出范围后，恢复时可自动重新建立连接。
    * **硬件保活机制**：针对带有自动关机机制的便携打印机，程序每隔 180 秒会自动发送一次预保留但对于大多数机器无用的 CUT 指令，重置打印机休眠倒计时。当然，如果你的机器具有切纸功能，
* **高度定制的 ESC/POS 封装**：支持文本对齐、字号调整、自动换行及切纸指令，格式输出清晰美观。

---

## 运行前需要做的：

1.下载源代码：直接download zip或者clone该项目：
```bash
git clone [https://github.com/YOUR_USERNAME/printangle4py.git](https://github.com/YOUR_USERNAME/printangle4py.git)
cd printangle4py
```
2.修改main.py中的mac地址：
```python
address = "你的打印机蓝牙MAC地址"
KEEP_ALIVE_INTERVAL = 180  # 3分钟（180秒）发一次保活指令，避开4分钟的关机点
```

## ⚙️ 部署为 Systemd 服务 (Systemctl Service)

为了让程序在开机后自动后台静默运行，我们需要将其配置为一个用户级的 Systemd 服务。

### 第一步：准备运行环境

1. 确保已安装必要的 Python 依赖（建议在虚拟环境中安装或使用系统的包管理器）：
```bash
pip install bleak
```

2.明确你的 main.py 存放路径（假设存放于 /home/你的用户名/printangle4py/main.py）。

3.确保你的 main.py 具有可执行权限：
  ```bash
  chmod +x /home/你的用户名/printangle4py/main.py
  ```

### 第二步：创建 Service 配置文件

使用你顺手的文本编辑器（如 Nano），在 /etc/systemd/system/ 目录下创建一个服务文件：
  ```bash
  sudo nano /etc/systemd/system/printangle4py.service
  ```

填入以下配置（注意将 User 和 ExecStart 里的路径替换为你自己的真实用户名和实际路径）：
  ```Ini,TOML
  [Unit]
Description=Printangle4py Bluetooth Thermal Printer Monitor
After=network.target bluetooth.target

[Service]
# 必须指定你的普通用户，因为程序需要读取该用户下的 ~/.local/share/fish/fish_history
User=你的用户名
Environment=PYTHONUNBUFFERED=1
# 如果你使用的是虚拟环境，请将 python3 替换为虚拟环境中的 python 绝对路径
ExecStart=/usr/bin/python3 /home/你的用户名/printangle4py/main.py
WorkingDirectory=/home/你的用户名/printangle4py/
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 第三步：重新加载并启动服务
保存退出后，执行以下命令让 Systemd 识别新服务，并设置为开机自启：
  ```bash
  # 1. 重新加载 systemd 守护进程
sudo systemctl daemon-reload

# 2. 启动服务
sudo systemctl start printangle4py.service

# 3. 设置为开机自启
sudo systemctl enable printangle4py.service

# 4. 查看当前运行状态和日志
sudo systemctl status printangle4py.service
  ```
