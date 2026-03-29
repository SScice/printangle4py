#!/usr/bin/env python3
import asyncio
from operator import add
import os
import time
from bleak import BleakClient

# ====================== 1. 指令码封装 (保持不变) ======================
INIT = b'\x1B\x40'
LF   = b'\x0A'
CUT  = b'\x1D\x56\x01\x00'
ALIGN_LEFT   = b'\x1B\x61\x00'
ALIGN_CENTER = b'\x1B\x61\x01'
ALIGN_RIGHT  = b'\x1B\x61\x02'
FONT_A_NORMAL = b'\x1B\x21\x00'

def font_size(n: int) -> bytes:
    return bytes([0x1D, 0x21, n * 17])

# ====================== 2. 长连接打印机类 ======================

address = "24:0A:C4:49:73:06"
KEEP_ALIVE_INTERVAL = 180  # 3分钟（180秒）发一次保活指令，避开4分钟的关机点


class BleakPrinter:
    def __init__(self, address):
        self.address = address
        self.char_uuid = "0000ff01-0000-1000-8000-00805f9b34fb"
        # 核心改动：在 Linux 下强制指定地址类型
        # 通常打印机使用 "public"，如果不行可以尝试 "random"
        self.client = BleakClient(address, address_type="random") 
        self.max_retries = 3

    async def connect(self):
        """建立连接"""
        if not self.client.is_connected:
            print(f"正在尝试连接打印机: {self.address}...")
            await self.client.connect()
            print("打印机已连接。")

    async def disconnect(self):
        """断开连接"""
        if self.client.is_connected:
            await self.client.disconnect()
            print("打印机连接已关闭。")

    async def get_status(self):
        """查看连接状态及设备基本信息"""
        print("\n" + "="*30)
        print("🔍 正在检索蓝牙设备状态...")
        
        # 1. 检查物理连接状态
        connected = self.client.is_connected
        print(f"连接状态: {'✅ 已连接' if connected else '❌ 未连接'}")
        
        if connected:
            print(f"设备地址: {self.address}")
            
            # 2. 获取 MTU (最大传输单元)
            # 这决定了你一次性能发多少字节的数据，对打印长图片很重要
            print(f"最大传输单元 (MTU): {self.client.mtu_size} bytes")
        
        print("="*30 + "\n")

    async def _ensure_connection(self):
        """内部辅助函数：确保在发送指令前处于连接状态"""
        if self.client.is_connected:
            return True

        print("⚠️ 检测到连接已断开，正在尝试自动重连...")
        for i in range(self.max_retries):
            try:
                print(f"  正在进行第 {i+1} 次尝试...")
                await self.client.connect()
                if self.client.is_connected:
                    print("✅ 重连成功！")
                    return True
            except Exception as e:
                print(f"  重连失败: {e}")
                await asyncio.sleep(1) # 等待1秒后重试
        
        print("❌ 达到最大重试次数，无法连接到打印机。")
        return False

    async def send_raw(self, data: bytes):
        """发送原始字节流（带自动重连）"""
        # 1. 发送前先确保连上了
        if await self._ensure_connection():
            try:
                await self.client.write_gatt_char(self.char_uuid, data, response=False)
            except Exception as e:
                print(f"发送数据失败: {e}")
        else:
            print("无法发送指令：连接已丢失且重连失败。")
    async def print_line(self, text: str, align=ALIGN_LEFT, size=0):
        """高层封装：打印一行文字"""
        # 按照你的逻辑：设置对齐 + 字号 + 内容 + 换行
        payload = align + font_size(size) + text.encode("gbk") + LF
        await self.send_raw(payload)
    
# ====================== 3. 业务逻辑模拟 ======================

async def test(address):
    printer = BleakPrinter(address)

    try:
        # --- 第一步：连接一次 ---

        # --- 第二步：连续发送多条指令，无需重复连接 ---
        print("正在发送批量打印任务...")
        await printer.get_status()  # 可选：先查看状态
        
        # 1. 初始化
        await printer.send_raw(INIT)
        
        # 2. 打印抬头（居中，大号字）

        await printer.send_raw(LF * 3)
        
        # 6. 切纸（如果你打印机支持）
        # await printer.send_raw(CUT)

        print("所有指令已发送完毕。")

    except Exception as e:
        print(f"发生错误: {e}")
        # --- 第三步：所有活干完了再断开 ---

async def monitor_fish_history(address,KEEP_ALIVE_INTERVAL):
    print("⏳Printangle4Linux Project by 罗宋，正在启动……")
    printer = BleakPrinter(address)
    history_path = os.path.expanduser("~/.local/share/fish/fish_history")

    # 外层循环：负责“死缠烂打”地请求连接
    while True:
        # 1. 确保连接正常（调用你之前写的 _ensure_connection）
        # 这个函数内部已经有了重试逻辑
        if not await printer._ensure_connection():
            print("⏳ 无法建立连接，10秒后重新尝试整体流程...")
            await asyncio.sleep(10)
            continue # 跳到开头，再次尝试连接

        print("✅ 打印机已就绪，开始监控 Fish 历史...")
        
        try:
            await printer.print_line("=== Fish Pro Monitor ===", align=ALIGN_CENTER)
            print(f"[{time.strftime('%H:%M:%S')}]🐠 正在深度监控: {history_path}")
            # 2. 打印抬头（居中，大号字）
            await printer.print_line("ARCHLINUX HYPRLAND", align=ALIGN_CENTER, size=1)
            await printer.send_raw(LF * 3)

            # 2. 启动 tail 进程
            process = await asyncio.create_subprocess_exec(
                'tail', '-n', '0', '-f', history_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 内层循环：负责实时处理数据
            while True:
                try:
                    print(f"[{time.strftime('%H:%M:%S')}]🐠 监控正常运行中: {history_path}")

                    # 【核心改动】等待读取，如果超过 180 秒没读到新内容，抛出 TimeoutError
                    line_bytes = await asyncio.wait_for(
                        process.stdout.readline(), 
                        timeout=KEEP_ALIVE_INTERVAL
                    )
                    
                    if not line_bytes: break
                    
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if "- cmd:" in line:
                        command = line.split("- cmd:", 1)[1].strip()
                        if command not in ['ls', 'cd', 'pwd', 'exit']:
                            print(f"[{time.strftime('%H:%M:%S')}]🔥 捕获指令: {command}")
                            await printer.print_line(f"[{time.strftime('%H:%M:%S')}]fish> {command}")
                except asyncio.TimeoutError:
                    # --- 触发保活逻辑 ---
                    if printer.client.is_connected:
                        print(f"[{time.strftime('%H:%M:%S')}] 发送保活指令...")
                        # 发送初始化指令，这不会让打印机吐纸，但会产生蓝牙通讯，重置它的关机计时器
                        # await printer.print_line(f"[{time.strftime('%H:%M:%S')}]Printangle4Linux Running......")
                        await printer.send_raw(CUT)
                    continue # 继续回到 wait_for 状态
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}]🔥 监控过程异常: {e}")
            await asyncio.sleep(5)
            # 同样会因为 while True 回到开头重新连接
if __name__ == "__main__":
    # asyncio.run(test(address))


    asyncio.run(monitor_fish_history(address,KEEP_ALIVE_INTERVAL))
