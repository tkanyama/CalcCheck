import threading
import time
from tkinter import ttk
import tkinter


#5秒タイマー
def timer():
    p.start(5)          #プログレスバー開始
    for i in range(6):
        time.sleep(1)   #1秒待機
        b["text"] = i   #秒数表示
    p.stop()            #プログレスバー停止


#ボタンクリック時に実行する関数
def button_clicked():
    t = threading.Thread(target=timer)  #スレッド立ち上げ
    t.start()   #スレッド開始


root = tkinter.Tk()

#プログレスバー
p = ttk.Progressbar(
    root,
    mode="indeterminate",   #非確定的
    )
p.pack()

#ボタン
b = tkinter.Button(
    root,
    width=15,
    text="start",
    command=button_clicked,
    )
b.pack()


root.mainloop()