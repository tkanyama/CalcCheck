
#==========================================================================================
#   構造計算書の数値検査プログラムのメインルーチン（ver.0.01）
#
#           一般財団法人日本建築総合試験所
#
#               coded by T.Kanyama  2023/02
#
#==========================================================================================
"""
このプログラムは、構造判定センターに提出される構造計算書（PDF）の検定比（許容応力度に対する部材応力度の比）を精査し、
設定した閾値（デフォルトは0.95）を超える部材を検出するプログラムである。

"""


import sys
import tkinter as tk
import time
import os
import json
import glob
import shutil
from tkinter import filedialog
from CheckTool import CheckTool
import logging
import threading
from datetime import datetime

# グリーバル変数の定義
time_sta =  0       # 経過時間を表示するための開始時刻
flag1 = False       # 表示ウインドウを制御するための変数（Trueの場合は表示、Falseは表示終了）
fname = ""          # 現在処理中のファイル名
folderName = ""     # 現在処理中のファイルのあるフォルダー名
dir1 = ""           # 処理前フォルダー
dir2 = ""           # 処理後フォルダー
dir3 = ""           # ログのフォルダー
dir4 = ""           # パラメータファイルのテンプレートのフォルダー
paraFileName = "para.json" # パラメータファイルの名称

#============================================================================
#  作業フォルダーの設定データ（init.json）読込
#  
#  作業フォルダーの設定データ（init.json）がない場合は、ダイアログで場所を選択する。
#   フォルダーを自動的に作成する。
#   その際、パラメータファイル（para.json）のテンプレートも作成
#============================================================================

def CreateFolfer():
    global dir1, dir2, dir3, dir4, folderName, paraFileName
    try:
        # CalcNames = [["SS7", "CheckTool"], ["その他", "CheckTool"]]
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
            with open('init.json', 'w', encoding="utf-8") as fp:
                json.dump(pageData, fp, indent=4, ensure_ascii=False)

            para = {"数値の閾値": 0.95, "開始ページ": 2, "終了ページ": 0}
            with open(dir4+'/'+paraFileName, 'w', encoding="utf-8") as fp:
                json.dump(para, fp, indent=4, ensure_ascii=False)

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

            if not os.path.isfile(dir4+'/'+paraFileName):
                para = {"数値の閾値": 0.95, "開始ページ": 2, "終了ページ": 0}
                with open(dir4+'/'+paraFileName, 'w') as fp:
                    json.dump(para, fp, indent=4, ensure_ascii=False)

    except OSError as e:
        print(e)
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
        
    except:
        print("")
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
    #*********************************************************************************



    #============================================================================
    #  実際に処理を行う関数（スレッドで実行）
    #============================================================================

def RunCheck():
    global time_sta
    global flag1, fname, dir1, dir2, dir3, dir4, folderName, paraFileName
    
    try:

        CT = CheckTool()    # チェックツールのインスタンスを作成
        inputRCPath = dir1      # 処理前フォルダー
        outputRCPath = dir2     # 処理後フォルダー
        folderfile = os.listdir(inputRCPath)
        print(folderfile)

        # 処理前フォルダーに保存されたデータフォルダー名をすべて検出
        folders = [f for f in folderfile if os.path.isdir(os.path.join(inputRCPath, f))]
        print(folders)

        # stpage = 242
        # edpage = 250
        if len(folders) > 0:
            for folder in folders:      # フォルダー毎に処理を実行
                if not "検出結果" in folder:  # フォルダー名に"検出結果"が含まれる場合は結果フォルダなので無視する。
                    folderName = folder     # 表示ウィンドウに表示させるフォルダー名
                    path1 = inputRCPath + "/" + folder
                    path2 = outputRCPath

                    # データフォルダー内にあるPDFファイルをすべて検出
                    files = glob.glob(os.path.join(path1, "*.pdf"))
                    print(files)

                    if len(files) > 0:
                        # パラメータファイル名の設定
                        parafile = path1 + '/' + paraFileName

                        if os.path.isfile(parafile):    # パラメータファイルがある場合はパラメータを読み込む
                            json_open = open(parafile, 'r')
                            json_load = json.load(json_open)
                            limit1 = json_load['数値の閾値']
                            stpage = json_load['開始ページ']
                            edpage = json_load['終了ページ']
                        else:                           # パラメータファイルがない場合はデフォルト値を設定
                            limit1 = 0.95
                            stpage = 2
                            edpage = 0   # 全ページ

                        for file in files:
                            
                            if not "検出結果" in file:  # ファイル名に"検出結果"が含まれる場合は結果ファイルなので無視する。

                                fname = os.path.basename(file)  # 表示ウインドウに表示するファイル名を設定

                                if CT.CheckTool(file, limit=limit1, stpage=stpage, edpage=edpage):
                                    outfolder = folder + '[検出結果(閾値={:.2f}'.format(limit1)+')]'
                                    # 検査がエラーなく終了した場合の処理
                                    # 処理後フォルダーに同じ名称のデータフォルダーがある場合は、上書きせずに、
                                    # データフォルダー名に'(n)'を追加して移動

                                    # フォルダー名の最後の3文字が (n) の場合は何番目であるか
                                    t1 = outfolder[len(outfolder)-3:]
                                    if t1[0] == "(" and t1[len(t1)-1] == ")" :
                                        num = int(t1.replace("(","").replace(")",""))
                                        numflag = True
                                    else:
                                        num = 0
                                        numflag = False
                                    
                                    if not os.path.isdir(path2 + "/" + outfolder):
                                        new_path = shutil.move(path1, path2 + "/" + outfolder)
                                    else:
                                        while True:
                                            # 同じ名前にならないよう繰り返す
                                            num += 1
                                            if numflag :
                                                newFolder = path2 + "/" + outfolder[:len(outfolder)-3] + "({})".format(num)
                                            else:
                                                newFolder = path2 + "/" + outfolder + "({})".format(num)
                                            if not os.path.isdir(newFolder):
                                                new_path = shutil.move(path1, newFolder)
                                                break
                                    
                                        
    
        t1 = time.time() - time_sta
        print("time = {} sec".format(t1))
        flag1 = False

    except OSError as e:
        print(e)
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
        
    except:
        print("")
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
    #*********************************************************************************



    #============================================================================
    #  プログラムのメインルーチン（外部から読み出す関数名）
    #============================================================================

def main():
    global time_sta
    global flag1, fname, dir1, dir2, dir3, dir4, folderName

    CreateFolfer()

    los_file = dir3 + "/" + "CheckTool.log"
    # log 出力レベルの設定
    logging.basicConfig(filename=los_file,level=logging.WARNING,
                format="%(asctime)s %(levelname)s %(message)s")
    logging.debug('debug')
    logging.info('info')
    logging.warning('warnig')
    logging.error('error')
    logging.critical('critical')

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

    root.update_idletasks()
    ww=root.winfo_screenwidth()
    lw=root.winfo_width()
    wh=root.winfo_screenheight()
    lh=root.winfo_height()
    canvas=tk.Canvas(root,width=lw,heigh=lh)
    canvas.pack()#ここを書かないとcanvasがうまく入らない．

    root.geometry(str(lw)+"x"+str(lh)+"+"+str(int(ww/2-lw/2))+"+"+str(int(wh/2-lh/2)) )

    thread1 = threading.Thread(target=RunCheck)
    thread1.start()
    flag1 = True
    while flag1:
        root.update()
        # now_h=datetime.now().hour
        # now_s=datetime.now().second
        # now_m=datetime.now().minute
        # now_time=str(now_h)+":"+str(now_m)+":"+str(now_s)
        now_time = folderName + "\n" + fname + "\n\n経過時間：{:7.0f}秒".format(time.time() - time_sta)
        canvas.create_text(lw/2,200,text=now_time,font=("",25,""),tag='Y') #タグを入れることで更新できるようにする．
        canvas.update()
        canvas.delete('Y')
        time.sleep(1.0)

    #*********************************************************************************



    #============================================================================
    #  プログラムのメインルーチン（外部から読み出す関数名）
    #============================================================================

if __name__ == '__main__':
    main()