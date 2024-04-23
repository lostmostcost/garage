import os
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import json
import math
from datetime import datetime
from functions import generate_query_url, get_request

class NaverRealEstate:
    def __init__(self, location):
        self.location = location
        self.df = self.load_excel()

    def load_excel(self):
        data_dir = os.path.join(os.getcwd(), 'data')
        excel_files = [file for file in os.listdir(data_dir) if file.endswith('.xlsx') and self.location in file]
        if excel_files:
            excel_file = os.path.join(data_dir, excel_files[0])  # Assume only one file found
            df = pd.read_excel(excel_file)
            #print(f"저장된 {excel_file} 를 불러왔습니다.")
        else:
            df = pd.DataFrame(columns=[
                '상품번호',
                '매물유형',
                '거래방식',
                '가격',
                '보증금',
                '월세',
                '계약면적',
                '전용면적',
                '층 수',
                '위도',
                '경도',
                '태그',
                '부동산',
                '상세정보'
            ])
            print("저장된 파일이 없습니다. crawl_data로 새로운 데이터를 가져오세요.")
        return df

    def crawl_data(self, wprcMin=None, wprcMax=None, rprcMin=None, rprcMax=None, rletTpCd="OR:SG:SMS", tradTpCd="B2:B3"):
        
        # 지역 매개변수 가져오기
        url1 = f"https://m.land.naver.com/search/result/{self.location}"
        res1 = get_request(url=url1)
        res1.raise_for_status()
        soup1 = (str)(BeautifulSoup(res1.text, 'lxml'))

        # 지역 매개변수 구성하기
        value1 = soup1.split("filter: {")[1].split("}")[0].replace(" ","").replace("'","")
        params1 = {}
        params1['view'] = 'atcl'
        params1['cortarNo'] = value1.split("cortarNo:")[1].split(",")[0]
        params1['lat'] = value1.split("lat:")[1].split(",")[0]
        params1['lon'] = value1.split("lon:")[1].split(",")[0]
        params1['z'] = value1.split("z:")[1].split(",")[0]

        # 지도 크기 설정하기
        lat_margin = 0.118
        lon_margin = 0.111

        params1['btm']=float(params1['lat'])-lat_margin
        params1['lft']=float(params1['lon'])-lon_margin
        params1['top']=float(params1['lat'])+lat_margin
        params1['rgt']=float(params1['lon'])+lon_margin

        # 검색 조건 설정하기1
        params1['rletTpCd'] = rletTpCd # 매물 유형
        params1['tradTpCd'] = tradTpCd # 거래 유형
        params1['wprcMin'] = wprcMin # 보증금
        params1['wprcMax'] = wprcMax 
        params1['rprcMin'] = rprcMin # 월세
        params1['rprcMax'] = rprcMax

        # 그룹 매개변수 가져오기
        base_url2 = "https://m.land.naver.com/cluster/clusterList?"
        query_url2 = generate_query_url(url=base_url2, params=params1)
        res2 = get_request(url=query_url2)
        json_str2 = json.loads(json.dumps(res2.json()))

        # 검색 조건 설정하기2 
        values2 = json_str2['data']['ARTICLE']
        params2 = {}
        params2['cortarNo'] = params1['cortarNo']
        params2['rletTpCd'] = params1['rletTpCd']
        params2['tradTpCd'] = params1['tradTpCd']
        params2['wprcMin'] = params1['wprcMin']
        params2['wprcMax'] = params1['wprcMax']
        params2['rprcMin'] = params1['rprcMin']
        params2['rprcMax'] = params1['rprcMax']

        # 페이지 별 부동산 데이터 가져오기
        for v in values2 :
            params2['itemId'] = v['lgeo']
            params2['lgeo'] = v['lgeo']
            params2['totCnt'] = v['count']
            params2['z'] = v['z']
            params2['lat'] = v['lat']
            params2['lon'] = v['lon']

            len_pages = int(params2['totCnt']) / 20 + 1
            for idx in  range(1, math.ceil(len_pages)):
                params2['page'] = idx
                base_url3 = "https://m.land.naver.com/cluster/ajax/articleList?"
                query_url3 = generate_query_url(url=base_url3, params=params2)
                res3 = get_request(url=query_url3)
                json_str3 = json.loads(json.dumps(res3.json()))
                values3 = json_str3['body']

                # DataFrame 객체로 변환
                for v in values3 :
                    self.df.loc[len(self.df)] = {
                        '상품번호': v.get('atclNo'),
                        '매물유형': v.get('rletTpNm'),
                        '거래방식': v.get('tradTpNm'),
                        '가격': v.get('prc', 0),
                        '보증금': int(v.get('hanPrc', '0').replace(',', '')),
                        '월세': v.get('rentPrc', 0),
                        '계약면적': float(v.get('spc1', np.nan) if v.get('spc1', np.nan) != '-' else np.nan),
                        '전용면적': float(v.get('spc2', np.nan) if v.get('spc2', np.nan) != '-' else np.nan),
                        '층 수': v.get('flrInfo', None),
                        '위도' : v.get('lat', None),
                        '경도' : v.get('lng', None),
                        '태그': v.get('tagList', None),
                        '부동산': v.get('rltrNm', None),
                        '상세정보': f"https://m.land.naver.com/article/info/{v.get('atclNo')}"
                        }
                
                print(f"수집한 데이터 : {len(self.df)}")

        # 엑셀 파일로 저장
        today = datetime.today()
        formatted_date = today.strftime("%y%m%d")
        self.df.to_excel(f'data/{self.location}_{formatted_date}.xlsx', index=False)

    def drop_duplicates(self) :
        df = self.df
        df.drop_duplicates(subset=['위도', '경도', '층 수', '가격', '거래방식'], keep='first', inplace=True)

    def filter_rows_above_areaMin(self, areaMin):
        filtered_df = self.df[self.df['전용면적'] >= areaMin]
        self.df = filtered_df