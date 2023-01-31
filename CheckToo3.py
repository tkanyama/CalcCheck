
# pip install pdfminer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
# from pdfminer.layout import LAParams, LTTextContainer
from pdfminer.layout import LAParams, LTTextContainer, LTContainer, LTTextBox, LTTextLine, LTChar

# pip install pdfrw
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl

# pip install reportlab
from reportlab.pdfgen import canvas
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# pip install PyPDF2
from PyPDF2 import PdfReader as PR2 # 名前が上とかぶるので別名を使用
import os,time
import sys
import json

from tkinter import filedialog
import numpy as np
import math

#============================================================================
#  浮動小数点数値を表しているかどうかを判定する関数
#============================================================================
def isfloat(s):  
    try:
        float(s)  # 文字列を実際にfloat関数で変換してみる
    except ValueError:
        return False
    else:
        return True

#============================================================================
#  整数を表しているかどうかを判定する関数
#============================================================================
def isint(s):  
    try:
        int(s)  # 文字列を実際にint関数で変換してみる
    except ValueError:
        return False
    else:
        return True

class CheckTool():
    #==================================================================================
    #   オブジェクトのインスタンス化および初期化
    #==================================================================================
    
    def __init__(self):
        # 源真ゴシック等幅フォント
        # GEN_SHIN_GOTHIC_MEDIUM_TTF = "/Library/Fonts/GenShinGothic-Monospace-Medium.ttf"
        GEN_SHIN_GOTHIC_MEDIUM_TTF = "./Fonts/GenShinGothic-Monospace-Medium.ttf"
        self.fontname1 = 'GenShinGothic'
        # IPAexゴシックフォント
        # IPAEXG_TTF = "/Library/Fonts/ipaexg.ttf"
        IPAEXG_TTF = "./Fonts/ipaexg.ttf"
        self.fontname2 = 'ipaexg'
        
        # フォント登録
        pdfmetrics.registerFont(TTFont(self.fontname1, GEN_SHIN_GOTHIC_MEDIUM_TTF))
        pdfmetrics.registerFont(TTFont(self.fontname2, IPAEXG_TTF))
        # print(pdfmetrics.getRegisteredFontNames())

        # initFile = "init.json"
        # if not os.path.isfile(initFile):
        #     dir = os.getcwd()
        #     fld = filedialog.askdirectory(initialdir = dir) 
        #     self.dir1 = fld + "/処理前フォルダ"
        #     self.dir2 = fld + "/処理後フォルダ"

        #     pageData = {"処理前フォルダ":self.dir1,"処理前フォルダ":self.dir2}
        #     # data_json = json.dumps(pageData, indent=4, ensure_ascii=False)
        #     with open('init.json', 'w') as fp:
        #         json.dump(pageData, fp, indent=4, ensure_ascii=False)
        # else:
        #     json_open = open(initFile, 'r')
        #     json_load = json.load(json_open)
        #     self.dir1 = json_load['処理前フォルダ']
        #     self.dir2 = json_load['処理前フォルダ']

        # self.pdf_file = FileName
        # self.pdf_out_file = os.path.splitext(self.pdfFileName)[0] + '[検出結果].pdf'


    def MakeChar(self, page, interpreter, device):

        interpreter.process_page(page)
        # １文字ずつのレイアウトデータを取得
        layout = device.get_result()

        CharData = []
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                m1 = lt.matrix
                if m1[1] == 0.0 :  # 回転していない文字のみを抽出
                    CharData.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])

        # その際、CharData2をY座標の高さ順に並び替えるためのリスト「CY」を作成
        CharData2=[]
        CY = []
        for cdata in CharData:
            char2 = cdata[0]
            x0 = cdata[1]
            x1 = cdata[2]
            y0 = cdata[3]
            y1 = cdata[4]
            
            CharData2.append(cdata)
            CY.append(int(y0))
        
        # リスト「CY」から降順の並び替えインデックッスを取得
        y=np.argsort(np.array(CY))[::-1]

        if len(CharData2) > 0:  # リストが空でない場合に処理を行う
            CharData3 = []
            # インデックスを用いて並べ替えた「CharData3」を作成
            for i in range(len(y)):
                CharData3.append(CharData2[y[i]])

            # 同じ高さのY座標毎にデータをまとめる２次元のリストを作成
            CharData4 = []
            i = 0
            for f in CharData3:
                if i==0 :   # 最初の文字のY座標を基準値に採用し、仮のリストを初期化
                    Fline = []
                    Fline.append(f)
                    gy = int(f[3])
                else:
                    if int(f[3])== gy:   # 同じY座標の場合は、リストに文字を追加
                        Fline.append(f)
                    else:           # Y座標が異なる場合は、リストを「CharData4」を保存し、仮のリストを初期化
                        if len(Fline) >= 4:
                            CharData4.append(Fline)
                        gy = int(f[3])
                        Fline = []
                        Fline.append(f)
                i += 1
            # 仮のリストが残っている場合は、リストを「CharData4」を保存
            if len(Fline) >= 4:
                CharData4.append(Fline)

            # 次にX座標の順番にデータを並び替える（昇順）
            t1 = []
            CharData5 = []
            for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
                CX = []         # 各データのX座標のデータリストを作成
                for F2 in F1:
                    CX.append(F2[1])
                
                # リスト「CX」から降順の並び替えインデックッスを取得
                x=np.argsort(np.array(CX))
                
                # インデックスを用いて並べ替えた「F3」を作成
                F3 = []
                t2 = ""
                for i in range(len(x)):
                    F3.append(F1[x[i]])
                    t3 = F1[x[i]][0]
                    t2 += t3
                # t1 += t2 + "\n"
                t1.append([t2])
                # print(t2,len(F3))
                CharData5.append(F3)

        CharData2 = []
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] > 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] < 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
        # CharData2 = CharDataPlus
        # outtext2 = []
        # CharOutPut2 = []
        fline = []
        Sflag = False
        tt2 = ""
        # for F1 in CharData:
        #     if not Sflag:
        #         if F1[0] != " ":
        #             fline.append(F1)
        #             tt2 += F1[0]
        #             Sflag = True
        #         # else:
        #         #     Sflag = True
        #         #     continue
        #     else:
        #         if F1[0] == " ":
        #             CharOutPut2.append(fline)
        #             outtext2.append([tt2])
        #             fline = []
        #             tt2 = ""
        #             Sflag = False
        #         else:
        #             fline.append(F1)
        #             tt2 += F1[0]

        # if len(fline)>0:
        #     CharOutPut2.append(fline)
        #     outtext2.append([tt2])

        fline = []
        Sflag = False
        tt2 = ""
        for F1 in CharData2:
            if not Sflag:
                if F1[0] != " ":
                    fline.append(F1)
                    tt2 += F1[0]
                    Sflag = True
                # else:
                #     Sflag = True
                #     continue
            else:
                if F1[0] == " ":
                    CharData5.append(fline)
                    t1.append([tt2])
                    fline = []
                    tt2 = ""
                    Sflag = False
                else:
                    fline.append(F1)
                    tt2 += F1[0]

        if len(fline)>0:
            CharData5.append(fline)
            t1.append([tt2])

        

        
        return t1 , CharData5



    #============================================================================
    #  プログラムの開始
    #============================================================================

    # time_sta = time.time() # 開始時刻の記録


    # # 源真ゴシック等幅フォント
    # GEN_SHIN_GOTHIC_MEDIUM_TTF = "/Library/Fonts/GenShinGothic-Monospace-Medium.ttf"
    # # IPAexゴシックフォント
    # IPAEXG_TTF = "/Library/Fonts/ipaexg.ttf"

    # # フォント登録
    # pdfmetrics.registerFont(TTFont('GenShinGothic', GEN_SHIN_GOTHIC_MEDIUM_TTF))
    # pdfmetrics.registerFont(TTFont('ipaexg', IPAEXG_TTF))
    # print(pdfmetrics.getRegisteredFontNames())

    # # 対象PDFファイル設定
    # pdf_file = './サンプル計算書(1).pdf'
    # # 検出結果ファイル設定
    # # pdf_out_file = 'サンプル計算書(1)[検索結果].pdf'
    # # pdf_file = FileName
    # pdf_out_file = os.path.splitext(pdf_file)[0] + '[検出結果].pdf'

    def CheckTool(self,filename, limit=0.95 ,stpage=0, edpage=0):

        if filename =="" :
            return False

        pdf_file = filename
        pdf_out_file = os.path.splitext(pdf_file)[0] + '[検出結果].pdf'

        # PyPDF2のツールを使用してPDFのページ情報を読み取る。
        try:
            with open(pdf_file, "rb") as input:
                reader = PR2(input)
                PageMax = len(reader.pages)     # PDFのページ数
                PaperSize = []
                for page in reader.pages:       # 各ページの用紙サイズの読取り
                    p_size = page.mediabox
                    page_xmin = float(page.mediabox.lower_left[0])
                    page_ymin = float(page.mediabox.lower_left[1])
                    page_xmax = float(page.mediabox.upper_right[0])
                    page_ymax = float(page.mediabox.upper_right[1])
                    PaperSize.append([page_xmax - page_xmin , page_ymax - page_ymin])
        except OSError as e:
            print(e)
            return 
        
        if stpage==0 :      # 検索を開始する最初のページ
            stpage = 2
        else:
            startpage = stpage
        if edpage==0 :  # 検索を終了する最後のページ
            endpage = PageMax 
        else:
            endpage = edpage

        # PDFMinerのツールの準備
        resourceManager = PDFResourceManager()
        # PDFから単語を取得するためのデバイス
        device = PDFPageAggregator(resourceManager, laparams=LAParams())
        # PDFから１文字ずつを取得するためのデバイス
        device2 = PDFPageAggregator(resourceManager)

        pageResultData = []
        # pageText = []
        pageNo = []
        limit1 = limit
        limit2 = 0.40
        limit3 = 0.40

        with open(pdf_file, 'rb') as fp:
            interpreter = PDFPageInterpreter(resourceManager, device)
            interpreter2 = PDFPageInterpreter(resourceManager, device2)
            pageI = 0
                    
            for page in PDFPage.get_pages(fp):
                pageI += 1

                # text = []
                ResultData = []
                mode = ""
                print("page={}:".format(pageI), end="")
                if pageI == 1 :
                    pageFlag = True
                    
                else:
                    if pageI < startpage:
                        print()
                        continue
                    if pageI > endpage:
                        break
                    # print(pageI)
                    pageFlag = False

                    interpreter.process_page(page)
                    layout = device.get_result()
        #
        #   このページに「柱の断面検定表」、「梁の断面検定表」、「壁の断面検定表」、「検定比図」の
        #   文字が含まれている場合のみ数値の検索を行う。
        #
                    QDL_Flag = False
                    検定表_Flag = False
                    柱_Flag = False
                    梁_Flag = False
                    壁_Flag = False
                    ブレース_Flag = False
                    杭_Flag = False
                    検定比図_Flag = False

                    xd = 3      #  X座標の左右に加える余白のサイズ（ポイント）を設定

                    mode = ""
                    for lt in layout:
                        # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
                        if isinstance(lt, LTTextContainer):
                            texts = lt.get_text()
                            if "柱の断面検定表"in texts :
                                柱_Flag = True
                                break
                            if  "梁の断面検定表"in texts:
                                梁_Flag = True
                                break
                            if "壁の断面検定表"in texts :                               
                                壁_Flag = True
                                break
                            if "断面算定表"in texts and "杭基礎"in texts:
                                杭_Flag = True
                                break
                            if "ブレースの断面検定表"in texts :
                                    ブレース_Flag = True
                                    break
                            if "検定比図"in texts:
                                検定比図_Flag = True
                                break
                    
                    if 壁_Flag:
                        i=0
                        for lt in layout:
                            # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
                            if isinstance(lt, LTTextContainer):
                                texts = lt.get_text()
                                if "ブレースの断面検定表"in texts :
                                    ブレース_Flag = True
                                    壁_Flag = False
                                    break
                            i += 1
                            if i>20:
                                break

                        
                    if 検定比図_Flag:
                        mode = "検定比図"
                    if 柱_Flag :
                        mode = "柱の検定表"
                    if 梁_Flag :
                        mode = "梁の検定表"
                    if 壁_Flag :
                        mode = "壁の検定表"
                    if 杭_Flag :
                        mode = "杭の検定表"
                    if ブレース_Flag :
                        mode = "ブレースの検定表"


                    i = 0
                    B_kind = ""
                    for lt in layout:
                        # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
                        if isinstance(lt, LTTextContainer):
                            texts = lt.get_text()
                            if "RC柱"in texts or "RC梁"in texts:
                                B_kind = "RC造"
                                break
                            if "SRC柱"in texts or "SRC梁"in texts:
                                B_kind = "SRC造"
                                break
                            if "S柱"in texts or "S梁"in texts:
                                B_kind = "S造"
                                break
                        # i +=1
                        # if i>50:
                        #     break


                    if mode == "" :     # 該当しない場合はこのページの処理は飛ばす。
                        print("No Data")
                        continue
                    else:
                        print(mode)

#=================================================================================================
#   検定比図のチェック
#=================================================================================================
                    
                    if mode == "検定比図" :

                        CharLines , CharData = self.MakeChar(page, interpreter2,device2)

                        if len(CharLines) > 0:
                            i = -1
                            for line in CharLines:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData[i] # １行文のデータを読み込む
                                
                                # if "検定比" in t3 : # 「検定比」が現れた場合の処理
                                # print(t3)
                                st = 0
                                t4 = t3.split()            # 文字列を空白で分割
                                if len(t4)>0:    # 文字列配列が１個以上ある場合に処理
                                    for t5 in t4:
                                        t6 = t5.replace("(","").replace(")","").replace(" ","")    # 「検定比」と数値が一緒の場合は除去
                                        nn = t3.find(t6,st)   # 数値の文字位置を検索
                                        ln = len(t6)

                                        # カッコがある場合は左右１文字ずつ追加
                                        if "(" in t5:
                                            xn = 1
                                        else:
                                            xn = 0

                                        if isfloat(t6):
                                            a = float(t6)
                                            if a>=limit1 and a<1.0:
                                                # 数値がlimit以上の場合はデータに登録
                                                xxx0 = CharLine[nn-xn][1]
                                                xxx1 = CharLine[nn+ln+xn-1][2]
                                                if CharLine[nn][5][1] > 0.0:
                                                    yyy0 = CharLine[nn][3] - 1.0
                                                    yyy1 = CharLine[nn+ln+xn-1][4] + 1.0
                                                elif CharLine[nn][5][1] < 0.0:
                                                    yyy0 = CharLine[nn+ln+xn-1][3] - 2.0
                                                    yyy1 = CharLine[nn][4] + 2.0
                                                else:
                                                    yyy0 = CharLine[nn][3]
                                                    yyy1 = CharLine[nn][4]

                                                if ln <=4 :
                                                    xxx0 -= xd
                                                    xxx1 += xd
                                                width3 = xxx1 - xxx0
                                                height3 = yyy1 - yyy0
                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                        # 数値を検索を開始するを文字数分移動
                                        st = nn + ln + 1
                            
#=================================================================================================
#   柱の検定表のチェック
#=================================================================================================
                                    
                    elif mode == "柱の検定表" : 

                        CharLines , CharData = self.MakeChar(page, interpreter2,device2)
                        
                        if B_kind == "RC造" or B_kind == "SRC造" or B_kind == "":
                            # =======================================================
                            #   RC造およびSRC造の柱の検定表
                            # ======================================================= 
                            if len(CharLines) > 0:
                                # lines =t1.splitlines()
                                i = -1
                                kmode = False
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    if not kmode :
                                        if "検定比" in t3 : # 最初の「検定比」が現れたら「kmode」をTrue
                                            kmode = True
                                            # 「検定比」の下にある数値だけを検出するためのX座標を取得
                                            n = t3.index("検定比")
                                            c1 = CharData[i][n]
                                            zx0 = c1[1]
                                            c2 = CharData[i][n+2]
                                            zx1 = c2[2]
                                            # print(c1[0],c2[0], zx0, zx1)
                                    else:
                                        CharLine = CharData[i] # １行文のデータを読み込む
                                        t4 = ""
                                    
                                        for char in CharLine:
                                            # kmodeの時には「検定比」の下にある数値だけを検出する。
                                            if char[1]>=zx0 and char[2]<=zx1:
                                                t4 += char[0]

                                        if isfloat(t4): # 切り取った文字が数値の場合の処理
                                            a = float(t4)
                                            if a>=limit1 and a<1.0:
                                                # 数値がlimit以上の場合はデータに登録
                                                nn = t3.index(t4)   # 数値の文字位置を検索
                                                xxx0 = CharLine[nn][1]
                                                xxx1 = CharLine[nn+3][2]
                                                yyy0 = CharLine[nn][3]
                                                yyy1 = CharLine[nn][4]
                                                xxx0 -= xd
                                                xxx1 += xd
                                                width3 = xxx1 - xxx0
                                                height3 = yyy1 - yyy0
                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                i = -1
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    
                                    CharLine = CharData[i] # １行文のデータを読み込む
                                    t4 = ""
                                
                                    for char in CharLine:
                                        # kmodeの時には「検定比」の下にある数値だけを検出する。
                                        if char[1]>zx1:
                                            t4 += char[0]
                                    if "検定比" in t4:
                                        st = 0
                                        n = t3.find("検定比",st)
                                        w0 = t4.split()
                                        if len(w0)>1:
                                            st = n + 3
                                            for w1 in w0:
                                                w2 = w1.replace("検定比","")
                                                if isfloat(w2): # 切り取った文字が数値の場合の処理
                                                    a = float(w2)
                                                    if a>=limit1 and a<1.0:
                                                        # 数値がlimit以上の場合はデータに登録
                                                        n = t3.find(w2,st)   # 数値の文字位置を検索
                                                        xxx0 = CharLine[n][1]
                                                        xxx1 = CharLine[n+3][2]
                                                        yyy0 = CharLine[n][3]
                                                        yyy1 = CharLine[n][4]
                                                        xxx0 -= xd
                                                        xxx1 += xd
                                                        width3 = xxx1 - xxx0
                                                        height3 = yyy1 - yyy0
                                                        ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                        flag = True
                                                        pageFlag = True
                                                        val = a
                                                        print('val={:.2f}'.format(val))
                                                
                                                st = t3.find(w1,st)+ len(w1)
                        if B_kind == "S造":
                            # =======================================================
                            #   S造の柱の検定表
                            # ======================================================= 
                            if len(CharLines) > 0:
                                # lines =t1.splitlines()
                                i = -1
                                kmode = False
                                fword = "σc/fc"
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    if not kmode :
                                        if fword in t3 : # 最初の「検定比」が現れたら「kmode」をTrue
                                            kmode = True
                                            # fwordより右側にある数値だけを検出するためのX座標を取得
                                            n = t3.index(fword)
                                            c1 = CharData[i][n]
                                            zx0 = c1[1]
                                    else:
                                        if kmode :
                                            
                                            CharLine = CharData[i] # １行文のデータを読み込む
                                            t4 = ""
                                        
                                            for char in CharLine:
                                                # kmodeの時には「検定比」の下にある数値だけを検出する。
                                                if char[1]>=zx0 :
                                                    t4 += char[0]
                                            if t4 == "": # 
                                                kmode = False
                                            else:
                                                st = 0
                                                w0 = t4.split()
                                                if len(w0)>1:
                                                    for w1 in w0:
                                                        w2 = w1.replace(" ","")
                                                        if isfloat(w2): # 切り取った文字が数値の場合の処理
                                                            a = float(w2)
                                                            if a>=limit3 and a<1.0:
                                                                # 数値がlimit以上の場合はデータに登録
                                                                n = t3.find(w2,st)   # 数値の文字位置を検索
                                                                xxx0 = CharLine[n][1]
                                                                xxx1 = CharLine[n+3][2]
                                                                yyy0 = CharLine[n][3]
                                                                yyy1 = CharLine[n][4]
                                                                xxx0 -= xd
                                                                xxx1 += xd
                                                                width3 = xxx1 - xxx0
                                                                height3 = yyy1 - yyy0
                                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                                flag = True
                                                                pageFlag = True
                                                                val = a
                                                                print('val={:.2f}'.format(val))
                                                        
                                                        st = t3.find(w1,st)+ len(w1)


#=================================================================================================
#   梁の検定表のチェック
#=================================================================================================
                                        
                    elif mode == "梁の検定表" : 

                        CharLines , CharData = self.MakeChar(page, interpreter2,device2)
                        if B_kind == "RC造" or B_kind == "SRC造" or B_kind == "":
                            # =======================================================
                            #   RC造およびSRC造の梁の検定表
                            # ======================================================= 
                            
                            if len(CharLines) > 0:
                            
                                # lines =t1.splitlines()
                                i = -1
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    CharLine = CharData[i] # １行文のデータを読み込む
                                    
                                    if "検定比" in t3 : # 「検定比」が現れた場合の処理
                                        # print(t3)
                                        st = 0
                                        t4 = t3.split()            # 文字列を空白で分割
                                        if len(t4)>0:    # 文字列配列が１個以上ある場合に処理
                                            for t5 in t4:
                                                t6 = t5.replace("検定比","")    # 「検定比」と数値が一緒の場合は除去
                                                nn = t3.find(t6,st)   # 数値の文字位置を検索
                                                ln = len(t5)
                                                if isfloat(t6):
                                                    a = float(t6)
                                                    if a>=limit1 and a<1.0:
                                                        # 数値がlimit以上の場合はデータに登録
                                                        xxx0 = CharLine[nn][1]
                                                        xxx1 = CharLine[nn+3][2]
                                                        yyy0 = CharLine[nn][3]
                                                        yyy1 = CharLine[nn][4]
                                                        xxx0 -= xd
                                                        xxx1 += xd
                                                        width3 = xxx1 - xxx0
                                                        height3 = yyy1 - yyy0
                                                        ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                        flag = True
                                                        pageFlag = True
                                                        val = a
                                                        print('val={:.2f}'.format(val))

                                                # 数値を検索を開始するを文字数分移動
                                                st = t3.find(t5,st)+ len(t5)
                                                # st += ln

                        if B_kind == "S造":
                            # =======================================================
                            #   S造の梁の検定表
                            # ======================================================= 
                            
                            if len(CharLines) > 0:
                                # lines =t1.splitlines()
                                i = -1
                                kmode = False
                                fword = "σb/fb"
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    if not kmode :
                                        if fword in t3 : # 最初のfwordが現れたら「kmode」をTrue
                                            kmode = True
                                            # fwordより右側にある数値だけを検出するためのX座標を取得
                                            n = t3.index(fword) + len(fword)-1
                                            c1 = CharData[i][n]
                                            zx0 = c1[1]
                                    if kmode :
                                        CharLine = CharData[i] # １行文のデータを読み込む
                                        t4 = ""
                                    
                                        for char in CharLine:
                                            # kfwordより右側にある数値だけを検出する。
                                            if char[1]>=zx0 :
                                                t4 += char[0]
                                        if t4 == "": # 
                                            kmode = False
                                        else:
                                            st = 0
                                            w0 = t4.split()
                                            if len(w0)>1:
                                                for w1 in w0:
                                                    w2 = w1.replace(" ","")
                                                    if isfloat(w2): # 切り取った文字が数値の場合の処理
                                                        a = float(w2)
                                                        if a>=limit1 and a<1.0:
                                                            # 数値がlimit以上の場合はデータに登録
                                                            n = t3.find(w2,st)   # 数値の文字位置を検索
                                                            xxx0 = CharLine[n][1]
                                                            xxx1 = CharLine[n+3][2]
                                                            yyy0 = CharLine[n][3]
                                                            yyy1 = CharLine[n][4]
                                                            xxx0 -= xd
                                                            xxx1 += xd
                                                            width3 = xxx1 - xxx0
                                                            height3 = yyy1 - yyy0
                                                            ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                            flag = True
                                                            pageFlag = True
                                                            val = a
                                                            print('val={:.2f}'.format(val))
                                                    
                                                    st = t3.find(w1,st)+ len(w1)
                                            
#=================================================================================================
#   耐力壁の検定表のチェック
#=================================================================================================

                    elif mode == "壁の検定表":
                        outtext1 , CharData1 = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:
                            i = -1
                            tn = len(outtext1)

                            while True:
                                i += 1
                                if i > tn-1 : break

                                t3 = outtext1[i][0]
                                # print(t3)
                                CharLine = CharData1[i]
                                if "QDL" in t3:
                                    nn = t3.find("QDL",0)   # 数値の文字位置を検索
                                    xxx0 = CharLine[nn][1]
                                    yyy1 = CharLine[nn][4]
                                    t4 = t3[nn+3:].replace(" ","")
                                    if isfloat(t4):
                                        A1 = float(t4)
                                    else:
                                        A1 = 0.0
                                    
                                    i += 1
                                    t3 = outtext1[i][0]
                                    CharLine = CharData1[i]
                                    
                                    nn  = t3.find("QAL",0) 
                                    yyy0 = CharLine[nn][3]

                                    t4 = t3[nn+3:].replace(" ","")
                                    nn2 = len(t3[nn:])
                                    
                                    xxx1 = CharLine[nn+nn2-1][2]
                                    yyy0 = CharLine[nn+nn2-1][3]
                                    
                                    if isfloat(t4):
                                        A2 = float(t4)
                                    else:
                                        A2 = 10000.0
                                    QDL_mode = False
                                    
                                    if A2 != 0.0:
                                        a = abs(A1/A2)
                                        if a>=limit2 and a<1.0:
                                            
                                            xxx0 -= xd
                                            xxx1 += xd
                                            width3 = xxx1 - xxx0
                                            height3 = yyy1 - yyy0
                                            points = []
                                            points.append((xxx0,yyy0,xxx1,yyy0))
                                            points.append((xxx1,yyy0,xxx1,yyy1))
                                            points.append((xxx1,yyy1,xxx0,yyy1))
                                            points.append((xxx0,yyy1,xxx0,yyy0))
                                            ResultData.append([a,[xxx0, yyy0, width3, height3],True,points])
                                            flag = True
                                            pageFlag = True
                                            val = a
                                            print('val={:.2f}'.format(val))

                                    i += 1
                                    t3 = outtext1[i][0]
                                    # print(t3)
                                    CharLine = CharData1[i]

                                    nn = t3.find("QDS",0)   # 数値の文字位置を検索
                                    xxx0 = CharLine[nn][1]
                                    yyy1 = CharLine[nn][4]
                                    t4 = t3[nn+3:].replace(" ","")
                                    if isfloat(t4):
                                        A1 = float(t4)
                                    else:
                                        A1 = 0.0
                                    QDL_mode = True
                                        
                                
                                    i += 1
                                    t3 = outtext1[i][0]
                                    CharLine = CharData1[i]
                                    
                                    nn = t3.find("QAS",0)
                                    yyy0 = CharLine[nn][3]

                                    t4 = t3[nn+3:].split()[0]
                                    nn2 = len(t3[nn:])
                                    
                                    xxx1 = CharLine[nn+nn2-1][2]
                                    yyy0 = CharLine[nn+nn2-1][3]
                                    
                                    if isfloat(t4):
                                        A2 = float(t4)
                                    else:
                                        A2 = 10000.0
                                    QDL_mode = False
                                    
                                    if A2 != 0.0:
                                        a = abs(A1/A2)
                                        if a>=limit2 and a<1.0:
                                            
                                            xxx0 -= xd
                                            xxx1 += xd
                                            width3 = xxx1 - xxx0
                                            height3 = yyy1 - yyy0
                                            ResultData.append([a,[xxx0, yyy0, width3, height3],True])
                                            flag = True
                                            pageFlag = True
                                            val = a
                                            print('val={:.2f}'.format(val))

                    if mode == "杭の検定表":
                        pageFlaf = False


#=================================================================================================
#   ブレースの検定表のチェック
#=================================================================================================
                                    
                    elif mode == "ブレースの検定表" : 

                        CharLines , CharData = self.MakeChar(page, interpreter2,device2)
                        
                        if len(CharLines) > 0:
                                # lines =t1.splitlines()
                                i = -1
                                kmode = False
                                for line in CharLines:
                                    i += 1
                                    t3 = line[0]
                                    fword = "Nt/Nat"
                                    if not kmode :
                                        if fword in t3 : # 最初の「検定比」が現れたら「kmode」をTrue
                                            kmode = True
                                            # 「検定比」の下にある数値だけを検出するためのX座標を取得
                                            n = t3.index(fword)
                                            c1 = CharData[i][n]
                                            zx0 = c1[1]
                                            c2 = CharData[i][n+len(fword)-1]
                                            zx1 = c2[2]
                                            # print(c1[0],c2[0], zx0, zx1)
                                    else:
                                        CharLine = CharData[i] # １行文のデータを読み込む
                                        t4 = ""
                                    
                                        for char in CharLine:
                                            # kmodeの時には「検定比」の下にある数値だけを検出する。
                                            if char[1]>=zx0 :
                                                t4 += char[0]
                                        if t4 == "" :
                                            kmode = False

                                        if isfloat(t4): # 切り取った文字が数値の場合の処理
                                            st = 0
                                            w0 = t4.split()
                                            if len(w0)>1:
                                                for w1 in w0:
                                                    w2 = w1.replace(" ","")
                                                    if isfloat(w2): # 切り取った文字が数値の場合の処理
                                                        a = float(w2)
                                                        if a>=limit3 and a<1.0:
                                                            # 数値がlimit以上の場合はデータに登録
                                                            n = t3.find(w2,st)   # 数値の文字位置を検索
                                                            xxx0 = CharLine[n][1]
                                                            xxx1 = CharLine[n+3][2]
                                                            yyy0 = CharLine[n][3]
                                                            yyy1 = CharLine[n][4]
                                                            xxx0 -= xd
                                                            xxx1 += xd
                                                            width3 = xxx1 - xxx0
                                                            height3 = yyy1 - yyy0
                                                            ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                            flag = True
                                                            pageFlag = True
                                                            val = a
                                                            print('val={:.2f}'.format(val))
                                                    
                                                    st = t3.find(w1,st)+ len(w1)
                                            





                                            # a = float(t4)
                                            # if a>=limit1 and a<1.0:
                                            #     # 数値がlimit以上の場合はデータに登録
                                            #     nn = t3.index(t4)   # 数値の文字位置を検索
                                            #     xxx0 = CharLine[nn][1]
                                            #     xxx1 = CharLine[nn+3][2]
                                            #     yyy0 = CharLine[nn][3]
                                            #     yyy1 = CharLine[nn][4]
                                            #     xxx0 -= xd
                                            #     xxx1 += xd
                                            #     width3 = xxx1 - xxx0
                                            #     height3 = yyy1 - yyy0
                                            #     ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                            #     flag = True
                                            #     pageFlag = True
                                            #     val = a
                                            #     print('val={:.2f}'.format(val))




                if pageFlag : 
                    pageNo.append(pageI)
                    pageResultData.append(ResultData)
                    

        # 使用したデバイスをクローズ
        device.close()
        device2.close()

        #============================================================================================
        #
        #   数値検出結果を用いて各ページに四角形を描画する
        #

        in_path = pdf_file
        out_path = pdf_out_file

        # 保存先PDFデータを作成
        cc = canvas.Canvas(out_path)
        cc.setLineWidth(1)
        # PDFを読み込む
        pdf = PdfReader(in_path, decompress=False)

        i = 0
        for pageI in range(len(pageNo)):
            pageN = pageNo[pageI]
            pageSizeX = float(PaperSize[pageN-1][0])
            pageSizeY = float(PaperSize[pageN-1][1])
            page = pdf.pages[pageN - 1]
            ResultData = pageResultData[pageI]
            # PDFデータへのページデータの展開
            pp = pagexobj(page) #ページデータをXobjへの変換
            rl_obj = makerl(cc, pp) # ReportLabオブジェクトへの変換  
            cc.doForm(rl_obj) # 展開

            if pageN == 1:  # 表紙に「"検定比（0.##以上）の検索結果」の文字を印字
                cc.setFillColor("red")
                font_name = "ipaexg"
                cc.setFont(font_name, 20)
                cc.drawString(20 * mm,  pageSizeY - 40 * mm, "検定比（{}以上）の検索結果".format(limit1))

            else:   # ２ページ目以降は以下の処理
                pn = len(ResultData)

                # ページの左肩に検出個数を印字
                cc.setFillColor("red")
                font_name = "ipaexg"
                cc.setFont(font_name, 12)
                t2 = "検索個数 = {}".format(pn)
                cc.drawString(20 * mm,  pageSizeY - 15 * mm, t2)

                # 該当する座標に四角形を描画
                for R1 in ResultData:
                    a = R1[0]
                    origin = R1[1]
                    flag = R1[2]
                    x0 = origin[0]
                    y0 = origin[1]
                    width = origin[2]
                    height = origin[3]

                    # 長方形の描画
                    cc.setFillColor("white", 0.5)
                    cc.setStrokeColorRGB(1.0, 0, 0)
                    cc.rect(x0, y0, width, height, fill=0)

                    if flag:    # "壁の検定表"の場合は、四角形の右肩に数値を印字
                        cc.setFillColor("red")
                        font_name = "ipaexg"
                        cc.setFont(font_name, 7)
                        t2 = " {:.2f}".format(a)
                        cc.drawString(origin[0]+origin[2], origin[1]+origin[3], t2)

            # ページデータの確定
            cc.showPage()

        # PDFの保存
        cc.save()


if __name__ == '__main__':

    
    time_sta = time.time()  # 開始時刻の記録

    CT = CheckTool()

    # stpage = 100
    # edpage = 300
    # limit = 0.70
    # filename = "サンプル計算書(1).pdf"

    # stpage = 100
    # edpage = 0
    # limit = 0.70
    # filename = "サンプル計算書(1)a.pdf"

    # stpage = 100
    # edpage = 0
    # limit = 0.70
    # filename = "新_サンプル計算書(2)PDF.pdf"

    # stpage = 2
    # edpage = 136
    # limit = 0.70
    # filename = "サンプル計算書(3)抜粋.pdf"

    stpage = 2
    edpage = 0
    limit = 0.70
    filename = "サンプル計算書(3)抜粋.pdf"


    CT.CheckTool(filename,limit=limit,stpage=stpage,edpage=edpage)
    

    t1 = time.time() - time_sta
    print("time = {} sec".format(t1))

