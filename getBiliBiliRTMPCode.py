import requests
from urllib.parse import parse_qs
import tkinter as tk
from tkinter import messagebox, ttk
import sys
import re
import pyperclip
class BiliLiveGetCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("B站直播获取推流码工具")
        
        # DPI自适应设置
        self.root.tk.call('tk', 'scaling', 1.33)  # 适配高DPI屏幕
        self.root.option_add('*Font', ('Microsoft YaHei', 10))  # 使用系统默认字体
        
        # 变量初始化
        self.cookies = ""
        self.room_id = ""
        self.csrf_value = ""
        self.locked = False
        
        # 创建UI
        self.create_widgets()
        
        # 窗口自适应
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())
        
    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cookie输入框
        tk.Label(main_frame, text="Cookie:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.cookie_entry = tk.Entry(main_frame, width=50)
        self.cookie_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        
        # 房间号输入框
        tk.Label(main_frame, text="房间号:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.room_id_entry = tk.Entry(main_frame, width=20)
        self.room_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 锁定/解锁按钮
        self.lock_button = tk.Button(main_frame, text="锁定", command=self.toggle_lock)
        self.lock_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # 操作按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 开播按钮
        self.start_button = tk.Button(button_frame, text="开播", command=self.start_live, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # 关播按钮
        self.stop_button = tk.Button(button_frame, text="关播", command=self.stop_live, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # 状态标签
        self.status_label = tk.Label(main_frame, text="请先输入Cookie和房间号，然后点击锁定", fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 输出文本框
        self.output_text = tk.Text(main_frame, height=15, width=60, state=tk.DISABLED)
        self.output_text.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # 滚动条
        scrollbar = tk.Scrollbar(main_frame, command=self.output_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # 复制按钮框架
        copy_buttons_frame = tk.Frame(main_frame)
        copy_buttons_frame.grid(row=6, column=0, columnspan=2, pady=5)
        
        # 复制按钮
        tk.Button(copy_buttons_frame, text="复制推流地址", 
                command=lambda: self.copy_from_output("RTMP地址")).pack(side=tk.LEFT, padx=5)
        tk.Button(copy_buttons_frame, text="复制推流码", 
                command=lambda: self.copy_from_output("推流码")).pack(side=tk.LEFT, padx=5)
        tk.Button(copy_buttons_frame, text="复制身份码", 
                command=lambda: self.copy_from_output("身份码")).pack(side=tk.LEFT, padx=5)
        
        # 网格布局配置
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
    
    def copy_from_output(self, prefix):
        """从输出文本中复制指定前缀的内容"""
        content = self.output_text.get("1.0", tk.END)
        pattern = re.compile(rf"{prefix}:\s*(.*?)(?:\n|$)")
        match = pattern.search(content)
        
        if match:
            value = match.group(1).strip()
            pyperclip.copy(value)
            self.log_output(f"已复制 {prefix}: {value}")
        else:
            self.log_output(f"未找到 {prefix} 信息")
    
    def toggle_lock(self):
        if not self.locked:
            # 尝试锁定
            self.cookies = self.cookie_entry.get().strip()
            self.room_id = self.room_id_entry.get().strip()
            
            if not self.cookies or not self.room_id:
                messagebox.showerror("错误", "请填写完整的Cookie和房间号")
                return
            
            try:
                parsed_cookies = parse_cookies(self.cookies)
                self.csrf_value = get_csrf_from_cookies(parsed_cookies)
                
                if not self.csrf_value:
                    messagebox.showerror("错误", "Cookie中缺少bili_jct(CSRF Token)")
                    return
                
                # 锁定成功
                self.locked = True
                self.lock_button.config(text="解锁")
                self.cookie_entry.config(state=tk.DISABLED)
                self.room_id_entry.config(state=tk.DISABLED)
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.NORMAL)
                self.status_label.config(text="已锁定，可以操作", fg="green")
                self.log_output("已锁定，可以操作")
                
            except Exception as e:
                messagebox.showerror("错误", f"解析Cookie失败: {str(e)}")
        else:
            # 解锁
            self.locked = False
            self.lock_button.config(text="锁定")
            self.cookie_entry.config(state=tk.NORMAL)
            self.room_id_entry.config(state=tk.NORMAL)
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="已解锁，请重新输入", fg="blue")
            self.log_output("已解锁，请重新输入")
    
    def log_output(self, message):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def start_live(self):
        self.log_output("正在尝试开播...")
        
        try:
            # 准备开播数据
            start_data = {
                'room_id': self.room_id,
                'platform': 'pc',
                'area_v2': '89',  # 89_cs:go分区 236_单机游戏·主机游戏
                'backup_stream': '0',
                'csrf_token': self.csrf_value,
                'csrf': self.csrf_value,
            }
            
            identity_code_data = {
                'action': 1,
                'csrf_token': self.csrf_value,
                'csrf': self.csrf_value,
            }
            
            # 准备请求头
            common_headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'cookie': self.cookies,
                'origin': 'https://link.bilibili.com',
                'priority': 'u=1, i',
                'referer': 'https://link.bilibili.com/p/center/index',
                'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A?Brand";v="8", "Chromium";v="135"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
            }
            
            # 1. 先执行开播
            live_response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/startLive',
                headers=common_headers,
                data=start_data
            ).json()
            
            # 2. 获取身份码
            identity_code_response = requests.post(
                'https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode',
                headers=common_headers,
                data=identity_code_data
            ).json()
            
            identity_code = identity_code_response['data']['code'] if identity_code_response['code'] == 0 else None
            
            # 3. 处理结果
            if live_response['code'] == 0:
                rtmp_addr = live_response['data']['rtmp']['addr']
                stream_key = live_response['data']['rtmp']['code']
                isp = live_response['data']['up_stream_extra']['isp']
                full_rtmp_url = f"{rtmp_addr}{stream_key}"
                
                # 记录结果
                self.log_output("\n=== 直播推流信息 ===")
                self.log_output(f"1. RTMP地址: {rtmp_addr}")
                self.log_output(f"2. 推流码: {stream_key}")
                self.log_output(f"3. 完整推流地址: {full_rtmp_url}")
                self.log_output(f"4. 运营商: {isp}")
                if identity_code:
                    self.log_output(f"5. 身份码: {identity_code}")
                
                messagebox.showinfo("成功", "开播成功！")
            else:
                self.log_output(f"开播失败: {live_response}")
                messagebox.showerror("错误", f"开播失败: {live_response.get('message', '未知错误')}")
                
        except Exception as e:
            self.log_output(f"开播过程中出错: {str(e)}")
            messagebox.showerror("错误", f"开播过程中出错: {str(e)}")
    
    def stop_live(self):
        self.log_output("正在尝试关播...")
        
        try:
            # 准备关播数据
            stop_data = {
                'room_id': self.room_id,
                'platform': 'pc',
                'csrf_token': self.csrf_value,
                'csrf': self.csrf_value,
            }
            
            # 准备请求头
            common_headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'cookie': self.cookies,
                'origin': 'https://link.bilibili.com',
                'priority': 'u=1, i',
                'referer': 'https://link.bilibili.com/p/center/index',
                'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A?Brand";v="8", "Chromium";v="135"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
            }
            
            # 执行关播
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/stopLive',
                headers=common_headers,
                data=stop_data
            ).json()
            
            if response['code'] == 0:
                self.log_output("关播成功")
                messagebox.showinfo("成功", "关播成功！")
            else:
                self.log_output(f"关播失败: {response}")
                messagebox.showerror("错误", f"关播失败: {response.get('message', '未知错误')}")
                
        except Exception as e:
            self.log_output(f"关播过程中出错: {str(e)}")
            messagebox.showerror("错误", f"关播过程中出错: {str(e)}")

def parse_cookies(cookie_str):
    """从cookie字符串中解析出各个键值对"""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    return cookies

def get_csrf_from_cookies(cookies):
    """从cookies中提取csrf (bili_jct)"""
    return cookies.get('bili_jct', '')

if __name__ == '__main__':
    root = tk.Tk()
    
    # Windows系统DPI感知
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    app = BiliLiveGetCodeApp(root)
    root.mainloop()