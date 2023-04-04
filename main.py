from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QDialog, QLabel, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import threading
import win32gui,win32con,win32api
import time
from pynput import keyboard,mouse
import sys
import yaml
from ctypes import cdll


class userWindowAboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('作者信息')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint) #去掉问号按钮，这你都能看出来？copilot。

        layout = QVBoxLayout(self)
        label = QLabel('作者邮箱：843773493@qq.com')
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(label)

class userWindow(QMainWindow):     #交互界面
    def __init__(self, *args, **kwargs):
        super(userWindow, self).__init__()
        self.hider = Hider()  # 中间控制器
        
        uic.loadUi("mainWindow.ui", self)   #加载ui文件
                # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("1.ico"))

        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit)
        self.tray_icon.setContextMenu(tray_menu)

        # 显示托盘图标
        self.tray_icon.show()
        
        self.button_start_close.clicked.connect(self.swith_start_close)
        self.button_hide_taskbar.toggled.connect(lambda checked: self.set_param('hide_taskbar',checked))   
        self.button_hide_desk_icon.toggled.connect(lambda checked: self.set_param('hide_iconbar',checked))
        self.button_hide_cursor.toggled.connect(lambda checked: self.set_param('hide_cursor',checked))
        self.action_about.triggered.connect(self.show_author_information)
        self.bugtton_config_set.clicked.connect(self.set_config)
        self.bugtton_config_set.setToolTip('输入大于1的数，并点击确定，设置等待时间，单位为秒')
        #self.view_config
        self.label_view_statue.setText('未启动')
        #self.label_view_config.setText('等待时间：'+str(self.hider.config_param['WAITING_TIME'])+'秒')
        self.label_view_config.setText(f"当前时间间隔：{self.hider.config_param['WAITING_TIME']:.2f}秒")
        
        self.load_config()
        

        
    def load_config(self):
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            
            self.button_hide_taskbar.setChecked(config['隐藏任务栏'])
            self.button_hide_taskbar.toggled.emit(True)
            self.button_hide_desk_icon.setChecked(config['隐藏任务栏'])
            self.button_hide_desk_icon.toggled.emit(True)
            self.button_hide_cursor.setChecked(config['隐藏任务栏'])
            self.button_hide_cursor.toggled.emit(True)

            self.hider.config_param['WAITING_TIME'] = config['时间间隔']
            self.label_view_config.setText(f"当前时间间隔：{self.hider.config_param['WAITING_TIME']:.2f}秒")
            
            if config['运行/停止程序']:
                self.swith_start_close()
                
            if config['显示界面']:
                self.show()

        
    def swith_start_close(self):
        if self.hider.threading_states['if_talk_1_start'] == False:
            self.label_view_statue.setText('运行中')
            self.hider.threading_1_start()
        elif self.hider.threading_states['if_talk_1_start'] == True:
            self.label_view_statue.setText('未启动')
            self.hider.threading_1_stop()
    
    def set_config(self):
        time_interval_str = self.Edit_time_interval.text()
        try:
            time_interval = float(time_interval_str)
            if time_interval < 1:
                self.label_view_interactive_information.setText(f"错误: '{time_interval_str}' 不能转成大于1的数.")
                return
        except ValueError:
            self.label_view_interactive_information.setText(f"错误: '{time_interval_str}' 不能转成大于1的数.")
            return
        
        self.label_view_interactive_information.setText(f"成功设置当前时间间隔为{time_interval:.2f}秒")
        self.hider.config_param['WAITING_TIME'] = time_interval
        self.label_view_config.setText(f"当前时间间隔：{self.hider.config_param['WAITING_TIME']:.2f}秒")
        

    def set_param(self, param_name,checked):
        self.hider.control_param[param_name] = checked
        #self.hider.test()
        
    def quit(self):
        try:   #懒得写判断语句了，直接try一下
            self.hider.threading_1_stop()
        except:
            pass
        self.tray_icon.hide()
        QApplication.instance().quit()
    
    def show_author_information(self):
        dialog = userWindowAboutDialog(self)
        dialog.exec_()
        
class Hider():     #交互界面与底层实现的中间层，(bug管理器)
    def __init__(self):
        
        #接口
        self.threading_states = {'if_talk_1_start':False}
        self.config_param = {'WAITING_TIME':10}
        self.control_param = {'hide_taskbar':False,'hide_iconbar':False,'hide_cursor':False,'Keep_displaying':False}   
             
        #内部变量
        self.__windows_controler = windowsControler()
        self.__threadings = {'talk_1':None,'talk_1_time_last':time.time(),'talk_1_threading_lock':threading.Lock(),'talk_1_hide_condition':[]}

    def test(self):
        self.__windows_controler.hide_cursor()
        time.sleep(2)
        self.__windows_controler.unhide_cursor()

    def threading_1_start(self):   #开启线程1
        self.threading_states['if_talk_1_start'] = True

        self.__threadings['talk_1'] = threading.Thread(target=self.__talk_1)
        self.__threadings['talk_1'].start()

    def threading_1_stop(self):   #关闭线程1
        self.threading_states['if_talk_1_start'] = False
        self.__threadings['talk_1'].join()   #等待线程结束,防止乱按按钮导致的线程混乱
                    
    def __talk_1_addition_reset_time(self,*args, **kwargs):   #重置线程1的计时器
        with self.__threadings['talk_1_threading_lock']:   #防止多线程同时修改
            self.__threadings['talk_1_time_last'] = time.time()
      
    def __talk_1_addition_enum_windows_callback(self,hwnd, extra):
        # 获取窗口标题
        window_text = win32gui.GetWindowText(hwnd)
        # 判断窗口是否可见
        if win32gui.IsWindowVisible(hwnd):
            # 判断窗口是否最小化
            #if window_text != "" :  # 过滤掉空标题的窗口
            if window_text != "Program Manager" and window_text != "Microsoft Text Input Application" and window_text != "" :  
                if win32gui.IsIconic(hwnd):
                    extra.append({"title": window_text, "hwnd": hwnd, "minimized": True})
                else:
                    extra.append({"title": window_text, "hwnd": hwnd, "minimized": False})
                    
    def __talk_1_addition_check_hide_condition(self):   #检查是否满足隐藏条件
        self.__threadings['talk_1_hide_condition'] = []   #清空上次的隐藏检查
        win32gui.EnumWindows( lambda hwnd, extra: self.__talk_1_addition_enum_windows_callback(hwnd, extra), self.__threadings['talk_1_hide_condition'])

        check_result = all(d["minimized"] for d in self.__threadings['talk_1_hide_condition'])  #当且仅当所有窗口都最小化时，才返回True
        print('检查结果：',check_result,self.__threadings['talk_1_hide_condition'])
        return check_result
      
    def __talk_1(self):     #开启计时器，开启检测，这是个子线程
        print('功能启动')
        
        #启动检测线程，一旦发现鼠标键盘动作，就更新计时器
        self.__talk_1_addition_reset_time()
        self.listener_1 = keyboard.Listener(on_press=self.__talk_1_addition_reset_time,    #简单回调没事，复杂回调得设置逻辑防止多次执行很长的代码
                                            on_release=self.__talk_1_addition_reset_time)   #线程只能start一次所以得重置
        self.listener_2 = mouse.Listener(on_move=self.__talk_1_addition_reset_time, 
                                         on_click=self.__talk_1_addition_reset_time, 
                                         on_scroll=self.__talk_1_addition_reset_time)

        self.listener_1.start()
        self.listener_2.start()
        
        while self.threading_states['if_talk_1_start']:   #self.threading_states['if_talk_1_start'] 被外部改为False时，就会正常退出此线程
            if time.time()-self.__threadings['talk_1_time_last'] >= self.config_param['WAITING_TIME'] \
                and self.__talk_1_addition_check_hide_condition():     
                    
                #控制参数为True，且windows状态为未隐藏
                if self.control_param['hide_cursor'] and not self.__windows_controler.windows_states['if_cursor_hidden']:
                    print('隐藏鼠标')
                    self.__windows_controler.hide_cursor()  #隐藏鼠标
                if self.control_param['hide_taskbar'] and not self.__windows_controler.windows_states['if_taskbar_hidden']:
                    print('隐藏任务栏')
                    self.__windows_controler.hide_taskbar()   #隐藏任务栏
                if self.control_param['hide_iconbar'] and not self.__windows_controler.windows_states['if_iconbar_hidden']:
                    print('隐藏桌面图标')
                    self.__windows_controler.hide_iconbar()   #隐藏桌面图标                  

                self.__windows_controler.updata_windows_states()   #更新windows状态
                print('似乎干了什么又什么都没干',self.control_param['hide_cursor'],not self.__windows_controler.windows_states['if_cursor_hidden'],
                      self.control_param['hide_taskbar'],not self.__windows_controler.windows_states['if_taskbar_hidden'],
                      self.control_param['hide_iconbar'],not self.__windows_controler.windows_states['if_iconbar_hidden'])
            if time.time()-self.__threadings['talk_1_time_last'] < self.config_param['WAITING_TIME']:   #一动鼠标键盘且屏幕是隐藏图标状态就显示图标
                
                if self.__windows_controler.windows_states['if_cursor_hidden']:
                    print('显示鼠标')
                    self.__windows_controler.unhide_cursor()  #显示鼠标
                if self.__windows_controler.windows_states['if_taskbar_hidden']:
                    print('显示任务栏')
                    self.__windows_controler.unhide_taskbar()  #显示任务栏
                if self.__windows_controler.windows_states['if_iconbar_hidden']:
                    print('显示桌面图标')
                    self.__windows_controler.unhide_iconbar()  #显示桌面图标
                print('EEE',self.__windows_controler.windows_states['if_cursor_hidden'],self.__windows_controler.windows_states['if_taskbar_hidden'],self.__windows_controler.windows_states['if_iconbar_hidden'])
                self.__windows_controler.updata_windows_states()   #更新windows状态

            time.sleep(0.2)   #不确定不加会不会浪费电脑资源

        self.listener_1.stop()     #这个线程自带stop函数，不用其它退出设计
        self.listener_2.stop()
        self.threading_states['if_talk_1_start'] = False    #将线程1的状态符设为0
        print('功能关闭')        
        
class windowsControler():    #自定义windows的底层实现, (bug生成器)
    def __init__(self):
        self.windows_states = {'if_taskbar_hidden':False,'if_iconbar_hidden':False,'if_cursor_hidden':False}
        self.__tool = cdll.LoadLibrary("find_deskTopIconBar.dll")
        self.__hwnd_taskbar = win32gui.FindWindow("Shell_TrayWnd",None)    #桌面任务栏的句柄,用spy++找到的,win11是Microsoft:Taskband:SearchBox似乎
        self.__hwnd_iconbar = self.__tool.GetDesktopListViewHWND()
        self.__hwnd_cursorhider = None   #这玩意不能提前创建,否则会出现无法隐藏鼠标

    def updata_windows_states(self):    #更新windows的状态
        self.windows_states['if_taskbar_hidden'] = not win32gui.IsWindowVisible(self.__hwnd_taskbar)   #这里的not是因为win32gui.IsWindowVisible(self.__hwnd_taskbar)返回的是0或1，而self.windows_states['if_taskbar_hidden']需要的是True或False
        self.windows_states['if_iconbar_hidden'] = not win32gui.IsWindowVisible(self.__hwnd_iconbar)   #IsWindowVisible，如果窗口可见返回True，否则返回False
        self.windows_states['if_cursor_hidden'] = bool(win32gui.IsWindow(self.__hwnd_cursorhider))  #注意这个是反的,如果窗口存在，则鼠标被隐藏（因该吧）
                            
    def hide_cursor(self):
        self.__hwnd_cursorhider = win32gui.CreateWindowEx(win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
                            "Static",
                            None,
                            win32con.WS_POPUP | win32con.WS_VISIBLE,
                            0, 0, 3, 3,
                            None,
                            None,
                            None,
                            None)
        # 把鼠标设为隐藏
        win32api.ShowCursor(False)   #-1
        #显示隐藏鼠标的透明窗口
        win32gui.ShowWindow(self.__hwnd_cursorhider, win32con.SW_SHOW)

        # 获取窗口的宽度和高度
        window_rect = win32gui.GetWindowRect(self.__hwnd_cursorhider)
        window_width = window_rect[2] - window_rect[0]
        window_height = window_rect[3] - window_rect[1]

        # 获取鼠标位置
        x, y = win32api.GetCursorPos()

        # 计算窗口的新位置
        new_x = x - window_width // 2
        new_y = y - window_height // 2

        # 将窗口移动到新位置
        win32gui.SetWindowPos(self.__hwnd_cursorhider, win32con.HWND_TOPMOST, new_x, new_y, 0, 0, win32con.SWP_NOSIZE )
        return True

    def unhide_cursor(self):
        # 把鼠标设为显示
        win32api.ShowCursor(True)  #显示鼠标
        win32gui.DestroyWindow(self.__hwnd_cursorhider)  #销毁辅助窗口
        return True

    def hide_taskbar(self):
        return bool(win32gui.ShowWindow(self.__hwnd_taskbar,0))
    
    def unhide_taskbar(self):
        return bool(win32gui.ShowWindow(self.__hwnd_taskbar,1))
    
    def hide_iconbar(self):
        return bool(win32gui.ShowWindow(self.__hwnd_iconbar,0))
       
    def unhide_iconbar(self):
        return bool(win32gui.ShowWindow(self.__hwnd_iconbar,1))
        
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)  #关闭窗口不退出程序
    window = userWindow()
    #window.show()   
    sys.exit(app.exec_())