import sys
import tkinter as tk


root = tk.Tk()
Width = 800
Height = 600
root.title(u"Calculation Cheet Check")
root.geometry("800x600")
root.geometry("{}x{}".format(Width,Height))

Static1 = tk.Label(text=u'\n構造計算書の数値検索プログラム', font=("MSゴシック", "28", "bold"))
Static1.pack()
# Static1.place(x=Width/2, y=20)


# notice_label = tk.Label(frame, text="*This app is made by Tkinter*", fg="blue", width="100",anchor=tk.E)


root.update_idletasks()
ww=root.winfo_screenwidth()
lw=root.winfo_width()
wh=root.winfo_screenheight()
lh=root.winfo_height()
root.geometry(str(lw)+"x"+str(lh)+"+"+str(int(ww/2-lw/2))+"+"+str(int(wh/2-lh/2)) )

root.mainloop()
