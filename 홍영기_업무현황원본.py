# from datetime import datetime
# from multiprocessing.sharedctypes import Value
# from optparse import Option
# from ssl import Options
import xlwings as xw
try: import pandas as pd 
except: 
    import os 
    os.system("pip install pandas")
    import pandas as pd 

def main():
    # xw.Book("홍영기_업무현황원본.xlsm").set_mock_caller()
    lastLine = 100
    book = xw.Book("홍영기_업무현황원본.xlsm")
    sheet = book.sheets("업무현황")
    source = book.sheets("MES원본")

    sheet["B1"].font.color = (0, 0, 0)    
    sheet["B1"].value=" 시작 " 
    source_data = source.range("A2:AO60000").options(pd.DataFrame, index=False, header=1, expand='table').value

    df = source_data[["품목코드"
                        , "주문코드"
                        , "납품처명"
                        , "제작구분"
                        ,  "제품구분"
                        , "주문일자"
                        , "고객요청납기일"
                        , "납품예정일"
                        , "고객 검수일"
                        , "인지"
                        , "사이즈"
                        , "패턴"
                        , "수량"
                        , "MOLD NO"
                        , "설계자" 
                        ]
                       ]
    # fp=open("Q:\\다운로드\\source.txt", 'w', encoding="utf-8")
    cancel =[]
    for i in range(len(df["설계자"])): 
        # fp.writelines("'%s'\n"%df.loc[i]["설계자"])
        if "취소" in str(df.loc[i]["설계자"]): 
            cancel.append("취소")
        elif "세영" in str(df.loc[i]["설계자"]): 
            cancel.append("세영")
        elif "원경" in str(df.loc[i]["설계자"]): 
            cancel.append("원경")
        elif "신우" in str(df.loc[i]["설계자"]): 
            cancel.append("신우")
        elif "청운" in str(df.loc[i]["설계자"]): 
            cancel.append("청운")
        elif "대광" in str(df.loc[i]["설계자"]): 
            cancel.append("대광")
        elif "혜원" in str(df.loc[i]["설계자"]): 
            cancel.append("혜원")
        elif "태진" in str(df.loc[i]["설계자"]): 
            cancel.append("태진")
        elif "번영" in str(df.loc[i]["설계자"]): 
            cancel.append("번영")
        else: 
            cancel.append("")
        # sheet["B1"].value=i+3 
        # sheet.range("A%d"%(i+3)).value = cancel[-1]
        # if i < 20: 
        # sheet.range("G%d"%(i+3)).value=df.loc[i]["주문일자"]
        # sheet.range("H%d"%(i+3)).value=df.loc[i]["고객요청납기일"]
        # sheet.range("I%d"%(i+3)).value=df.loc[i]["납품예정일"]
        # sheet.range("J%d"%(i+3)).value=df.loc[i]["고객 검수일"]

    cdf = pd.DataFrame(cancel, columns=["판정"])
    # sheet.range("A2:A%d"%(len(df)+3)).options(index=False, header=True).value = df["품목코드"]
    
    sheet.range("A2:A%d"%(len(df)+3)).options(index=False, header=True).value = cdf["판정"]
    sheet.range("B2:B%d"%(len(df)+3)).options(index=False, header=True).value = df["품목코드"]
    sheet.range("C2:C%d"%(len(df)+3)).options(index=False, header=True).value = df["주문코드"]
    sheet.range("D2:D%d"%(len(df)+3)).options(index=False, header=True).value = df["납품처명"]
    sheet.range("E2:E%d"%(len(df)+3)).options(index=False, header=True).value = df["제작구분"]
    sheet.range("F2:F%d"%(len(df)+3)).options(index=False, header=True).value = df["제품구분"]

    sheet.range("G2:G%d"%(len(df)+3)).options(index=False, header=True).value = df["주문일자"].dt.strftime("%m/%d/%Y")
    sheet.range("H2:H%d"%(len(df)+3)).options(index=False, header=True).value = df["고객요청납기일"].dt.strftime("%m/%d/%Y")
    sheet.range("I2:I%d"%(len(df)+3)).options(index=False, header=True).value = df["납품예정일"].dt.strftime("%m/%d/%Y")
    sheet.range("J2:J%d"%(len(df)+3)).options(index=False, header=True).value = df["고객 검수일"]#.dt.strftime("%m/%d/%Y")
    
    sheet.range("K2:K%d"%(len(df)+3)).options(index=False, header=True).value = df["인지"]
    sheet.range("L2:L%d"%(len(df)+3)).options(index=False, header=True).value = df["사이즈"]
    sheet.range("M2:M%d"%(len(df)+3)).options(index=False, header=True).value = df["패턴"]
    sheet.range("N2:N%d"%(len(df)+3)).options(index=False, header=True).value = df["수량"]
    sheet.range("O2:O%d"%(len(df)+3)).options(index=False, header=True).value = df["MOLD NO"]
    sheet.range("P2:P%d"%(len(df)+3)).options(index=False, header=True).value = df["설계자"]
    from xlwings.utils import rgb_to_int
    for i, cn in enumerate(cancel):
        if "취소" in cn:
            sheet.range("C1").value=i+3 
            try: 
                sheet.range("B%d:P%d"%(i+3, i+3)).font.color =  rgb_to_int((0, 255,0))
            except Exception as EX: 
                sheet.range("D1").value=str(EX)
                # exit()

    # for i, cn in enumerate(cancel):
    #     if i < 225: 
    #         sheet.range("c%d"%(i+3)).font.color = (i+1, 0, 0)
    #         sheet.range("d%d"%(i+3)).font.color = (0, i+1, 0)
    #         # sheet.range("e%d"%(i+3)).font.color = (0, 0, i+1)
    #     else: break 



    # sheet["B1"].value="끝" 
    # for i in range(len(df)): 
    #     fp.writelines("%d,'%s'\n"%(i+3,cancel[i])) 
    # fp.close()
    # print("*****************************")
    # source_data.to_excel("Q:\\다운로드\\MES원본.xlsx", sheet_name="MES원본")
    # source_data.to_excel("Q:\\다운로드\\업무현황.xlsx", sheet_name="업무현황")

if __name__ == "__main__":
    # xw.Book("Q:\다운로드\홍영기) 업무현황 원본.xlsm").set_mock_caller()
    main()