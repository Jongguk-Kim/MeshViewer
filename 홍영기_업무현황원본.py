from multiprocessing.sharedctypes import Value
from optparse import Option
from ssl import Options
import xlwings as xw
import pandas as pd 
import numpy as  np 

def main():
    # xw.Book("홍영기_업무현황원본.xlsm").set_mock_caller()
    lastLine = 100
    book = xw.Book("홍영기_업무현황원본.xlsm")
    sheet = book.sheets("업무현황")
    source = book.sheets("MES원본")

    sheet["B1"].font.color = (0, 0, 0)    
    sheet["B1"].value=" 시작 " 
    # for i in range(3, lastLine) : 
    #     if str(source["F%d"%(i)]) == "": break 
    #     if isinstance( source["A%d"%(i)].value, type(None)): break 
    #     m = 2; n = 5
    #     sheet.cells(i, m).value = source.cells(i,n).value # 품목코드
    #     sheet.cells(i, m+1).value = source.cells(i, 6).value # 주문코드
    #     sheet.cells(i, m+2).value = source.cells(i, 11).value 
    #     sheet.cells(i, m+3).value = source.cells(i, 9).value
    #     sheet.cells(i, m+4).value = source.cells(i, 12).value
    #     sheet.cells(i, m+5).value = source.cells(i, 4).value
    #     sheet.cells(i, m+6).value = source.cells(i, 10).value
    #     sheet.cells(i, m+7).value = source.cells(i, 17).value
    #     sheet.cells(i, m+8).value = source.cells(i, 30).value
    #     sheet.cells(i, m+9).value = source.cells(i, 21).value
    #     sheet.cells(i, m+10).value = source.cells(i, 13).value
    #     sheet.cells(i, m+11).value = source.cells(i, 14).value
    #     sheet.cells(i, m+12).value = source.cells(i, 16).value
    #     sheet.cells(i, m+13).value = source.cells(i, 15).value
    #     sheet.cells(i, m+14).value = source.cells(i, 8).value

    #     if "취소" in str(source.cells(i, 8).value): 
    #             sheet["C%d"%(i)].font.color = (0, 125, 125) # = 48 ## gray 

    # sheet["B1"].value=" 끝 " 
    # sheet["B1"].font.color = (0, 255, 0)

    source_data = source.range("A2:AO60000").options(pd.DataFrame, index=False, header=1, expand='table').value

    new_df = source_data[["품목코드"
                        , "주문코드"
                        , "납품처명"
                        , "제작구분"
                        ,  "제품구분"
                        , "주문일자"
                        , "고객요청납기일"
                        , "납품예정일"
                        , "인지"
                        , "사이즈"
                        , "패턴"
                        , "수량"
                        , "MOLD NO"
                        , "설계자" 
                        ]
                                            ]
    # new_df = pd.DataFrame() ## 빈 dataframe
    # new_df = pd.DataFrame(source_data, columns=["품목코드"
    #                                           , "주문코드"
    #                                           , "납품처명"
    #                                           , "제작구분"
    #                                           ,  "제품구분"
    #                                           , "주문일자"
    #                                           , "고객요청납기일"
    #                                           , "납품예정일"
    #                                           , "인지"
    #                                           , "사이즈"
    #                                           , "패턴"
    #                                           , "수량"
    #                                           , "MOLD NO"
    #                                           , "설계자" 
    #                                           ])


    # dsource["품목코드"] = source_data["주문코드"]
    # fp=open("Q:\\다운로드\\source.csv", 'w')
    # fp.writelines(str(source_data["설계자"]))
    # fp.writelines(str(dsource["품목코드"]))
    print("*****************************")
    source_data.to_excel("E:\\MES원본.xlsx", sheet_name="MES원본")
    source_data.to_excel("E:\\업무현황.xlsx", sheet_name="업무현황")
    # fp.write(source_data.to_string())
    # fp.close()
    # print(source_data)

if __name__ == "__main__":
    # xw.Book("Q:\다운로드\홍영기) 업무현황 원본.xlsm").set_mock_caller()
    main()