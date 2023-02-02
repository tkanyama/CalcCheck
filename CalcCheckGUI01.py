import sys
import tkinter as tk
import time
import os
import json
import glob
import shutil
from tkinter import filedialog
from CheckTool4 import CheckTool
import logging
import threading
from datetime import datetime

time_sta =  0
flag1 = False
fname = ""

def RunCheck():
    global time_sta
    global flag1,fname

    # los_file  = './main.log'
    # # log 出力レベルの設定
    # logging.basicConfig(filename=los_file,level=logging.WARNING,format="%(asctime)s %(levelname)s %(message)s")

    # logging.debug('debug')
    # logging.info('info')
    # logging.warning('warnig')
    # logging.error('error')
    # logging.critical('critical')

    try:
        CalcNames = [["SS7", "CheckTool_SS7"], ["その他", "CheckTool_SS7"]]
        initFile = "init.json"
        if not os.path.isfile(initFile):
            dir = os.getcwd()
            fld = filedialog.askdirectory(initialdir=dir)
            dir1 = fld + "/処理前フォルダ"
            dir2 = fld + "/処理後フォルダ"
            dir3 = fld + "/ログ"
            dir4 = fld + "/パラメータファイルのテンプレート"
            if not os.path.isdir(dir1):
                os.mkdir(dir1)
            if not os.path.isdir(dir2):
                os.mkdir(dir2)
            if not os.path.isdir(dir3):
                os.mkdir(dir3)
            if not os.path.isdir(dir4):
                os.mkdir(dir4)

            pageData = {"処理前フォルダ": dir1, "処理後フォルダ": dir2, "ログ": dir3, "パラメータファイルのテンプレート": dir4}
            # data_json = json.dumps(pageData, indent=4, ensure_ascii=False)
            with open('init.json', 'w') as fp:
                json.dump(pageData, fp, indent=4, ensure_ascii=False)

            para = {"数値の閾値": 0.95, "開始ページ": 2, "終了ページ": 0}
            with open(dir4+'/para.json', 'w') as fp:
                json.dump(para, fp, indent=4, ensure_ascii=False)

            for Calcname in CalcNames:
                if not os.path.isdir(dir1 + "/" + Calcname[0]):
                    os.mkdir(dir1 + "/" + Calcname[0])
                if not os.path.isdir(dir2 + "/" + Calcname[0]):
                    os.mkdir(dir2 + "/" + Calcname[0])

        else:
            json_open = open(initFile, 'r')
            json_load = json.load(json_open)
            dir1 = json_load['処理前フォルダ']
            dir2 = json_load['処理後フォルダ']
            dir3 = json_load['ログ']
            dir4 = json_load['パラメータファイルのテンプレート']
            if not os.path.isdir(dir1):
                os.mkdir(dir1)
            if not os.path.isdir(dir2):
                os.mkdir(dir2)
            if not os.path.isdir(dir3):
                os.mkdir(dir3)
            if not os.path.isdir(dir4):
                os.mkdir(dir4)

            if not os.path.isfile(dir4 + '/para.json'):
                para = {"数値の閾値": 0.95, "開始ページ": 2, "終了ページ": 0}
                with open(dir4 + '/para.json', 'w') as fp:
                    json.dump(para, fp, indent=4, ensure_ascii=False)

            for Calcname in CalcNames:
                if not os.path.isdir(dir1 + "/" + Calcname[0]):
                    os.mkdir(dir1 + "/" + Calcname[0])
                if not os.path.isdir(dir2 + "/" + Calcname[0]):
                    os.mkdir(dir2 + "/" + Calcname[0])

        # time_sta = time.time()  # 開始時刻の記録

        CT = CheckTool()
        for Calcname in CalcNames:
            inputRCPath = dir1 + "/" + Calcname[0]
            outputRCPath = dir2 + "/" + Calcname[0]
            folderfile = os.listdir(inputRCPath)
            print(folderfile)
            folders = [f for f in folderfile if os.path.isdir(os.path.join(inputRCPath, f))]
            print(folders)

            # stpage = 242
            # edpage = 250
            # CT = CheckTool()
            if len(folders) > 0:
                for folder in folders:
                    # los_file  = './main.log'
                    
                    path1 = inputRCPath + "/" + folder
                    los_file = path1 + "/" + folder +".log"
                    # log 出力レベルの設定
                    logging.basicConfig(filename=los_file,level=logging.WARNING,
                                format="%(asctime)s %(levelname)s %(message)s")
                    logging.debug('debug')
                    logging.info('info')
                    logging.warning('warnig')
                    logging.error('error')
                    logging.critical('critical')

                    path2 = outputRCPath
                    files = glob.glob(os.path.join(path1, "*.pdf"))
                    parafile = path1 + "/para.json"
                    print(files)
                    if len(files) > 0:
                        if os.path.isfile(parafile):
                            json_open = open(parafile, 'r')
                            json_load = json.load(json_open)
                            limit1 = json_load['数値の閾値']
                            stpage = json_load['開始ページ']
                            edpage = json_load['終了ページ']
                        else:
                            limit1 = 0.95
                            stpage = 2
                            edpage = 0   # 全ページ

                        for file in files:
                            
                            if not "検出結果" in file:
                                # path3 = file
                                # fname = sys.path.basename(path3)
                                fname = os.path.basename(file)
                                # if CT.RCCheck(file,limit=0.70,stpage=30,edpage=200):
                                funcName = "CT."+Calcname[1]
                                if eval(funcName)(file, limit=limit1, stpage=stpage, edpage=edpage):
                                    if not os.path.isdir(path2 + "/" + folder):
                                        new_path = shutil.move(path1, path2)
                                    else:
                                        new_path = shutil.move(path1, path2 + "/" + folder + "_new")
        
                    # los_file = "./main.log" 
                    # filename = os.path.splitext(os.path.basename(path1))[0]
                    # los_file2 = path2 + "/" + folder + "/" + filename + '.log' 
                    # new_path = new_path = shutil.move(los_file, los_file2 )
        
        t1 = time.time() - time_sta
        print("time = {} sec".format(t1))
        flag1 = False

    except OSError as e:
        print(e)
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
        
    except:
        print("")
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む

def main():
    global time_sta
    global flag1,fname

    time_sta = time.time()  # 開始時刻の記録

    root = tk.Tk()
    Width = 800
    Height = 600
    root.title(u"Calculation Cheet Check")
    root.geometry("800x600")
    root.geometry("{}x{}".format(Width,Height))

    Static1 = tk.Label(text=u'\n\n構造計算書の数値検索プログラム', font=("MSゴシック", "28", "bold"))
    Static1.pack()

    Static2 = tk.Label(text=u'\n一般財団法人日本建築総合試験所', font=("MSゴシック", "28", "bold"))
    Static2.pack()
    
    # Static1.place(x=Width/2, y=20)


    # notice_label = tk.Label(frame, text="*This app is made by Tkinter*", fg="blue", width="100",anchor=tk.E)


    root.update_idletasks()
    ww=root.winfo_screenwidth()
    lw=root.winfo_width()
    wh=root.winfo_screenheight()
    lh=root.winfo_height()
    canvas=tk.Canvas(root,width=lw,heigh=lh)
    canvas.pack()#ここを書かないとcanvasがうまく入らない．

    root.geometry(str(lw)+"x"+str(lh)+"+"+str(int(ww/2-lw/2))+"+"+str(int(wh/2-lh/2)) )

    data = 100
    thread1 = threading.Thread(target=RunCheck)
    thread1.start()
    flag1 = True
    while flag1:
        root.update()
        # now_h=datetime.now().hour
        # now_s=datetime.now().second
        # now_m=datetime.now().minute
        # now_time=str(now_h)+":"+str(now_m)+":"+str(now_s)
        now_time =fname + "\n\n経過時間：{:7.0f}秒".format(time.time() - time_sta)
        canvas.create_text(lw/2,200,text=now_time,font=("",25,""),tag='Y') #タグを入れることで更新できるようにする．
        canvas.update()
        canvas.delete('Y')
        time.sleep(1.0)

    
    # thread1.join()
    # root.mainloop()


if __name__ == '__main__':
    main()

    # root = tk.Tk()
    # Width = 800
    # Height = 600
    # root.title(u"Calculation Cheet Check")
    # root.geometry("800x600")
    # root.geometry("{}x{}".format(Width,Height))

    # Static1 = tk.Label(text=u'\n構造計算書の数値検索プログラム', font=("MSゴシック", "28", "bold"))
    # Static1.pack()
    # # Static1.place(x=Width/2, y=20)


    # # notice_label = tk.Label(frame, text="*This app is made by Tkinter*", fg="blue", width="100",anchor=tk.E)


    # root.update_idletasks()
    # ww=root.winfo_screenwidth()
    # lw=root.winfo_width()
    # wh=root.winfo_screenheight()
    # lh=root.winfo_height()
    # root.geometry(str(lw)+"x"+str(lh)+"+"+str(int(ww/2-lw/2))+"+"+str(int(wh/2-lh/2)) )

    # data = 100
    # thread1 = threading.Thread(target=RunCheck)
    # thread1.start()

    # root.mainloop()
