import requests
import argparse
import time
import hashlib
import uuid
from urllib.parse import parse_qs

# cookie字符串中解析出各个键值对
def parse_cookies(cookie_str):
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key] = value
    return cookies
# 从cookies中提取csrf (bili_jct)
def get_csrf_from_cookies(cookies):
    return cookies.get('bili_jct', '')

# 签名生成函数
def generate_sign(params, appkey):
    param_keys = sorted(params.keys())
    query = '&'.join([f"{k}={params[k]}" for k in param_keys])
    sign_str = query + appkey
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

# TraceID生成函数
def generate_trace_id():
    return f"PC_LINK:{str(uuid.uuid4()).upper()}:{int(time.time() * 1000)}"

# ※※※复制你的cookie在下面，注意放在""里※※※
common_cookies = ""
parsed_cookies = parse_cookies(common_cookies)
csrf_value = get_csrf_from_cookies(parsed_cookies)

# 直播姬客户端UA
common_headers = {
    'User-Agent': 'LiveHime/7.7.0.8681 os/Windows pc_app/livehime build/8681 osVer/10.0_x86_64',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': common_cookies,
    'X-Event-TraceID': generate_trace_id(),  # 动态TraceID头
    'Connection': 'keep-alive',
}

# 开播参数
def get_start_data():
    """动态生成开播参数（含签名和时间戳）"""
    base_data = {
        'room_id': '34348',  # 填自己的room_id(长房间号)
        'platform': 'pc_link',
        'area_v2': '89',  # 89_cs:go分区 236_单机游戏·主机游戏
        'type': '2',
        'backup_stream': '0',
        'csrf_token': csrf_value,  # 自动从cookies提取
        'csrf': csrf_value,  # 同上
        'access_key': '',
        'appkey': 'aae92bc66f3edfab',  # 可能日后需要更改
        'build': '8681',  # 客户端版本号
        'version': '7.7.0.8681',  # 版本号
        'ts': int(time.time()),  # 当前时间戳
    }
    base_data['sign'] = generate_sign(base_data, base_data['appkey'])  # 计算签名
    return base_data

# 关播参数
def get_stop_data():
    """动态生成关播参数"""
    base_data = {
        'room_id': '34348',  # 一样，改room_id(长房间号)
        'platform': 'pc_link',
        'csrf_token': csrf_value,
        'csrf': csrf_value,
        'access_key': '',
        'appkey': 'aae92bc66f3edfab',
        'build': '8681',
        'version': '7.7.0.8681',
        'ts': int(time.time()),
    }
    base_data['sign'] = generate_sign(base_data, base_data['appkey'])
    return base_data

# 身份码参数
def get_identity_code_data():
    return {
        'action': 1,
        'platform': 'pc_link',
        'csrf_token': csrf_value,
        'csrf': csrf_value,
        'build': '8681',
        'appkey': 'aae92bc66f3edfab',
        'ts': int(time.time()),
    }

def get_identity_code():
    """获取身份码"""
    data = get_identity_code_data()
    data['sign'] = generate_sign(data, data['appkey'])
    
    response = requests.post(
        'https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode',
        headers={**common_headers, 'X-Event-TraceID': generate_trace_id()},
        data=data
    ).json()
    
    if response['code'] == 0:
        return response['data']['code']
    else:
        print("获取身份码失败:", response)
        return None

def start_live():
    """开播函数"""
    # 1. 获取动态参数
    start_params = get_start_data()
    
    # 2. 执行开播请求
    live_response = requests.post(
        'https://api.live.bilibili.com/room/v1/Room/startLive',
        headers={**common_headers, 'X-Event-TraceID': generate_trace_id()},
        data=start_params
    ).json()
    
    # 3. 获取身份码
    identity_code = get_identity_code()
    
    # 4. 处理结果
    if live_response['code'] == 0:
        rtmp_addr = live_response['data']['rtmp']['addr']
        stream_key = live_response['data']['rtmp']['code']
        isp = live_response['data']['up_stream_extra']['isp']
        full_rtmp_url = f"{rtmp_addr}{stream_key}"
        
        print("\n=== 直播推流信息 ===")
        print(f"1. RTMP地址: {rtmp_addr}")
        print(f"2. 推流码: {stream_key}")
        print(f"3. 完整推流地址: {full_rtmp_url}")
        print(f"4. 运营商: {isp}")
        if identity_code:
            print(f"5. 身份码: {identity_code}")
        print()
        
        return {
            'live_response': live_response,
            'rtmp_addr': rtmp_addr,
            'stream_key': stream_key,
            'full_rtmp_url': full_rtmp_url,
            'isp': isp,
            'identity_code': identity_code
        }
    else:
        print("开播失败:", live_response)
        return live_response

def stop_live():
    """关播函数"""
    stop_params = get_stop_data()
    response = requests.post(
        'https://api.live.bilibili.com/room/v1/Room/stopLive',
        headers={**common_headers, 'X-Event-TraceID': generate_trace_id()},
        data=stop_params
    ).json()
    print("关播结果:", response)
    return response

def main():
    parser = argparse.ArgumentParser(
        description='B站获取直播推流码工具 Bilibili Live Streaming Key Retrieval Tool',
        usage='python getBiliBiliRTMPCode_CLI.py [start|stop]',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'action', 
        choices=['start', 'stop'], 
        nargs='?',
        help='''可选动作:
  start - 开播并获取推流地址 Start streaming and get the push URL
  stop  - 关闭当前直播 Close the current live stream
'''
    )
    
    args = parser.parse_args()
    
    # 无参数时显示帮助并退出
    if args.action is None:
        parser.print_help()
        return

    if not common_cookies:
        raise ValueError("请填写 Bilibili Cookie！")

    if args.action == 'start':
        start_live()
    elif args.action == 'stop':
        stop_live()

if __name__ == '__main__':
    main()