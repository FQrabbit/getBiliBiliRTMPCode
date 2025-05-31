import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from core.live_controller import BiliLiveController
import base64

class BiliBridge(QObject):
    """
    QML与Python的桥接类
    职责：处理UI交互信号，调用核心逻辑
    """
    statusChanged = Signal(str, str)  # (message, color)
    outputLogged = Signal(str)       # 日志输出
    operationResult = Signal(str, str)  # (title, message)
    configLoaded = Signal(str, str)  # 新增信号，加载配置后传递给QML
    roomTitleLoaded = Signal(str)  # 新增信号
    currentAreaIdLoaded = Signal(int) # 新增信号，加载当前分区ID后传递给QML
    allAreasLoaded = Signal(list) # 新增信号，加载所有分区类型列表 (字符串列表)
    filteredAreasLoaded = Signal(list) # 新增信号，加载过滤后的具体分区列表 (字符串列表)
    currentAreaInfoLoaded = Signal(int, str) # 新增信号，加载当前分区类型ID和名称 (已改为发送名称)
    currentAreaNamesLoaded = Signal(str, str) # 新增信号，加载当前分区类型名称和具体分区名称

    def __init__(self):
        super().__init__()
        self._controller = BiliLiveController()
        self._config_path = Path(__file__).parent / 'data'
        self._all_area_data = None # 用于缓存所有分区数据
        self._area_types_names = [] # 用于QML分区类型ComboBox的模型 (名称列表)
        self._areas_by_type_names = {} # 用于按分区类型存储具体分区 (名称列表)
        self._area_name_to_id = {} # 用于分区名称到ID的映射
        self._current_area_id = None # 保存当前房间的area_id

        self.load_config()  # 启动时自动加载

    @Slot(str, str, str)
    def start_live(self, cookies, room_id, area_name):
        """处理开播请求"""
        if not (cookies and room_id):
            self.outputLogged.emit("错误: 请填写完整的Cookie和房间号")
            return
        self._controller.cookies = cookies
        self._controller.room_id = room_id
        # 自动提取csrf
        parsed = self._controller.parse_cookies(cookies)
        csrf = self._controller.get_csrf_from_cookies(parsed)
        if not csrf:
            self.outputLogged.emit("开播失败: csrf 校验失败（Cookie中缺少bili_jct）")
            self.operationResult.emit("开播失败", "csrf 校验失败（Cookie中缺少bili_jct）")
            return
        self._controller.csrf_value = csrf

        # 动态设置分区ID
        area_id = None
        if area_name:
            area_id = self._area_name_to_id.get(area_name)
        if area_id is None:
            area_id = self._current_area_id
        self._controller.current_area_id = area_id

        self.outputLogged.emit("正在请求开播...")
        result = self._controller.start_live()
        if result['success']:
            info = [
                "\n=== 推流信息 ===",
                f"RTMP地址: {result['rtmp_addr']}",
                f"推流码: {result['stream_key']}",
                f"完整推流地址: {result['rtmp_addr']}{result['stream_key']}",
                f"运营商: {result['isp']}"
            ]
            if result.get('identity_code'):
                info.append(f"身份码: {result['identity_code']}")
            info_str = "\n".join(info)
            self.outputLogged.emit(info_str)
            self.operationResult.emit("开播成功", info_str)
        else:
            error_msg = result.get('error', '未知错误')
            self.outputLogged.emit(f"开播失败: {error_msg}")
            self.operationResult.emit("开播失败", error_msg)

    @Slot(str, str)
    def stop_live(self, cookies, room_id):
        """处理关播请求"""
        if not (cookies and room_id):
            self.outputLogged.emit("错误: 请填写完整的Cookie和房间号")
            return
        self._controller.cookies = cookies
        self._controller.room_id = room_id
        # 自动提取csrf
        parsed = self._controller.parse_cookies(cookies)
        csrf = self._controller.get_csrf_from_cookies(parsed)
        if not csrf:
            self.outputLogged.emit("关播失败: csrf 校验失败（Cookie中缺少bili_jct）")
            self.operationResult.emit("关播失败", "csrf 校验失败（Cookie中缺少bili_jct）")
            return
        self._controller.csrf_value = csrf
        self.outputLogged.emit("正在请求关播...")
        result = self._controller.stop_live()
        if result['success']:
            self.outputLogged.emit("关播成功")
            self.operationResult.emit("成功", "直播已结束")
        else:
            error_msg = result.get('error', '未知错误')
            self.outputLogged.emit(f"关播失败: {error_msg}")
            self.operationResult.emit("关播失败", error_msg)

    @Slot(str)
    def copyToClipboard(self, text: str):
        """统一剪贴板操作"""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self.outputLogged.emit(f"已复制: {text[:20]}...")  # 防止输出过长

    @Slot()
    def check_live_status(self):
        """检查直播状态"""
        cookies = self._controller.cookies
        room_id = self._controller.room_id
        if not (cookies and room_id):
            return
        
        try:
            status = self._controller.get_live_status()
            if status['is_live']:
                self.statusChanged.emit("直播中", "green")
            else:
                self.statusChanged.emit("未开播", "blue")
        except Exception as e:
            self.statusChanged.emit(f"状态检查失败: {str(e)}", "red")

    @Slot(str, str)
    def save_config(self, cookies, room_id):
        try:
            # 简单base64加密
            data = f'{cookies}\n{room_id}'
            encoded = base64.b64encode(data.encode('utf-8'))
            with open(self._config_path, 'wb') as f:
                f.write(encoded)
            self.outputLogged.emit('配置已保存')
        except Exception as e:
            self.outputLogged.emit(f'保存配置失败: {str(e)}')

    @Slot()
    def load_config(self):
        try:
            if not self._config_path.exists():
                return
            with open(self._config_path, 'rb') as f:
                encoded = f.read()
            decoded = base64.b64decode(encoded).decode('utf-8')
            cookies, room_id = decoded.split('\n', 1)
            self.configLoaded.emit(cookies, room_id)
            self.outputLogged.emit('配置已加载')
        except Exception as e:
            self.outputLogged.emit(f'加载配置失败: {str(e)}')

    @Slot(str, str)
    def get_room_title(self, cookies, room_id):
        try:
            self._controller.cookies = cookies
            self._controller.room_id = room_id
            parsed = self._controller.parse_cookies(cookies)
            csrf = self._controller.get_csrf_from_cookies(parsed)
            if not csrf:
                self.outputLogged.emit("获取标题失败: Cookie中缺少bili_jct")
                return
            self._controller.csrf_value = csrf
            title, area_id, ok, msg = self._controller.get_room_title() # 解包4个返回值
            if ok:
                self.roomTitleLoaded.emit(title)
                self._current_area_id = area_id # 保存当前area_id

                # 如果分区数据已加载，尝试选中当前分区
                if self._all_area_data:
                     self._select_current_area() # 调用选中逻辑

            self.outputLogged.emit(msg)
        except Exception as e:
            self.outputLogged.emit(f"获取标题失败: {str(e)}")

    @Slot(str, str, str)
    def update_room_area(self, cookies, room_id, area_name): # area_name作为参数
        """修改直播间分区"""
        try:
            self._controller.cookies = cookies
            self._controller.room_id = room_id
            parsed = self._controller.parse_cookies(cookies)
            csrf = self._controller.get_csrf_from_cookies(parsed)
            if not csrf:
                self.outputLogged.emit("修改分区失败: Cookie中缺少bili_jct")
                return
            self._controller.csrf_value = csrf

            # 根据分区名称查找area_id
            area_id = self._area_name_to_id.get(area_name)
            if area_id is None:
                 self.outputLogged.emit(f"修改分区失败: 未找到分区 {area_name} 对应的ID")
                 return

            # 调用core的修改分区方法
            ok, msg = self._controller.update_room_area(area_id)
            self.outputLogged.emit(msg)

            # 如果修改成功，更新当前显示的area_id和名称 (通过重新获取标题触发选中逻辑)
            if ok:
                 # 重新获取标题，触发选中逻辑更新UI
                 self.get_room_title(self._controller.cookies, self._controller.room_id)

        except Exception as e:
            self.outputLogged.emit(f"修改分区失败: {str(e)}")

    @Slot(str, str, str)
    def update_room_title(self, cookies, room_id, title):
        try:
            self._controller.cookies = cookies
            self._controller.room_id = room_id
            parsed = self._controller.parse_cookies(cookies)
            csrf = self._controller.get_csrf_from_cookies(parsed)
            if not csrf:
                self.outputLogged.emit("修改标题失败: Cookie中缺少bili_jct")
                return
            self._controller.csrf_value = csrf
            ok, msg = self._controller.update_room_title(title)
            self.outputLogged.emit(msg)
        except Exception as e:
            self.outputLogged.emit(f"修改标题失败: {str(e)}")

    @Slot()
    def get_all_areas(self):
        """获取所有分区列表并处理"""
        try:
            data, ok, msg = self._controller.get_all_areas()
            self.outputLogged.emit(msg)
            if ok and data and data.get('data'):
                self._all_area_data = data['data']
                self._area_types_names = []
                self._areas_by_type_names = {}
                self._area_name_to_id = {}

                for area_type in self._all_area_data:
                    type_id = area_type.get('id', 0)
                    type_name = area_type.get('name', '')
                    if type_id and type_name:
                        self._area_types_names.append(type_name) # 只添加名称
                        # 存储具体分区名称和ID映射
                        self._areas_by_type_names[type_name] = []
                        for area in area_type.get('list', []):
                            area_id = area.get('id', 0)
                            area_name = area.get('name', '')
                            if area_id and area_name:
                                self._areas_by_type_names[type_name].append(area_name) # 只添加名称
                                self._area_name_to_id[area_name] = area_id # 存储名称到ID的映射

                # 发送分区类型名称列表给QML
                self.allAreasLoaded.emit(self._area_types_names)

                # 如果已加载配置且有当前area_id，尝试选中当前分区
                if self._current_area_id is not None:
                     self._select_current_area() # 调用选中逻辑

            elif not ok:
                 self.outputLogged.emit(f"获取分区列表失败: {msg}")

        except Exception as e:
            self.outputLogged.emit(f"获取分区列表失败: {str(e)}")

    @Slot(str) # 接收分区类型名称
    def filter_areas(self, area_type_name):
        """根据分区类型名称过滤具体分区名称列表并发送给QML"""
        if self._areas_by_type_names and area_type_name in self._areas_by_type_names:
            self.filteredAreasLoaded.emit(self._areas_by_type_names[area_type_name])
        else:
            self.filteredAreasLoaded.emit([]) # 发送空列表

    def _select_current_area(self):
        """根据当前area_id查找对应的分区类型名称和具体分区名称，并发送信号给QML选中"""
        if self._all_area_data and self._current_area_id is not None:
             for area_type in self._all_area_data:
                 for area in area_type.get('list', []):
                     if area.get('id', 0) == self._current_area_id:
                         area_type_name = area_type.get('name', '')
                         area_name = area.get('name', '')
                         if area_type_name and area_name:
                            self.currentAreaNamesLoaded.emit(area_type_name, area_name)
                            # 过滤出具体分区列表并发送给QML，以便第二个ComboBox能选中
                            self.filter_areas(area_type_name)
                         return

def main():
    # 初始化Qt应用
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # 配置QML加载路径（兼容开发和生产环境）
    qml_path = Path(__file__).parent / "ui/qml/Windows/MainWindow.qml"
    if not qml_path.exists():
        # 尝试从项目根目录查找（适用于某些IDE的工作目录设置）
        qml_path = Path.cwd() / "ui/qml/Windows/MainWindow.qml"
        if not qml_path.exists():
            print(f"错误: 未找到QML文件 {qml_path}")
            sys.exit(1)

    # 注册桥接对象（注意对象命名与QML中一致）
    bridge = BiliBridge()
    engine.rootContext().setContextProperty("biliBridge", bridge)

    # 加载QML界面（转换为绝对路径）
    engine.load(qml_path.absolute().as_uri())
    
    if not engine.rootObjects():
        print("错误: QML加载失败，请检查：")
        print(f"1. QML文件路径: {qml_path}")
        print("2. QML文件语法错误")
        sys.exit(1)

    # 启动事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
