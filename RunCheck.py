
import time
import os,sys
import json
import glob
import shutil
from tkinter import filedialog
from CheckTool4 import CheckTool
import logging

if __name__ == '__main__':
    los_file  = './main.log'
    # log 出力レベルの設定
    logging.basicConfig(filename=los_file,level=logging.WARNING,format="%(asctime)s %(levelname)s %(message)s")

    logging.debug('debug')
    logging.info('info')
    logging.warning('warnig')
    logging.error('error')
    logging.critical('critical')

    try:
        CalcNames = [["SS7", "CheckTool_SS7"], ["その他", "CheckTool_SS7"]]
        initFile = "init.json"
        if not os.path.isfile(initFile):
            dir = os.getcwd()
            fld = filedialog.askdirectory(initialdir=dir)
            dir1 = fld + "/処理前フォルダ"
            dir2 = fld + "/処理後フォルダ"
            if not os.path.isdir(dir1):
                os.mkdir(dir1)
            if not os.path.isdir(dir2):
                os.mkdir(dir2)

            pageData = {"処理前フォルダ": dir1, "処理後フォルダ": dir2}
            # data_json = json.dumps(pageData, indent=4, ensure_ascii=False)
            with open('init.json', 'w') as fp:
                json.dump(pageData, fp, indent=4, ensure_ascii=False)

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
            if not os.path.isdir(dir1):
                os.mkdir(dir1)
            if not os.path.isdir(dir2):
                os.mkdir(dir2)

            for Calcname in CalcNames:
                if not os.path.isdir(dir1 + "/" + Calcname[0]):
                    os.mkdir(dir1 + "/" + Calcname[0])
                if not os.path.isdir(dir2 + "/" + Calcname[0]):
                    os.mkdir(dir2 + "/" + Calcname[0])

        time_sta = time.time()  # 開始時刻の記録

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
                    path1 = inputRCPath + "/" + folder
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
                                
                                # if CT.RCCheck(file,limit=0.70,stpage=30,edpage=200):
                                funcName = "CT."+Calcname[1]
                                if eval(funcName)(file, limit=limit1, stpage=stpage, edpage=edpage):
                                    if not os.path.isdir(path2 + "/" + folder):
                                        new_path = shutil.move(path1, path2)
                                    else:
                                        new_path = shutil.move(path1, path2 + "/" + folder + "_new")
        
        los_file = "./main.log" 
        filename = os.path.splitext(os.path.basename(path1))[0]
        los_file2 = path2 + "/" + folder + "/" + filename + '.log' 
        new_path = new_path = shutil.move(los_file, los_file2 )
        
        t1 = time.time() - time_sta
        print("time = {} sec".format(t1))

    except OSError as e:
        print(e)
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
        
    except:
        print("")
        logging.exception(sys.exc_info())#エラーをlog.txtに書き込む


        
