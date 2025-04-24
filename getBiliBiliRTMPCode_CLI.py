import requests
import argparse
from urllib.parse import parse_qs

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

# ※※※复制你的cookie在下面，注意放在""里※※※
common_cookies = ""
parsed_cookies = parse_cookies(common_cookies)
csrf_value = get_csrf_from_cookies(parsed_cookies)

#浏览器UA信息，可不改
common_headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'cookie': common_cookies,
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

# 开播参数
start_data = {
    'room_id': '34348',  # 填自己的room_id(长房间号)
    'platform': 'pc',
    'area_v2': '89', # 89_cs:go分区 236_单机游戏·主机游戏
    'backup_stream': '0',
    'csrf_token': csrf_value,  # 自动从cookies提取
    'csrf': csrf_value,  # 同上
}

# 关播参数
stop_data = {
    'room_id': '34348',  # 一样，改room_id(长房间号)
    'platform': 'pc',
    'csrf_token': csrf_value,  # 自动从cookies提取
    'csrf': csrf_value,  # 同上
}

# 身份码参数
identity_code_data = {
    'action': 1,
    'csrf_token': csrf_value,  # 自动从cookies提取
    'csrf': csrf_value,  # 同上
}

def get_identity_code():
    """获取身份码"""
    response = requests.post(
        'https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode',
        headers=common_headers,
        data=identity_code_data
    ).json()
    
    if response['code'] == 0:
        return response['data']['code']
    else:
        print("获取身份码失败:", response)
        return None
def start_live():
    """开播函数"""
    # 1. 先执行开播
    live_response = requests.post(
        'https://api.live.bilibili.com/room/v1/Room/startLive',
        headers=common_headers,
        data=start_data
    ).json()
    
    # 2. 获取身份码
    identity_code = get_identity_code()
    
    # 3. 处理结果
    if live_response['code'] == 0:
        rtmp_addr = live_response['data']['rtmp']['addr']
        stream_key = live_response['data']['rtmp']['code']
        isp = live_response['data']['up_stream_extra']['isp']
        full_rtmp_url = f"{rtmp_addr}{stream_key}"
        
        # 格式化输出
        print("\n=== 直播推流信息 ===")
        print(f"1. RTMP地址: {rtmp_addr}")
        print(f"2. 推流码: {stream_key}")
        print(f"3. 完整推流地址: {full_rtmp_url}")
        print(f"4. 运营商: {isp}")
        if identity_code:
            print(f"5. 身份码: {identity_code}")
        print()
        
        # 返回完整信息
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
    response = requests.post(
        'https://api.live.bilibili.com/room/v1/Room/stopLive',
        headers=common_headers,
        data=stop_data
    ).json()
    print("关播结果:", response)
    return response

def main():
    parser = argparse.ArgumentParser(description='B站获取推流码小工具')
    parser.add_argument('action', choices=['start', 'stop'], help='执行动作: start(开播) 或 stop(关播)')
    
    args = parser.parse_args()
    
    if not common_cookies:
        raise ValueError("请填写 Bilibili Cookie！")

    if args.action == 'start':
        start_live()
    elif args.action == 'stop':
        stop_live()
if __name__ == '__main__':
    main()