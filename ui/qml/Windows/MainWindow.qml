// MainWindow.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    title: "B站获取直播推流码工具"
    width: 900
    height: 600
    minimumWidth: 700
    minimumHeight: 480
    visible: true

    // 系统托盘支持 (仅桌面平台)
    QtObject {
        id: trayHandler
        property var trayIcon: null

        Component.onCompleted: {
            if (typeof Qt.platform.os !== "undefined" && Qt.platform.os !== "android" && Qt.platform.os !== "ios") {
                trayIcon = Qt.createQmlObject('import Qt.labs.platform 1.0; SystemTrayIcon {}', root)
                trayIcon.icon.source = "qrc:/icons/app_icon.png"
                trayIcon.tooltip = root.title
                trayIcon.visible = true

                trayIcon.onActivated.connect(function(reason) {
                    if (reason === SystemTrayIcon.Trigger) {
                        root.show()
                        root.raise()
                    }
                })
            }
        }
    }

    // 全局属性
    property string statusText: "准备就绪"
    property color statusColor: "steelblue"

    // 字体定义
    // FontLoader { id: monoFont; source: "qrc:/fonts/JetBrainsMono-Regular.ttf" }

    // 主布局：左侧导航 + 右侧内容
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // 左侧导航栏
        Rectangle {
            id: navBar
            color: "#23272e"
            width: 60
            Layout.fillHeight: true
            radius: 8
            Column {
                anchors.centerIn: parent
                spacing: 24
                // 导航按钮占位
                Rectangle { width: 36; height: 36; radius: 18; color: "#22ffffff"; anchors.horizontalCenter: parent.horizontalCenter }
                Rectangle { width: 36; height: 36; radius: 18; color: "#22ffffff"; anchors.horizontalCenter: parent.horizontalCenter }
                Rectangle { width: 36; height: 36; radius: 18; color: "#22ffffff"; anchors.horizontalCenter: parent.horizontalCenter }
            }
        }

        // 右侧主内容区
        Rectangle {
            id: shadowRect
            color: "#20000000"
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 12
            anchors.margins: 0

            Rectangle {
                id: mainContent
                anchors.fill: parent
                anchors.margins: 2
                color: "#f7f8fa"
                radius: 12
                border.color: "#e0e0e0"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 24

                    // 主体左侧：Cookie/房间号输入+直播设置
                    ColumnLayout {
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        spacing: 16

                        // 顶部卡片：Cookie和房间号输入
                        Rectangle {
                            color: "white"
                            radius: 10
                            border.color: "#e0e0e0"
                            Layout.fillWidth: true
                            height: 80
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 16
                                Text { text: "Cookie:"; color: "#333" }
                                TextField { id: cookieInput; Layout.preferredWidth: 320; placeholderText: "输入B站Cookie（包含SESSDATA和bili_jct）" }
                                Text { text: "房间号:"; color: "#333" }
                                TextField { id: roomIdInput; Layout.preferredWidth: 100; placeholderText: "房间号"; validator: IntValidator { bottom: 1 } }
                                Button { text: "保存配置"; onClicked: biliBridge.save_config(cookieInput.text, roomIdInput.text) }
                                Button { text: "加载配置"; onClicked: biliBridge.load_config() }
                            }
                        }

                        // 直播设置卡片
                        Rectangle {
                            color: "white"
                            radius: 10
                            border.color: "#e0e0e0"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 200
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 16
                                spacing: 10
                                // 分类
                                RowLayout {
                                    spacing: 8
                                    Text { text: "直播分类"; font.bold: true; color: "#333" }
                                    ComboBox {
                                        id: areaTypeComboBox
                                        Layout.preferredWidth: 180
                                        delegate: ItemDelegate {
                                            contentItem: Text { text: modelData; font.pointSize: 13 }
                                        }
                                        onCurrentIndexChanged: {
                                            if (currentIndex !== -1 && model.length > 0) {
                                                biliBridge.filter_areas(model[currentIndex])
                                            }
                                        }
                                    }
                                    ComboBox {
                                        id: areaComboBox
                                        Layout.preferredWidth: 180
                                        delegate: ItemDelegate {
                                            contentItem: Text { text: modelData; font.pointSize: 13 }
                                        }
                                        onCurrentIndexChanged: {
                                            if (currentIndex !== -1 && model.length > 0) {
                                                biliBridge.update_room_area(cookieInput.text, roomIdInput.text, model[currentIndex])
                                            }
                                        }
                                    }
                                }
                                // 房间标题
                                RowLayout {
                                    spacing: 8
                                    Text { text: "房间标题"; color: "#333" }
                                    TextField { id: roomTitleInput; Layout.preferredWidth: 220; placeholderText: "直播间标题" }
                                    Button { text: "保存"; onClicked: biliBridge.update_room_title(cookieInput.text, roomIdInput.text, roomTitleInput.text) }
                                }
                            }
                        }

                        // 操作按钮区
                        RowLayout {
                            spacing: 12
                            Button {
                                text: "开始直播"
                                onClicked: {
                                    var areaName = areaComboBox.currentIndex !== -1 ? areaComboBox.model[areaComboBox.currentIndex] : ""
                                    biliBridge.start_live(cookieInput.text, roomIdInput.text, areaName)
                                }
                            }
                            Button {
                                text: "结束直播"
                                onClicked: biliBridge.stop_live(cookieInput.text, roomIdInput.text)
                            }
                        }

                        // 日志输出卡片
                        Rectangle {
                            color: "white"
                            radius: 10
                            border.color: "#e0e0e0"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            anchors.topMargin: 8
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 6
                                Text { text: "日志输出"; font.bold: true; color: "#333" }
                                ScrollView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    TextArea { id: logOutput; readOnly: true; wrapMode: Text.Wrap }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 动画效果（示例：主内容区淡入）
    Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.InOutQuad } }
    opacity: 1

    // 消息对话框
    Dialog {
        id: resultDialog
        title: "操作结果"
        standardButtons: Dialog.Ok
        modal: true
        anchors.centerIn: parent
        enter: Transition {
            NumberAnimation { properties: "scale,opacity"; from: 0.7; to: 1; duration: 200; easing.type: Easing.OutBack }
        }
        exit: Transition {
            NumberAnimation { properties: "scale,opacity"; from: 1; to: 0.7; duration: 120; easing.type: Easing.InBack }
        }

        Column {
            width: parent.width
            spacing: 10
            Label {
                id: dialogMessage
                width: parent.width
                wrapMode: Text.Wrap
            }
            Row {
                spacing: 10
                visible: resultDialog.title === "开播成功"
                Button {
                    text: "复制RTMP地址"
                    onClicked: {
                        var rtmp = dialogMessage.text.match(/RTMP地址: (.*)/)
                        if (rtmp && rtmp[1]) biliBridge.copyToClipboard(rtmp[1])
                    }
                }
                Button {
                    text: "复制推流码"
                    onClicked: {
                        var key = dialogMessage.text.match(/推流码: (.*)/)
                        if (key && key[1]) biliBridge.copyToClipboard(key[1])
                    }
                }
                Button {
                    text: "复制身份码"
                    visible: dialogMessage.text.indexOf("身份码:") !== -1
                    onClicked: {
                        var idcode = dialogMessage.text.match(/身份码: (.*)/)
                        if (idcode && idcode[1]) biliBridge.copyToClipboard(idcode[1])
                    }
                }
            }
        }
    }

    // 连接信号
    Connections {
        target: biliBridge

        function onStatusChanged(message, color) {
            statusText = message
            statusColor = color
        }

        function onOutputLogged(message) {
            logOutput.append(message)
        }

        function onOperationResult(title, message) {
            resultDialog.title = title
            dialogMessage.text = message
            resultDialog.open()
        }

        function onConfigLoaded(cookies, roomId) {
            cookieInput.text = cookies
            roomIdInput.text = roomId
            tryLoadTitle()
        }

        function onRoomTitleLoaded(title) {
            roomTitleInput.text = title
        }

        function onAllAreasLoaded(areaTypes) { // 接收分区类型列表
            areaTypeComboBox.model = areaTypes
            // 初始时清空具体分区列表，并设置默认选中项（可选）
            areaComboBox.model = []
            areaTypeComboBox.currentIndex = -1 // 默认不选中
            areaComboBox.currentIndex = -1
            tryLoadTitle() // 分区加载后自动刷新房间信息
        }

        function onFilteredAreasLoaded(areas) { // 接收过滤后的具体分区列表
             areaComboBox.model = areas
             areaComboBox.currentIndex = -1 // 默认不选中
        }

        function onCurrentAreaNamesLoaded(areaTypeName, areaName) { // 接收当前分区类型名称和具体分区名称
             // 根据接收到的areaTypeName选中分区类型ComboBox
             for (var i = 0; i < areaTypeComboBox.model.length; ++i) {
                 if (areaTypeComboBox.model[i] === areaTypeName) {
                     areaTypeComboBox.currentIndex = i
                     // 选中分区类型后，会自动触发onCurrentIndexChanged，从而过滤并加载具体分区
                     // 此时再根据areaName选中具体分区ComboBox
                     // 延迟执行，确保具体分区模型已更新
                     Qt.callLater(function() {
                         for (var j = 0; j < areaComboBox.model.length; ++j) {
                             if (areaComboBox.model[j] === areaName) {
                                 areaComboBox.currentIndex = j
                                 break
                             }
                         }
                     })
                     break
                 }
             }
        }
    }

    function tryLoadTitle() {
        if (cookieInput.text.length > 0 && roomIdInput.text.length > 0) {
            biliBridge.get_room_title(cookieInput.text, roomIdInput.text)
        }
    }

    Component.onCompleted: {
        biliBridge.load_config()
        biliBridge.get_all_areas() // 程序启动时获取所有分区列表
    }

    // 全局按钮样式
    Component {
        id: modernButton
        Button {
            height: 44
            font.pointSize: 14
            padding: 24
            background: Rectangle {
                color: control.down ? "#4a90e2" : (control.hovered ? "#eaf3ff" : "#f5f7fa")
                border.color: control.down ? "#357ab8" : (control.hovered ? "#4a90e2" : "#e0e0e0")
                border.width: 1
                radius: 22
                Behavior on color { ColorAnimation { duration: 120 } }
            }
            contentItem: Text {
                text: control.text
                font.pointSize: 14
                color: control.down ? "white" : (control.hovered ? "#4a90e2" : "#333")
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                anchors.centerIn: parent
            }
        }
    }

    // 全局输入框样式
    Component {
        id: modernTextField
        TextField {
            height: 40
            font.pointSize: 13
            padding: 12
            background: Rectangle {
                color: "white"
                border.color: "#e0e0e0"
                border.width: 1
                radius: 12
            }
        }
    }
}