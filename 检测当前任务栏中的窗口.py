import win32gui

window_list = []
def enum_windows_callback(hwnd, extra):
    # 获取窗口标题
    window_text = win32gui.GetWindowText(hwnd)
    # 判断窗口是否可见
    if win32gui.IsWindowVisible(hwnd):
        # 判断窗口是否最小化
        #if window_text != "" :  # 过滤掉空标题的窗口
        if window_text != "" :  
            if win32gui.IsIconic(hwnd):
                extra.append({"title": window_text, "hwnd": hwnd, "minimized": True})
            else:
                extra.append({"title": window_text, "hwnd": hwnd, "minimized": False})

# 枚举所有顶层窗口
win32gui.EnumWindows(enum_windows_callback, window_list)

# 输出窗口列表
for window in window_list:
    print(f"窗口标题：'{window['title']}'，状态：{'已最小化' if window['minimized'] else '未最小化'}")
    
#程序结束后不立刻退出控制台
input("按回车键退出...")
    