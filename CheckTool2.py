


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

import os
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

#==================================================================================
#   構造計算書の数値検出ツールのClass
#       
#       Coded by kanyama (2022/01)
#==================================================================================
class CheckTool():
    #==================================================================================
    #   オブジェクトのインスタンス化および初期化
    #==================================================================================
    
    def __init__(self):
        # 源真ゴシック等幅フォント
        GEN_SHIN_GOTHIC_MEDIUM_TTF = "/Library/Fonts/GenShinGothic-Monospace-Medium.ttf"
        self.fontname1 = 'GenShinGothic'
        # IPAexゴシックフォント
        IPAEXG_TTF = "/Library/Fonts/ipaexg.ttf"
        self.fontname2 = 'ipaexg'
        
        # フォント登録
        pdfmetrics.registerFont(TTFont(self.fontname1, GEN_SHIN_GOTHIC_MEDIUM_TTF))
        pdfmetrics.registerFont(TTFont(self.fontname2, IPAEXG_TTF))
        # print(pdfmetrics.getRegisteredFontNames())

        initFile = "init.json"
        if not os.path.isfile(initFile):
            dir = os.getcwd()
            fld = filedialog.askdirectory(initialdir = dir) 
            self.dir1 = fld + "/処理前フォルダ"
            self.dir2 = fld + "/処理後フォルダ"

            pageData = {"処理前フォルダ":self.dir1,"処理前フォルダ":self.dir2}
            # data_json = json.dumps(pageData, indent=4, ensure_ascii=False)
            with open('init.json', 'w') as fp:
                json.dump(pageData, fp, indent=4, ensure_ascii=False)
        else:
            json_open = open(initFile, 'r')
            json_load = json.load(json_open)
            self.dir1 = json_load['処理前フォルダ']
            self.dir2 = json_load['処理前フォルダ']

        # self.pdf_file = FileName
        # self.pdf_out_file = os.path.splitext(self.pdfFileName)[0] + '[検出結果].pdf'

    def MakeChar(self ,page, interpreter, device):

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
                # elif m1[1] > 0.0 :
                #     CharDataPlus.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                # elif m1[1] <0.0 :
                #     CharDataMinus.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                
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
            outtext1 = []
            CharOutPut1 = []
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
                outtext1.append([t2])
                # print(t2,len(F3))
                CharOutPut1.append(F3)
        

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
        outtext2 = []
        CharOutPut2 = []
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
                    CharOutPut2.append(fline)
                    outtext2.append([tt2])
                    fline = []
                    tt2 = ""
                    Sflag = False
                else:
                    fline.append(F1)
                    tt2 += F1[0]

        if len(fline)>0:
            CharOutPut2.append(fline)
            outtext2.append([tt2])

        


        # その際、CharData2をY座標の高さ順に並び替えるためのリスト「CY」を作成
        # CharData2=[]
        # CY = []
        # for cdata in CharData:
        #     char2 = cdata[0]
        #     x0 = cdata[1]
        #     x1 = cdata[2]
        #     y0 = cdata[3]
        #     y1 = cdata[4]
            
        #     CharData2.append(cdata)
        #     CY.append(int(y0))
        
        # # リスト「CY」から降順の並び替えインデックッスを取得
        # y=np.argsort(np.array(CY))[::-1]

        # if len(CharData2) > 0:  # リストが空でない場合に処理を行う
        #     CharData3 = []
        #     # インデックスを用いて並べ替えた「CharData3」を作成
        #     for i in range(len(y)):
        #         CharData3.append(CharData2[y[i]])

        #     # 同じ高さのY座標毎にデータをまとめる２次元のリストを作成
        #     CharData4 = []
        #     i = 0
        #     for f in CharData3:
        #         if i==0 :   # 最初の文字のY座標を基準値に採用し、仮のリストを初期化
        #             Fline = []
        #             Fline.append(f)
        #             gy0 = int(f[3])
        #             gy1 = int(f[4])
        #         else:
        #             if int(f[4])>= gy0 and int(f[4])<= gy1:   # 同じY座標の場合は、リストに文字を追加
        #                 Fline.append(f)
        #             else:           # Y座標が異なる場合は、リストを「CharData4」を保存し、仮のリストを初期化
        #                 if len(Fline) >= 4:
        #                     CharData4.append(Fline)
        #                 Fline = []
        #                 Fline.append(f)
        #                 gy0 = int(f[3])
        #                 gy1 = int(f[4])

        #         i += 1
        #     # 仮のリストが残っている場合は、リストを「CharData4」を保存
        #     if len(Fline) >= 4:
        #         CharData4.append(Fline)

        #     # 次にX座標の順番にデータを並び替える（昇順）
        #     t1 = []
        #     CharOutPut2 = []
        #     for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
        #         CX = []         # 各データのX座標のデータリストを作成
        #         for F2 in F1:
        #             CX.append(F2[1])
                
        #         # リスト「CX」から降順の並び替えインデックッスを取得
        #         x=np.argsort(np.array(CX))
                
        #         # インデックスを用いて並べ替えた「F3」を作成
        #         F3 = []
        #         t2 = ""
        #         for i in range(len(x)):
        #             F3.append(F1[x[i]])
        #             t3 = F1[x[i]][0]
        #             t2 += t3
        #         # t1 += t2 + "\n"
        #         t1.append([t2])
        #         # print(t2,len(F3))
        #         CharOutPut2.append(F3)


        
        return outtext1 , CharOutPut1, outtext2, CharOutPut2







    #==================================================================================
    #   RC造用の関数
    #==================================================================================

    def RC_Check(self,FileName , limit = 0.95, stpage = 0 , edpage=0):
        if not os.path.isfile(FileName):
            print('ファイルがありません！！')
            return False

        pdf_file = FileName
        pdf_out_file = os.path.splitext(FileName)[0] + '[検出結果].pdf'
        print(pdf_out_file)

        a=0
        # PyPDF2のツールを使用してPDFのページ情報を読み取る。
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
        limit1 = 0.70
        limit2 = 0.40

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
                    杭_Flag = False
                    検定比図_Flag = False

                    xd = 0      #  X座標の左右に加える余白のサイズ（ポイント）を設定

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
                            if "検定比図"in texts:
                                検定比図_Flag = True
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
                
                    if mode == "" :     # 該当しない場合はこのページの処理は飛ばす。
                        print("No Data")
                        continue
                    else:
                        print(mode)

                    
                    if mode == "検定比図" :

                        outtext1 , CharData1, outtext2 ,CharData2 = self.MakeChar(page, interpreter2,device2)

                        if len(outtext1) > 0:
                            i = -1
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData1[i] # １行文のデータを読み込む
                                
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
                                                xxx1 = CharLine[nn+ln+xn][2]
                                                yyy0 = CharLine[nn][3]
                                                yyy1 = CharLine[nn][4]
                                                if ln <=4 :
                                                    xxx0 -= xd
                                                    xxx1 += xd
                                                width3 = xxx1 - xxx0
                                                height3 = yyy1 - yyy0

                                                points = []
                                                points.append((xxx0,yyy0,xxx1,yyy0))
                                                points.append((xxx1,yyy0,xxx1,yyy1))
                                                points.append((xxx1,yyy1,xxx0,yyy1))
                                                points.append((xxx0,yyy1,xxx0,yyy0))
                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                        # 数値を検索を開始するを文字数分移動
                                        st = nn + ln + 1
                            
                        if len(outtext2) > 0:
                            i = -1
                            for line in outtext2:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData2[i] # １行文のデータを読み込む
                                
                                # if "検定比" in t3 : # 「検定比」が現れた場合の処理
                                # print(t3)
                                st = 0
                                t4 = t3.split()            # 文字列を空白で分割
                                if len(t4)>0:    # 文字列配列が１個以上ある場合に処理
                                    for t5 in t4:
                                        t6 = t5.replace("(","").replace(")","").replace(" ","").replace("組","")    # 「検定比」と数値が一緒の場合は除去
                                        nn = t3.find(t6,st)   # 数値の文字位置を検索
                                        ln = len(t6)

                                        # カッコがある場合は左右１文字ずつ追加
                                        if "(" in t5:
                                            xn = 1
                                        else:
                                            xn = 0

                                        if isfloat(t6):
                                            a = float(t6)
                                            points= []
                                                    
                                            if a>=limit1 and a<1.0:
                                                # 数値がlimit以上の場合はデータに登録

                                                # xxx0 = CharLine[nn][1]
                                                # xxx1 = CharLine[nn][2]
                                                # yyy0 = CharLine[nn][3]
                                                # yyy1 = CharLine[nn][4]
                                                # points.append((xxx0,yyy0,xxx1,yyy0))
                                                # points.append((xxx1,yyy0,xxx1,yyy1))
                                                # points.append((xxx1,yyy1,xxx0,yyy1))
                                                # points.append((xxx0,yyy1,xxx0,yyy0))

                                                # p1 = [(xxx0+xxx1)/2.0,(yyy0+yyy1)/2.0]
                                                # xxxx0 = CharLine[nn+ln-1][1]
                                                # xxxx1 = CharLine[nn+ln-1][2]
                                                # yyyy0 = CharLine[nn+ln-1][3]
                                                # yyyy1 = CharLine[nn+ln-1][4]
                                                # points.append((xxxx0,yyyy0,xxxx1,yyyy0))
                                                # points.append((xxxx1,yyyy0,xxxx1,yyyy1))
                                                # points.append((xxxx1,yyyy1,xxxx0,yyyy1))
                                                # points.append((xxxx0,yyyy1,xxxx0,yyyy0))

                                                # p2 = [(xxxx0+xxxx1)/2.0,(yyyy0+yyyy1)/2.0]
                                                # CL = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                                                # cc = (p2[1]-p1[1])/(p2[0]-p1[0])
                                                # th = math.atan(cc)

                                                # if abs(th) > 0.0 :
                                                #     points.append([p1[0],p1[1],p2[0],p2[1]])


                                                #     c1 = math.cos(th)
                                                #     s1 = math.sin(th)
                                                #     cx = p1[0]
                                                #     cy = p1[1]
                                                #     dw = 3
                                                #     dh = 5
                                                #     x = [cx-dw , cx+CL+dw , cx+CL+dw , cx-dw , cx-dw]
                                                #     y = [cy-dh ,cy -dh , cy+dh , cy+dh , cy-dh]
                                                #     PP = []
                                                #     for i in range(len(x)):
                                                #         XX = c1*x[i] - s1*y[i] + cx-cx*c1+cy*s1
                                                #         YY = s1*x[i] + s1*y[i] + cy-cx*s1-cy*c1
                                                #         PP.append([XX , YY])
                                                #     # points = []
                                                #     for i in range(len(PP)-1):
                                                #         points.append([PP[i][0],PP[i][1],PP[i+1][0],PP[i+1][1]])


                                                # # xmin = 10000.0
                                                # # xmax = -10000.0
                                                # # ymin = 10000.0
                                                # # ymax = -10000.0
                                                # # for i in range(ln):
                                                # #     if CharLine[nn+i][1] < xmin:
                                                        
                                                # else:

                                                # if CharLine[nn][3][1]>0.0 :
                                                #     dy0 = 0.0
                                                #     dy1 = 6.0
                                                # else:
                                                #     dy0 = -6.0
                                                #     dy1 = 0.0
                                                xxx0 = CharLine[nn-xn][1]
                                                xxx1 = CharLine[nn+ln+xn-1][2]
                                                if CharLine[nn][5][1]>0.0:
                                                    yyy0 = CharLine[nn][3]
                                                    yyy1 = CharLine[nn+ln+xn-1][4]
                                                else:
                                                    yyy0 = CharLine[nn+ln+xn-1][3]-3.0
                                                    yyy1 = CharLine[nn][4]

                                                if ln <=4 :
                                                    xxx0 -= xd
                                                    xxx1 += xd
                                                width3 = xxx1 - xxx0
                                                height3 = yyy1 - yyy0
                                                points = []
                                                points.append((xxx0,yyy0,xxx1,yyy0))
                                                points.append((xxx1,yyy0,xxx1,yyy1))
                                                points.append((xxx1,yyy1,xxx0,yyy1))
                                                points.append((xxx0,yyy1,xxx0,yyy0))

                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                        # 数値を検索を開始するを文字数分移動
                                        st = nn + ln + 1
                        








                    elif mode == "柱の検定表" : 

                        outtext1 , CharData1, outtext2 ,CharData2  = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:
                            # lines =t1.splitlines()
                            i = -1
                            kmode = False
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                if kmode == False:                           
                                    if "検定比" in t3 : # 奇数回目の「検定比」が現れたら「kmode」をTrue
                                        kmode = True
                                        # 「検定比」の下にある数値だけを検出するためのX座標を取得
                                        n = t3.index("検定比")
                                        c1 = CharData1[i][n]
                                        zx0 = c1[1]
                                        c2 = CharData1[i][n+2]
                                        zx1 = c2[2]
                                        # print(c1[0],c2[0], zx0, zx1)
                                else:
                                    # kmode=Trueの場合の処理
                                    
                                    CharLine = CharData1[i] # １行文のデータを読み込む
                                    t4 = ""
                                    xxx0 = 100000.0
                                    yyy0 = 100000.0
                                    xxx1 = -100000.0
                                    yyy1 = -100000.0
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
                                            points = []
                                            points.append((xxx0,yyy0,xxx1,yyy0))
                                            points.append((xxx1,yyy0,xxx1,yyy1))
                                            points.append((xxx1,yyy1,xxx0,yyy1))
                                            points.append((xxx0,yyy1,xxx0,yyy0))
                                            ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                            flag = True
                                            pageFlag = True
                                            val = a
                                            print('val={:.2f}'.format(val))
                                    
                                    if "検定比" in t3 : # 偶数回目の「検定比」が現れたら「kmode」をFalseにする
                                        kmode = False

                                        # まず、同様に検定比」の下にある数値だけを検出する。
                                        t4 = ""
                                        xxx0 = 100000.0
                                        yyy0 = 100000.0
                                        xxx1 = -100000.0
                                        yyy1 = -100000.0
                                        for char in CharLine:
                                            if char[1]>=zx0 and char[2]<=zx1:
                                                t4 += char[0]

                                        if isfloat(t4):
                                            a = float(t4)
                                            if a>=limit1 and a<1.0:
                                                nn = t3.index(t4)   # 数値の文字位置を検索
                                                xxx0 = CharLine[nn][1]
                                                xxx1 = CharLine[nn+3][2]
                                                yyy0 = CharLine[nn][3]
                                                yyy1 = CharLine[nn][4]
                                                points = []
                                                points.append((xxx0,yyy0,xxx1,yyy0))
                                                points.append((xxx1,yyy0,xxx1,yyy1))
                                                points.append((xxx1,yyy1,xxx0,yyy1))
                                                points.append((xxx0,yyy1,xxx0,yyy0))
                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                    #　続いて検定比」の右側にある数値を検出する。
                                        n = t3.index("検定比")      # 偶数回目の「検定比」の文字位置を検索
                                        t4 = t3[n+3:]              # 「検定比」の右側だけの文字列を取得
                                        st = n + 3
                                        t5 = t4.split()            # 文字列を空白で分割
                                        if len(t5)>0:    # 文字列配列が１個以上ある場合に処理
                                            for t6 in t5:
                                                if isfloat(t6):
                                                    a = float(t6)
                                                    if a>=limit1 and a<1.0:
                                                        # 数値がlimit以上の場合はデータに登録
                                                        nn = t3.find(t6,st)   # 数値の文字位置を検索
                                                        xxx0 = CharLine[nn][1]
                                                        xxx1 = CharLine[nn+3][2]
                                                        yyy0 = CharLine[nn][3]
                                                        yyy1 = CharLine[nn][4]
                                                        xxx0 -= xd
                                                        xxx1 += xd
                                                        width3 = xxx1 - xxx0
                                                        height3 = yyy1 - yyy0
                                                        points = []
                                                        points.append((xxx0,yyy0,xxx1,yyy0))
                                                        points.append((xxx1,yyy0,xxx1,yyy1))
                                                        points.append((xxx1,yyy1,xxx0,yyy1))
                                                        points.append((xxx0,yyy1,xxx0,yyy0))
                                                        ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                                        flag = True
                                                        pageFlag = True
                                                        val = a
                                                        print('val={:.2f}'.format(val))
                                                st += len(t6)
                                            
                                        
                    elif mode == "梁の検定表" : 

                        outtext1 , CharData1, outtext2 ,CharData2  = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:

                            # lines =t1.splitlines()
                            i = -1
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData1[i] # １行文のデータを読み込む
                                
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
                                                    points = []
                                                    points.append((xxx0,yyy0,xxx1,yyy0))
                                                    points.append((xxx1,yyy0,xxx1,yyy1))
                                                    points.append((xxx1,yyy1,xxx0,yyy1))
                                                    points.append((xxx0,yyy1,xxx0,yyy0))
                                                    ResultData.append([a,[xxx0, yyy0, width3, height3],False,points])
                                                    flag = True
                                                    pageFlag = True
                                                    val = a
                                                    print('val={:.2f}'.format(val))

                                            # 数値を検索を開始するを文字数分移動
                                            st += ln
                                            

                    elif mode == "壁の検定表":
                        outtext1 , CharData1, outtext2 ,CharData2  = self.MakeChar(page, interpreter2,device2)
                        
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


                    if mode == "杭の検定表":
                        pageFlaf = False


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
                cc.rotate(a)
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
                    points = R1[3]

                    # 長方形の描画
                    cc.setFillColor("white", 0.5)
                    cc.setStrokeColorRGB(1.0, 0, 0)
                    cc.rect(x0, y0, width, height, fill=0)
                    # cc.lines(points)
                    # cc.lines([(20,0,20,10), (20,30,20,40), (0,20,10,20), (30,20,40,20)])

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

        
        # return True


    #==================================================================================
    #   SRC造用の関数
    #==================================================================================

    def SRC_Check(self,FileName , limit = 0.95, stpage = 0 , edpage=0):
        if not os.path.isfile(FileName):
            print('ファイルがありません！！')
            return False

        pdf_file = FileName
        pdf_out_file = os.path.splitext(FileName)[0] + '[検出結果].pdf'
        print(pdf_out_file)

        a=0
        # PyPDF2のツールを使用してPDFのページ情報を読み取る。
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
        limit1 = 0.70
        limit2 = 0.40

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
                            if "検定比図"in texts:
                                検定比図_Flag = True
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
                
                    if mode == "" :     # 該当しない場合はこのページの処理は飛ばす。
                        print("No Data")
                        continue
                    else:
                        print(mode)

                    
                    if mode == "検定比図" :

                        # for lt in layout:
                        #     # LTTextContainerの場合だけ標準出力
                        #     if isinstance(lt, LTTextContainer):
                                
                        #         words = lt.get_text()
                        #         datas = lt.get_text().splitlines()
                        #         data2 = [] 
                        #         if mode == "検定比図":
                        #             for data in datas:                          
                        #                 data2.append(data.split())

                        #         elif mode == "柱の検定表":        
                        #             if "検定比" in words:
                        #                 for data in datas:
                        #                     data2.append(data.split())
                                            
                        #         else:        
                        #             if "検定比" in words:
                        #                 for data in datas:
                        #                     if "検定比" in data:
                        #                         data2.append(data.split())
                        #                     else:
                        #                         data2.append([""])

                        #         words = lt.get_text().split()
                        #         x0 = lt.x0
                        #         x1 = lt.x1
                        #         y0 = lt.y0
                        #         y1 = lt.y1
                        #         width = lt.width
                        #         height = lt.height

                        #         flag = False
                        #         i = 0
                        #         n1 = 0
                        #         for data in data2:
                        #             if not("QAL" in data or "QAS" in data):
                        #                 n1 += 1

                        #         n2 = 0
                        #         for d1 in data2:
                        #             if len(d1) > n2 : n2 = len(d1)

                        #         for d1 in data2:
                        #             if not("QAL" in d1 or "QAS" in d1):
                        #                 i += 1
                        #             j = 0
                                    
                        #             for d2 in d1:
                        #                 j += 1
                        #                 if j > n2 : j=n2
                        #                 t = d2.replace("(","").replace(")","")
                        #                 if isfloat(t) or isint(t):
                        #                     a = float(t)
                        #                     if a >= limit1 and a < 1.0 :
                        #                         xx0 = x0 + (j-1)*width/n2
                        #                         if mode == "柱の検定表" and j == 1 : 
                        #                             xx0 += 5.0
                        #                         yy0 = y1 - height * i / n1
                        #                         height2 = height / n1
                        #                         if height2 < 7.0 : height2 = 7.0
                        #                         width2 =  width/n2
                        #                         # text.append(d2)
                        #                         ResultData.append([a,[xx0, yy0, width2, height2],False])
                        #                         flag = True
                        #                         pageFlag = True

                        #         if flag :
                        #             # print("-------")
                        #             # print(datas)
                        #             print("-------")
                        #             print('{}, x0={:.2f}, x1={:.2f}, y0={:.2f}, y1={:.2f}, width={:.2f}, height={:.2f}'.format(
                        #                 lt.get_text().strip(), lt.x0, lt.x1, lt.y0, lt.y1, lt.width, lt.height))
                        #             print("-------")




                        outtext1 , CharData5, outtext2 ,CharData66= self.MakeChar(page, interpreter2,device2)

                        for char2 in CharData5:
                            for char in char2:
                                c = char[0]
                                x0 = char[1]
                                x1 = char[2]
                                y0 = char[3]
                                y1 = char[4]
                                w = x1 - x0
                                h = y1 - y0
                                print("{}, w={:.2f}, h={:.2f}, x0={:.2f}, x1={:.2f}, y0={:.2f}, y1={:.2f}".format(c,w,h,x0,x1,y0,y1))
                            
                        if len(outtext1) > 0:
                            i = -1
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData5[i] # １行文のデータを読み込む
                                
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
                                                xxx1 = CharLine[nn+ln+xn][2]
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
                            
                                    
                    elif mode == "柱の検定表" : 

                        outtext1 , CharData5, outtext2 ,CharData6 = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:
                            # lines =t1.splitlines()
                            i = -1
                            kmode = False
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                if kmode == False:                           
                                    if "検定比" in t3 : # 奇数回目の「検定比」が現れたら「kmode」をTrue
                                        kmode = True
                                        # 「検定比」の下にある数値だけを検出するためのX座標を取得
                                        n = t3.index("検定比")
                                        c1 = CharData5[i][n]
                                        zx0 = c1[1]
                                        c2 = CharData5[i][n+2]
                                        zx1 = c2[2]
                                        # print(c1[0],c2[0], zx0, zx1)
                                else:
                                    # kmode=Trueの場合の処理
                                    
                                    CharLine = CharData5[i] # １行文のデータを読み込む
                                    t4 = ""
                                    xxx0 = 100000.0
                                    yyy0 = 100000.0
                                    xxx1 = -100000.0
                                    yyy1 = -100000.0
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
                                    
                                    if "検定比" in t3 : # 偶数回目の「検定比」が現れたら「kmode」をFalseにする
                                        kmode = False

                                        # まず、同様に検定比」の下にある数値だけを検出する。
                                        t4 = ""
                                        xxx0 = 100000.0
                                        yyy0 = 100000.0
                                        xxx1 = -100000.0
                                        yyy1 = -100000.0
                                        for char in CharLine:
                                            if char[1]>=zx0 and char[2]<=zx1:
                                                t4 += char[0]

                                        if isfloat(t4):
                                            a = float(t4)
                                            if a>=limit1 and a<1.0:
                                                nn = t3.index(t4)   # 数値の文字位置を検索
                                                xxx0 = CharLine[nn][1]
                                                xxx1 = CharLine[nn+3][2]
                                                yyy0 = CharLine[nn][3]
                                                yyy1 = CharLine[nn][4]
                                                ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                                flag = True
                                                pageFlag = True
                                                val = a
                                                print('val={:.2f}'.format(val))

                                    #　続いて検定比」の右側にある数値を検出する。
                                        n = t3.index("検定比")      # 偶数回目の「検定比」の文字位置を検索
                                        t4 = t3[n+3:]              # 「検定比」の右側だけの文字列を取得
                                        st = n + 3
                                        t5 = t4.split()            # 文字列を空白で分割
                                        if len(t5)>0:    # 文字列配列が１個以上ある場合に処理
                                            for t6 in t5:
                                                if isfloat(t6):
                                                    a = float(t6)
                                                    if a>=limit1 and a<1.0:
                                                        # 数値がlimit以上の場合はデータに登録
                                                        nn = t3.find(t6,st)   # 数値の文字位置を検索
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
                                                st += len(t6)
                                            
                                        
                    elif mode == "梁の検定表" : 

                        outtext1 , CharData5, outtext2 ,CharData6 = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:

                            # lines =t1.splitlines()
                            i = -1
                            for line in outtext1:
                                i += 1
                                t3 = line[0]
                                CharLine = CharData5[i] # １行文のデータを読み込む
                                
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
                                            st += ln
                                            

                    elif mode == "壁の検定表":
                        outtext1 , CharData5, outtext2 ,CharData6 = self.MakeChar(page, interpreter2,device2)
                        
                        if len(outtext1) > 0:
                            i = -1
                            tn = len(outtext1)

                            while True:
                                i += 1
                                if i > tn-1 : break

                                t3 = outtext1[i][0]
                                # print(t3)
                                CharLine = CharData5[i]
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
                                    CharLine = CharData5[i]
                                    
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
                                            ResultData.append([a,[xxx0, yyy0, width3, height3],True])
                                            flag = True
                                            pageFlag = True
                                            val = a
                                            print('val={:.2f}'.format(val))

                                    i += 1
                                    t3 = outtext1[i][0]
                                    # print(t3)
                                    CharLine = CharData5[i]

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
                                    CharLine = CharData5[i]
                                    
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

        
        # return True



    #==================================================================================
    #   S造用の関数
    #==================================================================================

    def S_Check(self,FileName , limit = 0.95, stpage = 0 , edpage=0):
        if not os.path.isfile(FileName):
            print('ファイルがありません！！')
            return False

        pdf_file = FileName
        pdf_out_file = os.path.splitext(FileName)[0] + '[検出結果].pdf'
        print(pdf_out_file)

        a=0

        # PyPDF2のツールを使用してPDFのページ情報を読み取る。
        with open(pdf_file, "rb") as input:
            reader = PR2(input)
            PageMax = len(reader.pages)     # PDFのページ数
            PaperSize = []
            for page in reader.pages:       # 各ページの用紙サイズの読取り
                p_size = page.mediabox
                x0 = page.mediabox.lower_left[0]
                y0 = page.mediabox.lower_left[1]
                x1 = page.mediabox.upper_right[0]
                y1 = page.mediabox.upper_right[1]
                PaperSize.append([x1 - x0 , y1 - y0])


        # PDFMinerのツールの準備
        resourceManager = PDFResourceManager()
        device = PDFPageAggregator(resourceManager, laparams=LAParams())

        if stpage==0 :      # 検索を開始する最初のページ
            stpage = 2
        else:
            startpage = stpage
        if edpage==0 :  # 検索を終了する最後のページ
            endpage = PageMax 
        else:
            endpage = edpage
        pageResultData = []
        # pageText = []
        pageNo = []
        limit1 = limit
        limit2 = 0.40

        with open(pdf_file, 'rb') as fp:
            interpreter = PDFPageInterpreter(resourceManager, device)
            pageI = 0
                    
            for page in PDFPage.get_pages(fp):
                pageI += 1

                # text = []
                ResultData = []
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

                    QDL_Flag = False
                    検定表_Flag = False
                    柱_Flag = False
                    梁_Flag = False
                    壁_Flag = False
                    検定比図_Flag = False
                    mode = ""
                    for lt in layout:
                        # LTTextContainerの場合だけ標準出力
                        if isinstance(lt, LTTextContainer):
                            texts = lt.get_text()
                            if "柱の断面検定表"in texts :
                                柱_Flag = True
                            if  "梁の断面検定表"in texts:
                                梁_Flag = True
                            if "壁の断面検定表"in texts :
                                壁_Flag = True
                            if "検定比図"in texts:
                                検定比図_Flag = True
                        
                    if 検定比図_Flag:
                        mode = "検定比図"
                    if 柱_Flag :
                        mode = "柱の検定表"
                    if 梁_Flag :
                        mode = "梁の検定表"
                    if 壁_Flag :
                        mode = "壁の検定表"
                
                    if mode == "" :
                        print("Pass")
                        continue
                    else:
                        print(mode)

                    
                    if mode == "検定比図" or mode == "柱の検定表" or mode == "梁の検定表": 
                        
                        for lt in layout:
                            # LTTextContainerの場合だけ標準出力
                            if isinstance(lt, LTTextContainer):
                                
                                words = lt.get_text()
                                datas = lt.get_text().splitlines()
                                data2 = [] 
                                if mode == "検定比図":
                                    for data in datas:                          
                                        data2.append(data.split())

                                elif mode == "柱の検定表":        
                                    if "検定比" in words:
                                        for data in datas:
                                            data2.append(data.split())
                                            
                                else:        
                                    if "検定比" in words:
                                        for data in datas:
                                            if "検定比" in data:
                                                data2.append(data.split())
                                            else:
                                                data2.append([""])

                                words = lt.get_text().split()
                                x0 = lt.x0
                                x1 = lt.x1
                                y0 = lt.y0
                                y1 = lt.y1
                                width = lt.width
                                height = lt.height

                                flag = False
                                i = 0
                                n1 = 0
                                for data in data2:
                                    if not("QAL" in data or "QAS" in data):
                                        n1 += 1

                                n2 = 0
                                for d1 in data2:
                                    if len(d1) > n2 : n2 = len(d1)

                                for d1 in data2:
                                    if not("QAL" in d1 or "QAS" in d1):
                                        i += 1
                                    j = 0
                                    
                                    for d2 in d1:
                                        j += 1
                                        if j > n2 : j=n2
                                        t = d2.replace("(","").replace(")","")
                                        if isfloat(t) or isint(t):
                                            a = float(t)
                                            if a >= limit1 and a < 1.0 :
                                                xx0 = x0 + (j-1)*width/n2
                                                if mode == "柱の検定表" and j == 1 : 
                                                    xx0 += 5.0
                                                yy0 = y1 - height * i / n1
                                                height2 = height / n1
                                                if height2 < 7.0 : height2 = 7.0
                                                width2 =  width/n2
                                                # text.append(d2)
                                                ResultData.append([a,[xx0, yy0, width2, height2],False])
                                                flag = True
                                                pageFlag = True

                                if flag :
                                    # print("-------")
                                    # print(datas)
                                    print("-------")
                                    print('{}, x0={:.2f}, x1={:.2f}, y0={:.2f}, y1={:.2f}, width={:.2f}, height={:.2f}'.format(
                                        lt.get_text().strip(), lt.x0, lt.x1, lt.y0, lt.y1, lt.width, lt.height))
                                    print("-------")
                        
                    elif mode == "壁の検定表":
                        # print("壁")
                        QGL_Mode = False
                        for lt in layout:
                            # LTTextContainerの場合だけ標準出力
                            if isinstance(lt, LTTextContainer):
                                data0 = lt.get_text()
                                # print(data0)
                                if QGL_Mode == False:
                                    if "QDL" in data0:

                                        datas = data0.splitlines()
                                        
                                        QDL_x0 = lt.x0
                                        QDL_x1 = lt.x1
                                        QDL_y0 = lt.y0
                                        QDL_y1 = lt.y1
                                        QDL_width = lt.width
                                        QDL_height = lt.height
                                        QGL_Mode = True
                                else:
                                    datas = data0.splitlines()
                                    x0 = lt.x0
                                    x1 = lt.x1
                                    y0 = lt.y0
                                    y1 = lt.y1
                                    width = lt.width
                                    height = lt.height

                                    if len(datas) == 4 and y0 == QDL_y0 and y1 == QDL_y1:
                                        x = []
                                        QGL_Mode = False
                                        for data in datas:
                                            t = data.split()[0]
                                            t = t.replace("(","").replace(")","")
                                            if isint(t) or isfloat(t):
                                                a = float(t)
                                                x.append(a)
                                        
                                        c = []
                                        if x[1] != 0:
                                            c.append(abs(x[0]/x[1]))
                                        else:
                                            c.append(0.0)

                                        if x[3] != 0:
                                            c.append(abs(x[2]/x[3]))
                                        else:
                                            c.append(0.0)

                                        i = 0
                                        for c1 in c:
                                            i += 1
                                            if c1 >= limit2 and c1 < 1.0 :
                                                xx0 = QDL_x0
                                                yy0 = QDL_y1 - QDL_height * i / 2
                                                height2 = QDL_height / 2
                                                if height2 < 7.0 : height2 = 7.0
                                                width2 = x1 - QDL_x0
                                                # text.append(c1)
                                                ResultData.append([c1,[xx0, yy0, width2, height2],True])
                                                pageFlag = True

                if pageFlag : 
                    pageNo.append(pageI)
                    # pageText.append(text)
                    pageResultData.append(ResultData)

        device.close()
        # print(pageText)

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

            if pageN == 1:
                cc.setFillColor("red")
                font_name = "ipaexg"
                cc.setFont(font_name, 20)
                cc.drawString(20 * mm,  pageSizeY - 40 * mm, "検定比（{}以上）の検索結果".format(limit1))
            else:
                pn = len(ResultData)
                cc.setFillColor("red")
                font_name = "ipaexg"
                cc.setFont(font_name, 12)
                t2 = "検索個数 = {}".format(pn)
                cc.drawString(20 * mm,  pageSizeY - 15 * mm, t2)
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

                    if flag:
                        cc.setFillColor("red")
                        font_name = "ipaexg"
                        cc.setFont(font_name, 7)
                        t2 = " {:.2f}".format(a)
                        cc.drawString(origin[0]+origin[2], origin[1]+origin[3], t2)

            # ページデータの確定
            cc.showPage()

        # PDFの保存
        cc.save()
        return True

