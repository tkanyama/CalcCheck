

#==========================================================================================
#   構造計算書の数値検査プログラムのサブルーチン（ver.0.01）
#
#           一般財団法人日本建築総合試験所
#
#               coded by T.Kanyama  2023/02
#
#==========================================================================================
"""
このプログラムは、構造判定センターに提出される構造計算書（PDF）の検定比（許容応力度に対する部材応力度の比）を精査し、
設定した閾値（デフォルトは0.95）を超える部材を検出するプログラムのツールである。

"""
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

# その他のimport
import os,time
import sys
import numpy as np
import logging
import re

kind = ""
version = ""

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
    #end if
#end def

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
    #end if
#end def

#============================================================================
#
#   構造計算書のチェックを行うclass
#
#============================================================================

class CheckTool():
    #==================================================================================
    #   オブジェクトのインスタンス化および初期化
    #==================================================================================
    
    def __init__(self):

        self.BeamMemberSpan = {}    # 部材符号と諸元データの辞書
        
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
    #end def
    #*********************************************************************************


    #==================================================================================
    #   表紙の文字から構造計算プログラムの種類とバージョンを読み取る関数
    #==================================================================================

    def CoverCheck(self, page, interpreter, device):
        global kind, version

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
                #end if
            #end if
        #next

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
        #next
        
        # リスト「CY」から降順の並び替えインデックッスを取得
        y=np.argsort(np.array(CY))[::-1]

        if len(CharData2) > 0:  # リストが空でない場合に処理を行う
            CharData3 = []
            # インデックスを用いて並べ替えた「CharData3」を作成
            for i in range(len(y)):
                CharData3.append(CharData2[y[i]])
            #next

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
                    #end if
                #end if
                i += 1
            #next

            # 仮のリストが残っている場合は、リストを「CharData4」を保存
            if len(Fline) >= 4:
                CharData4.append(Fline)
            #end if

            # 次にX座標の順番にデータを並び替える（昇順）
            t1 = []
            CharData5 = []
            for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
                CX = []         # 各データのX座標のデータリストを作成
                for F2 in F1:
                    CX.append(F2[1])
                #next
                
                # リスト「CX」から降順の並び替えインデックッスを取得
                x=np.argsort(np.array(CX))
                
                # インデックスを用いて並べ替えた「F3」を作成
                F3 = []
                t2 = ""
                for i in range(len(x)):
                    F3.append(F1[x[i]])
                    t3 = F1[x[i]][0]
                    t2 += t3
                #next
                # t1 += t2 + "\n"
                t1.append([t2])
                # print(t2,len(F3))
                CharData5.append(F3)
            #next
        #end if

        CharData2 = []
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] > 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                #end if
            #end if
        #next
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] < 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                #end if
            #end if
        #next

        fline = []
        Sflag = False
        tt2 = ""

        fline = []
        Sflag = False
        tt2 = ""
        for F1 in CharData2:
            if not Sflag:
                if F1[0] != " ":
                    fline.append(F1)
                    tt2 += F1[0]
                    Sflag = True
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
                #end if
            #end if
        #next

        if len(fline)>0:
            CharData5.append(fline)
            t1.append([tt2])
        #end if
        kind ="不明"
        vesion = "不明"
        for line in t1:
            # 全角の'：'と'／'を半角に置換
            t2 = line[0].replace(" ","").replace("：",":").replace("／","/")

            if "プログラムの名称" in t2:
                n = t2.find(":",0)
                kind = t2[n+1:]
            elif "プログラムバージョン" in t2:
                n = t2.find(":",0)
                version = t2[n+1:]
                break
            #end if
        #next
        
        return kind , version
    #end def
    #*********************************************************************************


    #==================================================================================
    #   各ページから１文字ずつの文字と座標データを抽出し、行毎の文字配列および座標配列を戻す関数
    #==================================================================================

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
                #end if
            #end if
        #next

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
        #next
        
        # リスト「CY」から降順の並び替えインデックッスを取得
        y=np.argsort(np.array(CY))[::-1]

        if len(CharData2) > 0:  # リストが空でない場合に処理を行う
            CharData3 = []
            # インデックスを用いて並べ替えた「CharData3」を作成
            for i in range(len(y)):
                CharData3.append(CharData2[y[i]])
            #next

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
                        if len(Fline) >= 2:
                            CharData4.append(Fline)
                        gy = int(f[3])
                        Fline = []
                        Fline.append(f)
                    #end if
                #end if
                i += 1
            #next
            # 仮のリストが残っている場合は、リストを「CharData4」を保存
            if len(Fline) >= 4:
                CharData4.append(Fline)
            #end if

            # 次にX座標の順番にデータを並び替える（昇順）
            t1 = []
            CharData5 = []
            for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
                CX = []         # 各データのX座標のデータリストを作成
                for F2 in F1:
                    CX.append(F2[1])
                #next
                
                # リスト「CX」から降順の並び替えインデックッスを取得
                x=np.argsort(np.array(CX))
                
                # インデックスを用いて並べ替えた「F3」を作成
                F3 = []
                t2 = ""
                for i in range(len(x)):
                    F3.append(F1[x[i]])
                    t3 = F1[x[i]][0]
                    if t3 != " ":
                        t2 += t3
                    #end if
                #next
                # t1 += t2 + "\n"
                t1.append([t2])
                # print(t2,len(F3))
                CharData5.append(F3)
            #next
        #end if

        CharData2 = []
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] > 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                #end if
            #end if
        #nexr
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] < 0.0 : # 正の回転している文字のみを抽出
                    CharData2.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                #end if
            #end iuf
        #next
        
        fline = []
        Sflag = False
        tt2 = ""
        
        fline = []
        Sflag = False
        tt2 = ""
        for F1 in CharData2:
            if not Sflag:
                if F1[0] != " ":
                    fline.append(F1)
                    tt2 += F1[0]
                    Sflag = True
                #end if
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
                #end if
            #end if
        #next

        if len(fline)>0:
            tt2=tt2.replace(" ","").replace("　","")
            CharData5.append(fline)
            t1.append([tt2])
        #end if

        return t1 , CharData5
    #end def
    #*********************************************************************************

#==================================================================================
#   各ページから１文字ずつの文字と座標データを抽出し、行毎の文字配列および座標配列を戻す関数
#==================================================================================

    def MakeCharPlus(self, page, interpreter, device):

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
                #end if
            #end if
        #next

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
        #next
        
        # リスト「CY」から昇順の並び替えインデックッスを取得
        y=np.argsort(np.array(CY))  #[::-1]

        if len(CharData2) > 0:  # リストが空でない場合に処理を行う
            CharData3 = []
            # インデックスを用いて並べ替えた「CharData3」を作成
            for i in range(len(y)):
                CharData3.append(CharData2[y[i]])
            #next

            # 同じ高さのY座標毎にデータをまとめる２次元のリストを作成
            CharData4 = []
            i = 0
            dy = 3
            dx = 7
            for f in CharData3:
                if i==0 :   # 最初の文字のY座標を基準値に採用し、仮のリストを初期化
                    Fline = []
                    Fline.append(f)
                    gy = int(f[3])
                else:
                    # if int(f[3])>= gy-dy and int(f[3])<= gy+dy:   # 同じY座標に近い場合は、リストに文字を追加
                    if int(f[3])== gy :   # 同じY座標の場合は、リストに文字を追加
                        Fline.append(f)
                    else:           # Y座標が異なる場合は、リストを「CharData4」を保存し、仮のリストを初期化
                        if len(Fline) >= 2: #2文字以上を追加
                            CharData4.append(Fline)
                        gy = int(f[3])
                        Fline = []
                        Fline.append(f)
                    #end if
                #end if
                i += 1
            #next
            # 仮のリストが残っている場合は、リストを「CharData4」を保存
            if len(Fline) >= 4:
                CharData4.append(Fline)
            #end if

            # 次にX座標の順番にデータを並び替える（昇順）
            t1H = []
            CharDataH = []
            for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
                CX = []         # 各データのX座標のデータリストを作成
                for F2 in F1:
                    CX.append(F2[1])
                #next
                
                # リスト「CX」から降順の並び替えインデックッスを取得
                x=np.argsort(np.array(CX))
                
                # インデックスを用いて並べ替えた「F3」を作成
                F3 = []
                t2 = ""
                F0 = F1[x[0]]
                x2 = F0[2]
                for i in range(len(x)):
                    F0 = F1[x[i]]
                    F3.append(F0)
                    t3 = F0[0]
                    if F0[1]>x2+dx:
                        t2 += " "
                    #end if
                    t2 += t3
                    x2 = F0[2]
                    
                #next
                # t1 += t2 + "\n"
                t1H.append([t2])
                # print(t2,len(F3))
                CharDataH.append(F3)
            #next
        #end if

        CharData = []
        for lt in layout:
            if isinstance(lt, LTChar):  # レイアウトデータうち、LTCharのみを取得
                char1 = lt.get_text()   # レイアウトデータに含まれる全文字を取得
                if lt.matrix[1] != 0.0 : # 回転している文字のみを抽出
                    CharData.append([char1, lt.x0, lt.x1, lt.y0, lt.y1,lt.matrix])
                #end if
            #end if
        #next
        

        # その際、CharData2をX座標の順に並び替えるためのリスト「CX」を作成
        CharData2=[]
        CX = []
        for cdata in CharData:
            char2 = cdata[0]
            x0 = cdata[1]
            x1 = cdata[2]
            y0 = cdata[3]
            y1 = cdata[4]
            
            CharData2.append(cdata)
            CX.append(int(x0))
        #next
        
        # リスト「CX」から降順の並び替えインデックッスを取得
        x=np.argsort(np.array(CX)) # [::-1]

        if len(CharData2) > 0:  # リストが空でない場合に処理を行う
            CharData3 = []
            # インデックスを用いて並べ替えた「CharData3」を作成
            for i in range(len(x)):
                CharData3.append(CharData2[x[i]])
            #next

            # 同じX座標毎にデータをまとめる２次元のリストを作成
            CharData4 = []
            i = 0
            dy = 7
            dx = 3
            for f in CharData3:
                if i==0 :   # 最初の文字のY座標を基準値に採用し、仮のリストを初期化
                    Fline = []
                    Fline.append(f)
                    gx = int(f[1])
                else:   
                    # if int(f[1])>= gx-dx and int(f[1])<= gx+dx:   # 同じY座標の場合は、リストに文字を追加
                    if int(f[1]) == gx :   # 同じY座標の場合は、リストに文字を追加
                        Fline.append(f)
                    else:           # Y座標が異なる場合は、リストを「CharData4」を保存し、仮のリストを初期化
                        if len(Fline) >= 2:
                            CharData4.append(Fline)
                        gx = int(f[1])
                        Fline = []
                        Fline.append(f)
                    #end if
                #end if
                i += 1
            #next
            # 仮のリストが残っている場合は、リストを「CharData4」を保存
            if len(Fline) >= 2:
                CharData4.append(Fline)
            #end if

            # 次にY座標の順番にデータを並び替える（昇順）
            t1V = []
            CharDataV = []
            for F1 in CharData4:    # Y座標が同じデータを抜き出す。                        
                CY = []         # 各データのX座標のデータリストを作成
                for F2 in F1:
                    CY.append(F2[3])
                #next
                
                # リスト「CX」から降順の並び替えインデックッスを取得
                y=np.argsort(np.array(CY))
                
                # インデックスを用いて並べ替えた「F3」を作成


                # t2 = ""
                # F0 = F1[x[0]]
                # x2 = F0[2]
                # for i in range(len(x)):
                #     F0 = F1[x[i]]
                #     F3.append(F0)
                #     t3 = F0[0]
                #     if F0[1]>x2+dx:
                #         t2 += " "
                #     #end if
                #     t2 += t3
                #     x2 = F0[2]  

                F3 = []
                t2 = ""
                F0 = F1[y[0]]
                y2 = F0[4]
                for i in range(len(y)):
                    F0 = F1[y[i]]
                    F3.append(F0)
                    t3 = F0[0]
                    if F0[3]>y2+dy:
                        t2 += " "
                    #end if
                    t2 += t3
                    y2 = F0[4] 
                #next
                # t1 += t2 + "\n"
                t1V.append([t2])
                # print(t2,len(F3))
                CharDataV.append(F3)
            #next
        #end if


        return t1H , CharDataH, t1V , CharDataV
    #end def
    #*********************************************************************************

#==================================================================================
#   床伏図から部材の符号と配置を検出する関数
#==================================================================================
    def BeamMemberSearch(self,CharLinesH , CharDataH, CharLinesV , CharDataV):
        # X1の文字がある行を検索
        Xst = []
        i = -1
        for line in CharLinesH:
            # print(line[0])
            i += 1
            if "X1" in line[0]:
                Xst.append(i)
            #end if
        #next
        Xst.append(len(CharDataH))

        
        for k in range(len(Xst)-1):
            #各階の床伏図

            stline = Xst[k]-2
            edline = Xst[k+1]-2
            X = []
            Xname = []
            Y = []
            Yname = []
            Xlength1 = 0
            Xlength2 = []
            Scale = 1
            ymin = CharDataH[stline][0][3]
            ymax = CharDataH[edline][0][4]

            for i in range(stline,edline):
                # i += 1
                line = CharLinesH[i][0]
                # print(line)
                items = line.split()
                line2 = line.replace(" ","")
                st = 0
                for item in items:
                    if re.match('X\d+', item):  # X1,X2,・・・・X通りの座標
                        CharData = CharDataH[i]            
                        n = line2.find(item, st)
                        x0 = CharData[n][1]
                        x1 = CharData[n+len(item)-1][2]
                        X.append((x0+x1)/2.0)
                        Xname.append(item)
                        st = n + len(item)

                    elif re.match('\d+FL\S+', item) or re.match('RFL\S+', item):   # 階高
                        FloorName = item.replace("層","")

                    elif re.match('S=\d+/\d+', item):   # スケールの読取り
                        n = line2.find("/",st)
                        Scale = int(line2[n+1:])
                        st = n + len(item)
                            
                    elif re.match('\d+', item):     # X方向寸法の読取り
                        if isint(item):
                            if len(items)>1:    # 寸法が複数横並びの場合は柱間
                                if int(item)>=1000:
                                    Xlength2.append(int(item))
                                #end if
                            else:               # 寸法がひとつの場合は合計寸法
                                if int(item)>=1000:
                                    Xlength1 = int(item)
                                #end if
                            #end if
                        #end if

                    elif re.match('Y\d+', item):  # Y1,Y2,・・・・Y通りの座標
                        CharData = CharDataH[i]            
                        n = line2.find(item, st)
                        y0 = CharData[n][3]
                        y1 = CharData[n][4]
                        Y.append((y0+y1)/2.0)
                        Yname.append(item)
                        st = n + len(item)
                    #end if
                #next
            #next

            Ylength1 = 0
            Ylength2 = []
            for i in range(len(CharLinesV)):
                line = ""
                yy= CharDataV[i][0][4]
                for Char in CharDataV[i]:
                    if Char[3]>=ymin and Char[4]<=ymax:                       
                        if Char[3]>yy+7:
                            line += " "
                        line += Char[0]
                        yy = Char[4]
                    #end if
                #next
                # line = CharLinesV[i][0]
                # print(line)
                items = line.split()
                line2 = line.replace(" ","")
                st = 0
                for item in items:
                    if re.match('\d+', item):     # Y方向寸法の読取り
                        if isint(item):
                            if len(items)>1:    # 寸法が複数横並びの場合は柱間
                                if int(item)>=1000:
                                    Ylength2.append(int(item))
                                #end if
                            else:               # 寸法がひとつの場合は合計寸法
                                if int(item)>=1000:
                                    Ylength1 = int(item)
                                #end if
                            #end if
                        #end if

            # 部材記号と部材長、
            for i in range(stline,edline):
                # i += 1
                line = CharLinesH[i][0]
                # print(line)
                items = line.split()
                line2 = line.replace(" ","")
                st = 0
                for item in items:
                    CharData = CharDataH[i]            
                    n = line2.find(item, st)
                    x0 = CharData[n][1]
                    x1 = CharData[n+len(item)-1][2]
                    xm = (x0+x1)/2.0
                    y0 = CharData[n][3]
                    y1 = CharData[n+len(item)-1][4]
                    ym = (y0+y1)/2.0
                    st = n + len(item)
                    # if re.match('\d+G\d+', item) or re.match('-\d+G\d+', item) or re.match('B\d+', item) or re.match('RG\d+', item) or re.match('-RG\d+', item):     # 大梁
                    if re.match('\S*\d+G\d+', item) or re.match('B\d+', item) or re.match('\S*RG\d+', item) or re.match('\S*FG\d+', item) :     # 大梁
                        if len(items)==1: 
                            xposition = Xname[0]+"-"+Xname[len(Xname)-1]
                            j=-1
                            yposition = ""
                            for y in Y:
                                j += 1
                                if ym <= y + 7 and ym>=y-7:
                                    yposition = Yname[j]
                                    break
                                #end if
                            #next
                            
                            if not item in self.BeamMemberSpan:
                                d1 = [[str(Xlength1),FloorName,xposition,yposition]] 
                                dic1 = {}
                                dic1["配置"] = d1
                                self.BeamMemberSpan[item] = dic1
                                continue
                            else:
                                dic1 = self.BeamMemberSpan[item]
                                d2= d1["配置"]
                                d2.append([str(Xlength1),FloorName, xposition,yposition])
                                dic1["配置"] = d2
                                self.BeamMemberSpan[item] = dic1
                                continue
                            #end if
                        else:
                            # CharData = CharDataH[i]            
                            # n = line2.find(item, st)
                            # x0 = CharData[n][1]
                            # x1 = CharData[n+len(item)-1][2]
                            item2 = item.replace("-","")
                            for j in range(len(X)-1):
                                if x0 > X[j] and x1 < X[j+1]:
                                    xlen = Xlength2[j]
                                    xposition = Xname[j]+"-"+Xname[j+1]
                                    jj=-1
                                    yposition = ""
                                    for y in Y:
                                        jj += 1
                                        if ym <= y + 5 and ym>=y-5:
                                            yposition = Yname[jj]
                                            continue
                                        #end if
                                    #next
                                    if not item2 in self.BeamMemberSpan:
                                        d1 = [[str(xlen),FloorName, xposition,yposition]]
                                        dic1 = {}
                                        dic1["配置"] = d1
                                        self.BeamMemberSpan[item2] = dic1
                                        # self.BeamMemberSpan[item2] = d1
                                        # self.memberSpan[item2] = str(Xlength2[j])
                                        continue
                                    else:
                                        dic1 = self.BeamMemberSpan[item2]
                                        d2 = dic1["配置"]
                                        d2.append([str(Xlength1),FloorName, xposition,yposition])
                                        dic1["配置"] = d2
                                        self.BeamMemberSpan[item2] = dic1
                                
                                        # d1 = self.BeamMemberSpan[item2]
                                        # d2 = d1
                                        # d2.append([str(xlen),FloorName,xposition,yposition])
                                        # # d3 = [d1[0],d2]
                                        # self.BeamMemberSpan[item2] = d2
                                        continue
                                #end if
                            #next
                        #end if
                    #end if
                #next
            #next

            # Ylength1 = 0
            # Ylength2 = []
            st = 0
            for i in range(len(CharLinesV)):
                line = ""
                yy= CharDataV[i][0][4]
                CharDataV2 = []                     # ここから修せ
                for Char in CharDataV[i]:
                    if Char[3]>=ymin and Char[4]<=ymax:                       
                        if Char[3]>yy+7:
                            line += " "
                        line += Char[0]
                        CharDataV2.append(Char)
                        yy = Char[4]
                    #end if
                #next
                # line = CharLinesV[i][0]
                # print(line)
                items = line.split()
                line2 = line.replace(" ","")
                # st = 0
                for item in items:
                    CharData = CharDataV[i]            
                    n = line2.find(item, st)
                    x0 = CharData[n][1]
                    x1 = CharData[n+len(item)-1][2]
                    xm = (x0+x1)/2.0
                    y0 = CharData[n][3]
                    y1 = CharData[n+len(item)-1][4]
                    ym = (y0+y1)/2.0
                    st = n + len(item)

                    if re.match('\S*\d+G\d+', item) or re.match('B\d+', item) or re.match('\S*RG\d+', item) or re.match('\S*FG\d+', item):     # 大梁、小梁
                        if len(items)==1:

                            yposition = Yname[0]+"-"+Yname[len(Yname)-1]
                            xposition = ""
                            for j in range(len(X)):
                                if xm <= X[j] + 20 and xm >= X[j] -20:
                                    xposition = Xname[j]
                                    break
                                #end if
                            #next
                            for j in range(len(X)-1):    
                                if xm <= (X[j]+X[j+1])/2.0 + 20 and xm >= (X[j]+X[j+1])/2.0 - 20:
                                    xposition = Xname[j]+"-"+Xname[j+1]
                                    break
                                #end if
                            #next
                            if not item in self.BeamMemberSpan:
                                d1 = [[str(Ylength1),FloorName, xposition,yposition]]
                                dic1 = {}
                                dic1["配置"] = d1
                                self.BeamMemberSpan[item] = dic1
                                # self.BeamMemberSpan[item] = d1
                                continue
                            else:
                                dic1 = self.BeamMemberSpan[item]
                                d2= dic1["配置"]
                                d2.append([str(Xlength1),FloorName, xposition,yposition])
                                dic1["配置"] = d2
                                self.BeamMemberSpan[item] = dic1
                                # d1 = self.BeamMemberSpan[item]
                                # d2= d1
                                # d2.append([str(Ylength1),FloorName, xposition,yposition])
                                # # d3 = [d1[0],d2]
                                # self.BeamMemberSpan[item] = d2
                                continue
                            #end if
                        else:
                            
                            for j in range(len(Y)-1):
                                if y0 > Y[j] and y1 < Y[j+1]:
                                    ylen = Ylength2[j]
                                    yposition = Yname[j]+"-"+Yname[j+1]
                                    xposition = ""
                                    for jj in range(len(X)-1):
                                        if xm <= X[jj] + 7 and xm >= X[jj] -7:
                                            xposition = Xname[jj]
                                            continue
                                        elif xm <=(X[jj]+X[jj+1])/2.0 + 7 and xm >=(X[jj]+X[jj+1])/2.0 - 7:
                                            xposition = Xname[jj]+"-"+Xname[jj+1]
                                            continue
                                        #end if
                                    #next

                                    if not item in self.BeamMemberSpan:
                                        d1 = [[str(ylen),FloorName, xposition,yposition]]
                                        dic1 = {}
                                        dic1["配置"] = d1
                                        self.BeamMemberSpan[item] = dic1
                                        # d1 = [[str(ylen),FloorName, xposition,yposition]]
                                        # self.BeamMemberSpan[item] = d1
                                        break
                                    else:
                                        dic1 = self.BeamMemberSpan[item]
                                        d2= dic1["配置"]
                                        d2.append([str(ylen),FloorName, xposition,yposition])
                                        dic1["配置"] = d2
                                        self.BeamMemberSpan[item] = dic1
                                        # d1 = self.BeamMemberSpan[item]
                                        # d2= d1
                                        # d2.append([str(ylen),FloorName, xposition,yposition])
                                        # # d3 = [d1[0],d2]
                                        # self.BeamMemberSpan[item] = d2
                                        break
                                    #end if
                                #end if
                            #next
                        #end if
                    #end if
                #next
            #next
        #next







    #==================================================================================
    #   各ページの数値を検索し、閾値を超える数値を四角で囲んだPDFファイルを作成する関数
    #   （SS7用の関数）
    #==================================================================================

    def SS7(self, page, limit, interpreter, device,interpreter2, device2):
        
        #============================================================
        # 構造計算書がSS7の場合の処理
        #============================================================
        pageFlag = False
        ResultData = []
        limit1 = limit
        limit2 = limit
        limit3 = limit
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
        床伏図_Flag = False
        断面リスト_Flag = False

        xd = 3      #  X座標の左右に加える余白のサイズ（ポイント）を設定

        mode = ""
        for lt in layout:
            # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
            if isinstance(lt, LTTextContainer):
                texts = lt.get_text()
                if "柱の断面検定表"in texts :
                    柱_Flag = True
                    break
                #end if
                if  "梁の断面検定表"in texts:
                    梁_Flag = True
                    break
                #end if
                if "壁の断面検定表"in texts :                               
                    壁_Flag = True
                    break
                #end if
                if "断面算定表"in texts and "杭基礎"in texts:
                    杭_Flag = True
                    break
                #end if
                if "ブレースの断面検定表"in texts :
                    ブレース_Flag = True
                    break
                #end if
                if "検定比図"in texts:
                    検定比図_Flag = True
                    break
                #end if
                if "床伏図"in texts:
                    床伏図_Flag = True
                    break
                #end if
                if "断面リスト"in texts:
                    断面リスト_Flag = True
                    break
                #end if
            #end if
        #next
        
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
                    #end if
                #enf if
                i += 1
                if i>20:
                    break
                #end if
            #next
        #end if
            
        if 検定比図_Flag:
            mode = "検定比図"
        #end if
        if 柱_Flag :
            mode = "柱の検定表"
        #end if
        if 梁_Flag :
            mode = "梁の検定表"
        #end if
        if 壁_Flag :
            mode = "壁の検定表"
        #end if
        if 杭_Flag :
            mode = "杭の検定表"
        #end if
        if ブレース_Flag :
            mode = "ブレースの検定表"
        #end if
        if 床伏図_Flag :
            mode = "床伏図"
        #end if
        if 断面リスト_Flag :
            mode = "断面リスト"
        #end if



        
        i = 0
        B_kind = ""
        for lt in layout:
            # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
            if isinstance(lt, LTTextContainer):
                texts = lt.get_text()
                if "RC柱"in texts or "RC梁"in texts:
                    B_kind = "RC造"
                    break
                #end if
                if "SRC柱"in texts or "SRC梁"in texts:
                    B_kind = "SRC造"
                    break
                #end if
                if "S柱"in texts or "S梁"in texts:
                    B_kind = "S造"
                    break
                #end if
            #end if
        #next

        if mode == "" :     # 該当しない場合はこのページの処理は飛ばす。
            print("No Data")
            return False,[]
        else:
            print(mode)
        #end if


        #=================================================================================================
        #   床伏図の部材寸法チェック
        #=================================================================================================
        
        if mode == "床伏図" :
            CharLinesH , CharDataH, CharLinesV , CharDataV = self.MakeCharPlus(page, interpreter2,device2)
            self.BeamMemberSearch(CharLinesH , CharDataH, CharLinesV , CharDataV)
            keys = list(self.BeamMemberSpan.keys())
            for key in keys:
                dic1 = self.BeamMemberSpan[key]
                print(key,dic1)

            a=0
            # print(self.BeamMemberSpan)
        
        #=================================================================================================
        #   断面リストのチェック
        #=================================================================================================
        
        if mode == "断面リスト" :

            CharLines , CharData = self.MakeChar(page, interpreter2,device2)

            if len(CharLines) > 0:
                ucount = 0
                scount = 0
                断面サイズ = []
                主筋上端 = []
                主筋下端 = []
                材料上端 = []
                材料下端 = []
                かぶり上端 = []
                かぶり下端 = []
                あばら筋 = []
                あばら筋材料 = []
                memberName = []
                itemsx = []
                nameCenter = []
                        

                for i in range(len(CharLines)):
                    
                    line = CharLines[i][0]
                    line2 = ""
                    xx= CharData[i][0][2]
                    for Char in CharData[i]:
                        if Char[1]>xx+7:
                            line2 += " "
                        line2 += Char[0]
                        xx = Char[2]
                    #next
                    items = line2.split()
                    print(line)
                    print(items)
                    if len(items)>0:
                        st = 0
                        for item in items:
                            n = line.find(item,st)
                            x1 = CharData[i][n][1]
                            x2 = CharData[i][n+len(item)-1][2]
                            xm = (x1+x2)/2.0
                            itemsx.append(xm)
                            st = n + len(item)
                            if re.match("G\d+\w*",item):   # G1,G11,G2等がある場合はその中央のX座標を取得
                                nameCenter.append([item,xm])
                            #end if
                        #next
                        if len(nameCenter)>0:
                            memberN = len(nameCenter)   # 部材の数量
                        #end if

                        if "中央" in line  or "全断面" in line:
                            itemCenter = []
                            j = -1
                            for item in items:
                                j += 1
                                if item == "端部" or item == "中央" or item == "左端" or item == "右端" or item == "全断面" :
                                    itemCenter.append([item, itemsx[j]])
                                #end if
                            #next
                            continue
                        #end if

                        if "符号名"in line:
                            if len(断面サイズ)>0:
                                a=0
                                j = 0
                                for names in memberName:
                                    names2 = names.split(',')
                                    dic1 = {}
                                    # j += 1
                                    item = itemCenter[j][0]
                                    if item == "端部":
                                        kind = ["端部","中央"]
                                    elif item == "左端":
                                        kind = ["左端","中央","右端"]
                                    elif item == "全断面":
                                        kind = ["全断面"]
                                    #end if
                                    kn = len(kind)
                                    for k in range(kn):
                                        dic2 = {}
                                        dic2["断面サイズ"]= 断面サイズ[j+k]
                                        dic2["主筋上端"]= 主筋上端[j+k]
                                        dic2["主筋下端"]= 主筋下端[j+k]
                                        dic2["材料上端"]= 材料上端[j+k]
                                        dic2["材料下端"]= 材料下端[j+k]
                                        dic2["かぶり上端"]= かぶり上端[j+k]
                                        dic2["かぶり下端"]= かぶり下端[j+k]
                                        dic2["あばら筋"]= あばら筋[j+k]
                                        dic2["あばら筋材料"]= あばら筋材料[j+k]
                                        dic1[kind[k]] = dic2
                                    #next
                                    j += kn
                                    
                                    print(names2)
                                    for name in names2:
                                        if name in self.BeamMemberSpan.keys():
                                            dic0 = self.BeamMemberSpan[name]
                                            dic0["断面諸元"] = dic1
                                            dic0["断面種類"] = kind
                                            self.BeamMemberSpan[name] = dic0
                                        else:
                                            dic0 = {}
                                            dic0["断面諸元"] = dic1
                                            dic0["断面種類"] = kind
                                            self.BeamMemberSpan[name] = dic0
                                        #end if
                                    #next
                                #next
                            #end if

                            ucount = 0
                            scount = 0
                            断面サイズ = []
                            主筋上端 = []
                            主筋下端 = []
                            材料上端 = []
                            材料下端 = []
                            かぶり上端 = []
                            かぶり下端 = []
                            あばら筋 = []
                            あばら筋材料 = []
                            memberName = []
                            for item in items:
                                item2 = item.split()
                                flag = True
                                for item3 in item2:
                                    if re.match("RG\d+",item3) or re.match("\d+G\d+",item3):   # 梁の符号パターンに合う場合は配列に記録
                                        flag = flag and True
                                    else:
                                        flag = flag and False
                                    #end if
                                #next
                                if flag :
                                    memberName.append(item)
                                #end if
                            #next
                            continue
                        #end if

                        if "ｂ×Ｄ"in line:   # ｂ×Ｄ
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                断面サイズ.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if "上端"in line and ucount==0:
                            ucount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                主筋上端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if "下端"in line and scount==0:
                            scount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                主筋下端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if
                            
                        if "上端"in line and ucount==1:
                            ucount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                材料上端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if "下端"in line and scount==1:
                            scount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                材料下端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if
                        
                        if "上端"in line and ucount==2:
                            ucount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                かぶり上端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if "下端"in line and scount==2:
                            scount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                かぶり下端.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if ucount==3 and scount==3:
                            ucount += 1
                            scount += 1
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                あばら筋.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if

                        if "材料"in line and ucount==4 and scount==4:
                            n1 = len(itemCenter)
                            n2 = len(items)
                            if n2 > n1*2:
                                items2 = []
                                for j in range(0,n2-1,2):
                                    items2.append(items[j]+items[j+1])
                                #next
                            else:
                                items2 = items
                            #end if
                            n2 = len(items2)
                            for j in range(n1):
                                あばら筋材料.append(items2[n2-n1+j])
                            #next
                            continue
                        #end if
                        
                    #end if
                #next
                if len(断面サイズ)>0:
                    a=0
                    j = 0
                    for names in memberName:
                        names2 = names.split(',')
                        dic1 = {}
                        # j += 1
                        item = itemCenter[j][0]
                        if item == "端部":
                            kind = ["端部","中央"]
                        elif item == "左端":
                            kind = ["左端","中央","右端"]
                        elif item == "全断面":
                            kind = ["全断面"]
                        #end if
                        kn = len(kind)
                        for k in range(kn):
                            dic2 = {}
                            dic2["断面サイズ"]= 断面サイズ[j+k]
                            dic2["主筋上端"]= 主筋上端[j+k]
                            dic2["主筋下端"]= 主筋下端[j+k]
                            dic2["材料上端"]= 材料上端[j+k]
                            dic2["材料下端"]= 材料下端[j+k]
                            dic2["かぶり上端"]= かぶり上端[j+k]
                            dic2["かぶり下端"]= かぶり下端[j+k]
                            dic2["あばら筋"]= あばら筋[j+k]
                            dic2["あばら筋材料"]= あばら筋材料[j+k]
                            dic1[kind[k]] = dic2
                        #next
                        j += kn
                        
                        print(names2)
                        for name in names2:
                            if name in self.BeamMemberSpan.keys():
                                dic0 = self.BeamMemberSpan[name]
                                dic0["断面諸元"] = dic1
                                dic0["断面種類"] = kind
                                self.BeamMemberSpan[name] = dic0
                            else:
                                dic0 = {}
                                dic0["断面諸元"] = dic1
                                dic0["断面種類"] = kind
                                self.BeamMemberSpan[name] = dic0
                            #end if
                        #next
                    #next
                #end if

            #end if

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
                                    #end if

                                    if ln <=4 :
                                        xxx0 -= xd
                                        xxx1 += xd
                                    #end if
                                    width3 = xxx1 - xxx0
                                    height3 = yyy1 - yyy0
                                    ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                    flag = True
                                    pageFlag = True
                                    val = a
                                    print('val={:.2f}'.format(val))
                                #end if
                            #end if

                            # 数値を検索を開始するを文字数分移動
                            st = nn + ln + 1
                        #next
                    #end if
                #next
            #end if
                
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
                                        #end if
                                    #end if
                                    
                                    st = t3.find(w1,st)+ len(w1)
                                #next
                            #end if
                        #end if
                    #next
                #end if
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
                            #end if
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
                                                #end if
                                            #end if
                                            
                                            st = t3.find(w1,st)+ len(w1)
                                        #next
                                    #end if
                                #end if
                            #end if
                        #end if
                    #next
                #end if
            #end if


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
                                        #end if
                                    #end if

                                    # 数値を検索を開始するを文字数分移動
                                    st = t3.find(t5,st)+ len(t5)
                                    # st += ln
                                #next
                            #end if
                        #end if
                    #next
                #end if
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
                            #end if
                        if kmode :
                            CharLine = CharData[i] # １行文のデータを読み込む
                            t4 = ""
                        
                            for char in CharLine:
                                # kfwordより右側にある数値だけを検出する。
                                if char[1]>=zx0 :
                                    t4 += char[0]
                            #next
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
                                            #end if
                                        #end if
                                        st = t3.find(w1,st)+ len(w1)
                                    #next
                                #end if
                            #end if
                        #end if
                    #next
                #end if
            #end if
                                
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
                            #end if
                        #end if
                    #end if
                #end while
            #end if

        elif mode == "杭の検定表":
            pageFlag = False


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
                                #end if
                            #next
                            if t4 == "" :
                                kmode = False
                            #end if

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
                                            #end if
                                        #end if
                                        
                                        st = t3.find(w1,st)+ len(w1)
                                    #next
                                #end if
                            #end if
                        #end if
                    #next
            #end if
        #end if
        
        #==========================================================================
        #  検出結果を出力する
        return pageFlag, ResultData
    #end def
    #*********************************************************************************

    def OtherSheet(self, page, limit, interpreter, device,interpreter2, device2):
        
        #============================================================
        # 構造計算書が不明の場合の処理
        #============================================================
        pageFlag = False
        ResultData = []
        limit1 = limit
        limit2 = limit
        limit3 = limit
        interpreter.process_page(page)
        layout = device.get_result()
        #
        #   このページに「断面検定表」、「検定比図」の
        #   文字が含まれている場合のみ数値の検索を行う。
        #
        

        検定比_Flag = False

        xd = 3      #  X座標の左右に加える余白のサイズ（ポイント）を設定

        mode = ""
        for lt in layout:
            # LTTextContainerの場合だけ標準出力　断面算定表(杭基礎)
            if isinstance(lt, LTTextContainer):
                texts = lt.get_text()
                if "断面検定表"in texts or "検定比図" in texts :
                    検定比_Flag = True
                    break
            #end if
        #next

        if not 検定比_Flag  :     # 該当しない場合はこのページの処理は飛ばす。
            print("No Data")
            return False,[]
        # else:
        #     print(mode)
        #end if

        #=================================================================================================
        #   検定比図のチェック
        #=================================================================================================
        
        if 検定比_Flag  :

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
                                    #end if

                                    if ln <=4 :
                                        xxx0 -= xd
                                        xxx1 += xd
                                    #end if
                                    width3 = xxx1 - xxx0
                                    height3 = yyy1 - yyy0
                                    ResultData.append([a,[xxx0, yyy0, width3, height3],False])
                                    flag = True
                                    pageFlag = True
                                    val = a
                                    print('val={:.2f}'.format(val))
                                #end if
                            #end if

                            # 数値を検索を開始するを文字数分移動
                            st = nn + ln + 1
                        #next
                    #end if
                #next
            #end if
        # #end if
        
        #==========================================================================
        #  検出結果を出力する
        return pageFlag, ResultData
    #end def
    #*********************************************************************************


    #============================================================================
    #  プログラムのメインルーチン（外部から読み出す関数名）
    #============================================================================

    def CheckTool(self,filename, limit=0.95 ,stpage=0, edpage=0):
        global flag1, fname, dir1, dir2, dir3, dir4, dir5, folderName, paraFileName
        global ErrorFlag, ErrorMessage
        global kind, verion

        if filename =="" :
            return False
        #end if

        pdf_file = filename
        pdf_out_file = os.path.splitext(pdf_file)[0] + '[検出結果(閾値={:.2f}'.format(limit)+')].pdf'

        # PyPDF2のツールを使用してPDFのページ情報を読み取る。
        # PDFのページ数と各ページの用紙サイズを取得
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
            #end with
        except OSError as e:
            print(e)
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False, kind, version
        except:
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False, kind, version
        #end try
        
        #=============================================================
        if stpage <= 0 :      # 検索を開始する最初のページ
            startpage = 2
        elif stpage > PageMax:
            startpage = PageMax-1
        else:
            startpage = stpage
        #end if

        if edpage <= 0 :  # 検索を終了する最後のページ
            endpage = PageMax 
        elif edpage > PageMax:
            endpage = PageMax
        else:
            endpage = edpage
        #end if

        # PDFMinerのツールの準備
        resourceManager = PDFResourceManager()
        # PDFから単語を取得するためのデバイス
        device = PDFPageAggregator(resourceManager, laparams=LAParams())
        # PDFから１文字ずつを取得するためのデバイス
        device2 = PDFPageAggregator(resourceManager)

        pageResultData = []
        pageNo = []

        try:
            with open(pdf_file, 'rb') as fp:
                interpreter = PDFPageInterpreter(resourceManager, device)
                interpreter2 = PDFPageInterpreter(resourceManager, device2)
                pageI = 0
                        
                for page in PDFPage.get_pages(fp):
                    pageI += 1

                    ResultData = []
                    print("page={}:".format(pageI), end="")
                    if pageI == 1 :
                        pageFlag = True
                        kind, version = self.CoverCheck(page, interpreter2, device2)
                        print()
                        print("プログラムの名称：{}".format(kind))
                        print("プログラムのバーsジョン：{}".format(version))

                        with open("./kind.txt", 'w', encoding="utf-8") as fp2:
                            print(kind, file=fp2)
                            print(version, file=fp2)
                            fp2.close()

                    else:

                        if pageI < startpage:
                            print()
                            continue
                        #end if
                        if pageI > endpage:
                            break
                        #end if

                        if kind == "SuperBuild/SS7":
                            #============================================================
                            # 構造計算書がSS7の場合の処理
                            #============================================================

                            pageFlag, ResultData = self.SS7(page, limit, interpreter, device, interpreter2, device2)

                        # 他の種類の構造計算書を処理する場合はここに追加
                        # elif kind == "****":
                        #     pageFlag, ResultData = self.***(page, limit, interpreter, device, interpreter2, device2)

                        else:
                            #============================================================
                            # 構造計算書の種類が不明の場合はフォーマットを無視して数値のみを検出
                            #============================================================

                            pageFlag, ResultData = self.OtherSheet(page, limit, interpreter, device, interpreter2, device2)

                            # return False
                        #end if

                    if pageFlag : 
                        pageNo.append(pageI)
                        pageResultData.append(ResultData)
                    #end if
                #next

                fp.close()
            # end with

        except OSError as e:
            print(e)
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False
        except:
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False
        #end try


        # 使用したデバイスをクローズ
        device.close()
        device2.close()

        #============================================================================================
        #
        #   数値検出結果を用いて各ページに四角形を描画する
        #
        #============================================================================================
        
        try:
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
                    cc.drawString(20 * mm,  pageSizeY - 40 * mm, "検定比（{}以上）の検索結果".format(limit))

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
                        #end if
                    #next
                #end if

                # ページデータの確定
                cc.showPage()
            # next

            # PDFの保存
            cc.save()

            # time.sleep(1.0)
            # # すべての処理がエラーなく終了したのでTrueを返す。
            # return True

        except OSError as e:
            print(e)
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False
        except:
            logging.exception(sys.exc_info())#エラーをlog.txtに書き込む
            return False

        #end try

        # すべての処理がエラーなく終了したのでTrueを返す。
        return True

    #end def    
    #*********************************************************************************


#==================================================================================
#   このクラスを単独でテストする場合のメインルーチン
#==================================================================================

if __name__ == '__main__':
    
    time_sta = time.time()  # 開始時刻の記録

    CT = CheckTool()

    stpage = 2
    edpage = 200
    limit = 0.70
    filename = "サンプル計算書(1)床伏せ図.pdf"

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

    # stpage = 2
    # edpage = 0
    # limit = 0.70
    # filename = "サンプル計算書(3)抜粋.pdf"

    if CT.CheckTool(filename,limit=limit,stpage=stpage,edpage=edpage):
        print("OK")
    else:
        print("NG")
    

    t1 = time.time() - time_sta
    print("time = {} sec".format(t1))

#*********************************************************************************
