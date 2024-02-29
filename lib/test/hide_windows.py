from pynput.keyboard import Key, Controller
import time


def hide_windows():
    keyboard = Controller()
    # 按下Win键
    keyboard.press(Key.cmd)
    time.sleep(0.1)
    # 按下D键
    keyboard.press('d')
    time.sleep(0.1)
    # 释放D键
    keyboard.release('d')
    time.sleep(0.1)
    # 释放Win键
    keyboard.release(Key.cmd)

hide_windows()
time.sleep(1)
hide_windows()




