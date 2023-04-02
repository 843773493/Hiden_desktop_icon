from ctypes import windll
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QDialog, QMessageBox, QPushButton,
                             QLabel, QCheckBox, QComboBox, QLineEdit, QSpinBox,
                             QMenu, QAction, QGridLayout, QHBoxLayout, QVBoxLayout,
                             QTextEdit,QGroupBox, QStyle, QSystemTrayIcon)

 # coding=utf-8
import random
import win32con,win32api,win32gui  #淘汰的工具
import time
#import pyautogui as pag    #也是个控制鼠标键盘的
import pydirectinput
from PyQt5 import QtGui, QtWidgets,QtCore
import sys
import threading

import time
from pynput import keyboard,mouse
from ctypes import *

WAITING_TIME = 10

class SystemTrayDemo(QDialog):
    def __init__(self):
        super(SystemTrayDemo, self).__init__()
        
        # 设置窗口标题
        self.setWindowTitle('使用说明:ctrl+8隐藏时不熄屏')
        
        #设置窗口尺寸
        self.resize(400, 300)
        
        self.sysIcon = QIcon('1.ico')
        self.setWindowIcon(self.sysIcon)
        


        self.ES_CONTINUOUS = 0x80000000      #重置屏幕熄屏计时器的控制常数
        self.ES_SYSTEM_REQUIRED = 0x00000001
        self.ES_DISPLAY_REQUIRED= 0x00000002
        self.key_last_display = None
        self.Keep_displaying = False


        self.quit_sign = 0
        self.initUi()

        self.iconopaque()   #启动后就启动这个
        self.taskbar = win32gui.FindWindow("Shell_TrayWnd",None)    #桌面任务栏的句柄,用spy++找到的
        self.iconbar = self.find_windows_iconwindow()    #图标的句柄
        self.keyboard_ctrl = keyboard.Controller()
        

    def initUi(self):
        

        #控制透明度的线程
        self.State_of_the_screen = 0    #正常为0
        self.time_last = 0        #记录时间的
        self.mouse_position = (0,0)  #记录鼠标位置
        self.p1 = None  #线程初始化
        self.p1_state = 0   #线程状态标志
        self.on_cheking = 1
        self.lock = threading.Lock()    #线程锁
        

        #面板
        self.createMessageGroupBox()
        self.createTrayIcon()
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.grpMessageBox)
        self.setLayout(mainLayout)
        
        #让托盘图标显示在系统托盘上
        self.trayIcon.show()





    #创建托盘图标
    def createTrayIcon(self):
        aRestore = QAction('恢复(&R)', self, triggered = self.showNormal)
        aQuit = QAction('退出(&Q)', self, triggered = lambda:self.quit('quit'))
        
        menu = QMenu(self)
        menu.addAction(aRestore)
        menu.addAction(aQuit)
        
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.sysIcon)
        self.trayIcon.setContextMenu(menu)

    
    #控制面板
    def createMessageGroupBox(self):
        
        self.grpMessageBox = QGroupBox('控制面板')
        #==== 开始淡化按钮 ====#
        Button_1 = QPushButton('执行隐藏')
        Button_1.setDefault(True)
        Button_1.clicked.connect(self.iconopaque)    #按钮下执行的函数都得用if 防止有人乱点出现bug
        
        #==== 关闭检测按钮 ====#
        Button_2 = QPushButton('关闭隐藏')
        Button_2.setDefault(True)
        Button_2.clicked.connect(self.quit)

        #==== 状态显示 ====#
        label_1=QLabel(self)
        #label_1.setFrameShape(QtWidgets.QFrame.Box)
        label_1.setText('   当前状态:')
        self.label_2=QLineEdit('未工作，熄屏{}'.format('开启' if self.Keep_displaying else '关闭'))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        #self.label_2.setFrameShape(QtWidgets.QFrame.Box)
        #self.label_2.setText('未工作')

        #==== 将上述部件加入到一个网格布局中
        msgLayout = QGridLayout()

        msgLayout.addWidget(Button_1, 0, 0) 
        msgLayout.addWidget(Button_2, 1, 0) 
        msgLayout.addWidget(label_1, 3, 0) 
        msgLayout.addWidget(self.label_2, 3, 1,1,3) #占1行3列，但第三列恰好被stretch拉长所以会占满

        msgLayout.setColumnStretch(3, 1)   
        #msgLayout.setRowStretch(4, 1)
        self.grpMessageBox.setLayout(msgLayout)       


      

    #关闭事件处理, 不关闭，只是隐藏，真正的关闭操作在托盘图标菜单里
    def closeEvent(self, event):
        if self.trayIcon.isVisible():
            QMessageBox.information(self, '系统托盘', 
                                    '程序将继续在系统托盘中运行，要终止本程序，\n'
                                    '请在系统托盘入口的上下文菜单中选择"退出"')
            self.hide()
            event.ignore()
    
    def quit(self,quit_process = ''):        #停止跟退出都会激活这个函数，所以要区分一下
        if self.p1 != None:            #p1激活时，这么退出p1，否则不用管
            self.label_2.setText('退出中')
            self.label_2.repaint()   #button激活的函数中的label更新需要这个

            self.lock.acquire()  #发出退出信号时锁定线程
            self.p1_state = 0  
            self.lock.release()

            self.p1.join()   #等待线程退出干净
            self.p1 = None    #用于管理，当信号重置

            self.label_2.setText('未运行，熄屏{}'.format('开启' if self.Keep_displaying else '关闭'))

        if quit_process == 'quit':     #退出时会自动给这个参数赋值 'quit'
            QApplication.instance().quit()
        
    def Get_all_windows(self):
        hWnd_list = []
        win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), hWnd_list)
        # print(hWnd_list)
        return hWnd_list

    def Get_son_windows(self,parent):
        hWnd_child_list = []
        win32gui.EnumChildWindows(parent, lambda hWnd, param: param.append(hWnd), hWnd_child_list)
        # print(hWnd_child_list)
        return hWnd_child_list

    def Get_title(self,hwnd):
        title = win32gui.GetWindowText(hwnd)
        # print('窗口标题:%s' % (title))
        return title

    def Get_clasname(self,hwnd):
        clasname = win32gui.GetClassName(hwnd)
        # print('窗口类名:%s' % (clasname))
        return clasname

    def find_windows_iconwindow(self):
        hWnd_list = self.Get_all_windows()
        for hwnd in hWnd_list:
            if self.Get_clasname(hwnd) == 'WorkerW':
                hWnd_child_list = self.Get_son_windows(hwnd)
                for child_hwnd in hWnd_child_list:
                    if self.Get_clasname(child_hwnd) == 'SHELLDLL_DefView':
                        hWnd_grandchild_list = self.Get_son_windows(child_hwnd)
                        for grandchild_hwnd in hWnd_grandchild_list:
                            if self.Get_clasname(grandchild_hwnd) == 'SysListView32':
                                return grandchild_hwnd

    def iconopaque(self):   #开始执行透明

        if self.p1 == None:    #没有线程就建，防止多次点击开启多个线程
            self.p1 = threading.Thread(target=self.talk_1)
            
        if not self.p1.is_alive():   #判断是否已经开启
            self.time_last = time.time()    #记录上次没动鼠标键盘前的时间
            self.p1.start()
            self.label_2.setText('运行中，熄屏{}'.format('开启' if self.Keep_displaying else '关闭'))
            

    def On_move(self,x, y):           #随时监测，需要记录上一次的位置来判断是否动了鼠标
        if self.mouse_position[0]-x == 0 and self.mouse_position[1]-y == 0:  #没变化就不管，计时器会继续走
            pass
        else:           #有变化就更新新位置，重置计时器
            self.mouse_position = (x,y)
            self.Reset_the_timer()

    def On_click(self,x, y, button, pressed):    #当触发这俩函数时都表示动了鼠标
        self.Reset_the_timer()

    def On_scroll(self,x, y, dx, dy):
        self.Reset_the_timer()

    def On_press(self,key):  #当触发这俩函数时都表示动了键盘
        '按下按键时执行。'
        
        if self.key_last_display == keyboard.Key.ctrl_l and key == keyboard.KeyCode.from_char('8'):
            self.Keep_displaying = ~self.Keep_displaying     #会在 0和-1之间变换
        self.key_last_display = key
        print(key,self.Keep_displaying)

        
        if self.on_cheking == 1:    #由于是按键盘快捷键实现的功能，所以在实现功能时关闭检测
            self.Reset_the_timer()

    def On_release(self,key):   
        if self.on_cheking == 1:
            self.Reset_the_timer()

    def Reset_the_timer(self):
        self.time_last = time.time()   #初始化计时器

    def screenON(self):   #在隐藏图标状态下，防止windows熄屏
        HWND_BROADCAST = 0xffff
        WM_SYSCOMMAND = 0x0112
        SC_MONITORPOWER = 0xF170
        MonitorPowerOff = 1     #1关，2开
        SW_SHOW = 5
        windll.user32.PostMessageW(HWND_BROADCAST, WM_SYSCOMMAND,
                                SC_MONITORPOWER, MonitorPowerOff)

        shell32 = windll.LoadLibrary("shell32.dll")
        shell32.ShellExecuteW(None, 'open', 'rundll32.exe',
                            'USER32', '', SW_SHOW)


    def talk_1(self):     #开启计时器，开启检测，这是个子线程
        print('p1 start')
        self.listener_1 = keyboard.Listener( on_press=self.On_press, on_release=self.On_release)   #线程只能start一次所以得重置
        self.listener_2 = mouse.Listener( on_move=self.On_move, on_click=self.On_click, on_scroll=self.On_scroll)

        self.listener_1.start()
        self.listener_2.start()
        
        self.p1_state = 1    #将线程1的状态符设为1

        self.lock.acquire()    #可以把 lock和通信变量 打包
        while self.p1_state:   #self.p1_state 被外部改为0时，就会正常退出此线程
            self.lock.release()    #为了在检查p1_state时没有别线程的改变它，似乎没啥必要，可能出现的多线程同时操作同一变量，影响不大，大不了再循环一次便是
            if time.time()-self.time_last >= WAITING_TIME \
                and self.State_of_the_screen == 0 \
                and win32gui.GetWindowText (win32gui.GetForegroundWindow()) == '':   #超过10秒没动鼠标键盘且屏幕是正常状态且前台窗口为壁纸即标题名为''，就执行隐藏图标
                
                self.on_cheking = 0

                self.hide_cursor()  #隐藏鼠标
                win32gui.ShowWindow(self.taskbar,0)      #隐藏任务栏
                win32gui.ShowWindow(self.iconbar,0)      
                self.on_cheking = 1
                self.State_of_the_screen = 1
                self.screenON()

                if self.Keep_displaying:     #重置windows的熄屏计时器
                    windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS | self.ES_DISPLAY_REQUIRED)

            if time.time()-self.time_last < WAITING_TIME and self.State_of_the_screen == 1:   #一动鼠标键盘且屏幕是隐藏图标状态就显示图标
                self.on_cheking = 0

                self.unhide_cursor()  #显示鼠标
                win32gui.ShowWindow(self.taskbar,1)      #显示任务栏
                win32gui.ShowWindow(self.iconbar,1)      
                self.on_cheking = 1
                self.State_of_the_screen = 0

            time.sleep(0.2)   #不确定不加会不会浪费电脑资源
            self.lock.acquire()
        self.lock.release()   #必须要退出，不然以后不能用锁了

        
        self.listener_1.stop()     #这个线程自带stop函数，不用其它退出设计
        self.listener_2.stop()
        print('p1 stop')
                
    def hide_cursor(self):
        # 创建一个透明窗口
        self.hwnd = win32gui.CreateWindowEx(win32con.WS_EX_TOPMOST,
                                    "Static",
                                    None,
                                    win32con.WS_POPUP | win32con.WS_VISIBLE,
                                    0, 0, 1, 1,
                                    None,
                                    None,
                                    None,
                                    None)
        # 把鼠标设为隐藏
        win32api.ShowCursor(False)
        # 获取鼠标位置
        x, y = win32api.GetCursorPos()
        # 把窗口移到鼠标那儿
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, x, y, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    def unhide_cursor(self):
        # 把鼠标设为显示
        win32api.ShowCursor(True)
        win32gui.DestroyWindow(self.hwnd)

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    #如果系统不支持最小化到托盘
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, '系统托盘', '本系统不支持托盘功能')
        sys.exit(1)
        
    QApplication.setQuitOnLastWindowClosed(False)
    
    window = SystemTrayDemo()
    #window.show()  #启动后不主界面显示

    sys.exit(app.exec())


