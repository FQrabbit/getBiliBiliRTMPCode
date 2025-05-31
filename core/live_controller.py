# core\live_controller.py
import requests
from urllib.parse import parse_qs
import re
import time
import hashlib
import uuid

class BiliLiveController:
    def __init__(self):
        self.cookies = ""
        self.room_id = ""
        self.csrf_value = ""
        self.locked = False
        self.current_area_id = None
        
    def parse_cookies(self, cookie_str):
        """从cookie字符串中解析出各个键值对"""
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key] = value
        return cookies

    def get_csrf_from_cookies(self, cookies):
        """从cookies中提取csrf (bili_jct)"""
        return cookies.get('bili_jct', '')

    def generate_trace_id(self):
        """TraceID生成函数"""
        return f"PC_LINK:{str(uuid.uuid4()).upper()}:{int(time.time() * 1000)}"

    def generate_common_headers(self):
        """生成通用的请求头"""
        return {
            'User-Agent': 'LiveHime/7.7.0.8681 os/Windows pc_app/livehime build/8681 osVer/10.0_x86_64',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': self.cookies,
            'X-Event-TraceID': self.generate_trace_id(),
            'Connection': 'keep-alive',
        }

    def generate_sign(self, params, appkey):
        """签名生成函数"""
        param_keys = sorted(params.keys())
        query = '&'.join([f"{k}={params[k]}" for k in param_keys])
        sign_str = query + appkey
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def get_start_data(self):
        """动态生成开播参数"""
        area_id = str(self.current_area_id) if self.current_area_id else '89'
        base_data = {
            'room_id': self.room_id,
            'platform': 'pc_link',
            'area_v2': area_id,
            'type': '2',
            'backup_stream': '0',
            'csrf_token': self.csrf_value,
            'csrf': self.csrf_value,
            'access_key': '',
            'appkey': 'aae92bc66f3edfab',
            'build': '8681',
            'version': '7.7.0.8681',
            'ts': int(time.time()),
        }
        base_data['sign'] = self.generate_sign(base_data, base_data['appkey'])
        return base_data

    def get_stop_data(self):
        """动态生成关播参数"""
        base_data = {
            'room_id': self.room_id,
            'platform': 'pc_link',
            'csrf_token': self.csrf_value,
            'csrf': self.csrf_value,
            'access_key': '',
            'appkey': 'aae92bc66f3edfab',
            'build': '8681',
            'version': '7.7.0.8681',
            'ts': int(time.time()),
        }
        base_data['sign'] = self.generate_sign(base_data, base_data['appkey'])
        return base_data

    def get_identity_code_data(self):
        """身份码参数"""
        return {
            'action': 1,
            'platform': 'pc_link',
            'csrf_token': self.csrf_value,
            'csrf': self.csrf_value,
            'build': '8681',
            'appkey': 'aae92bc66f3edfab',
            'ts': int(time.time()),
        }

    def get_identity_code(self):
        """获取身份码"""
        data = self.get_identity_code_data()
        data['sign'] = self.generate_sign(data, data['appkey'])
        
        response = requests.post(
            'https://api.live.bilibili.com/xlive/open-platform/v1/common/operationOnBroadcastCode',
            headers={**self.generate_common_headers(), 'X-Event-TraceID': self.generate_trace_id()},
            data=data
        ).json()
        
        if response['code'] == 0:
            return response['data']['code']
        return None

    def start_live(self):
        """开播函数"""
        try:
            start_params = self.get_start_data()
            
            live_response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/startLive',
                headers={**self.generate_common_headers(), 'X-Event-TraceID': self.generate_trace_id()},
                data=start_params
            ).json()
            
            identity_code = self.get_identity_code()
            
            result = {'success': False}
            if live_response['code'] == 0:
                result = {
                    'success': True,
                    'rtmp_addr': live_response['data']['rtmp']['addr'],
                    'stream_key': live_response['data']['rtmp']['code'],
                    'full_rtmp_url': f"{live_response['data']['rtmp']['addr']}{live_response['data']['rtmp']['code']}",
                    'isp': live_response['data']['up_stream_extra']['isp'],
                    'identity_code': identity_code
                }
            else:
                result['error'] = live_response.get('message', '未知错误')
            
            return result
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop_live(self):
        """关播函数"""
        try:
            stop_params = self.get_stop_data()
            response = requests.post(
                'https://api.live.bilibili.com/room/v1/Room/stopLive',
                headers={**self.generate_common_headers(), 'X-Event-TraceID': self.generate_trace_id()},
                data=stop_params
            ).json()
            
            if response['code'] == 0:
                return {'success': True}
            else:
                return {'success': False, 'error': response.get('message', '未知错误')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_request(self, url, data, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self.generate_common_headers(), data=data)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1 * (attempt + 1))  # 指数退避

    def auto_reconnect(self):
        """自动重连机制"""
        if not self.is_connected:
            try:
                self.start_live()
                return True
            except Exception as e:
                self.logger.error(f"自动重连失败: {str(e)}")
                return False
        return True

    def get_room_title(self):
        """获取当前直播间标题和分区ID"""
        try:
            url = f'https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo?room_ids={self.room_id}&req_biz=link-center'
            headers = self.generate_common_headers()
            headers.update({
                'origin': 'https://link.bilibili.com',
                'referer': 'https://link.bilibili.com/p/center/index',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            })
            resp = requests.get(url, headers=headers)
            res = resp.json()
            if res.get('code') == 0:
                room_info = res['data']['by_room_ids'].get(str(self.room_id), {})
                title = room_info.get('title', '')
                area_id = room_info.get('area_id', 0)
                return title, area_id, True, '直播间标题和分区已获取'
            else:
                return '', 0, False, res.get('message', '未知错误')
        except Exception as e:
            return '', 0, False, str(e)

    def get_all_areas(self):
        """获取所有直播分区列表"""
        try:
            url = 'https://api.live.bilibili.com/xlive/web-interface/v1/index/getWebAreaList?source_id=2'
            headers = self.generate_common_headers()
            headers.update({
                'origin': 'https://link.bilibili.com',
                'referer': 'https://link.bilibili.com/p/center/index',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            })
            resp = requests.get(url, headers=headers)
            res = resp.json()
            if res.get('code') == 0:
                return res['data'], True, '分区列表获取成功'
            else:
                return None, False, res.get('message', '未知错误')
        except Exception as e:
            return None, False, str(e)

    def update_room_title(self, new_title):
        """修改当前直播间标题"""
        try:
            url = 'https://api.live.bilibili.com/room/v1/Room/update'
            headers = self.generate_common_headers()
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://link.bilibili.com',
                'referer': 'https://link.bilibili.com/p/center/index',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            })

            data = {
                'platform': 'pc',
                'room_id': self.room_id,
                'title': new_title,
                'csrf_token': self.csrf_value,
                'csrf': self.csrf_value,
            }

            resp = requests.post(
                url,
                headers=headers,
                data=data
            )
            res = resp.json()
            if res.get('code') == 0:
                return True, '直播间标题修改成功'
            else:
                return False, f'修改标题失败: {res.get('message', '未知错误')}'
        except Exception as e:
            return False, f'修改标题失败: {str(e)}'

    def update_room_area(self, area_id: int):
        """修改直播间分区"""
        try:
            url = 'https://api.live.bilibili.com/room/v1/Room/update'
            # 使用通用headers，其中包含了直播姬UA
            headers = self.generate_common_headers()
            # 补充抓包中发现的必要headers
            headers.update({
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://link.bilibili.com',
                'referer': 'https://link.bilibili.com/p/center/index',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            })

            data = {
                'room_id': self.room_id,
                'area_id': area_id, # 新分区ID
                'csrf_token': self.csrf_value,
                'csrf': self.csrf_value,
            }

            resp = requests.post(
                url,
                headers=headers,
                data=data
            )
            res = resp.json()
            if res.get('code') == 0:
                return True, '直播间分区修改成功'
            else:
                return False, f'修改分区失败: {res.get('message', '未知错误')}'
        except Exception as e:
            return False, f'修改分区失败: {str(e)}'
