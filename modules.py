import os
import time
import json
import math
import random
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from functools import wraps

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36",
    # Add more user agents as needed
    ]

def im_not_a_robot(sleep_interval=50):
    def decorator(func):
        call_count = 0
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_count
            headers = kwargs.get('headers', {})
            call_count += 1
            time.sleep(random.uniform(1, 2))
            global user_agent
            user_agent = random.choice(USER_AGENTS)
            headers['User-Agent'] = user_agent
            kwargs['headers'] = headers
            
            if call_count % sleep_interval == 0:
                print(f"요청 횟 수 : {call_count} | Sleeping for 10 ~ 15 seconds...")
                time.sleep(random.uniform(10, 15))
                
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry_on_failure(max_retries=30, retry_status_code=307):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                response = func(*args, **kwargs)
                if response.status_code == retry_status_code:
                    print(f"status code : {retry_status_code} | User-Agent : {user_agent} | 재시도 중...")
                    retries += 1
                else:
                    return response
            raise Exception(f"최대 재시도 횟 수({max_retries})를 초과하여 종료합니다.")
        return wrapper
    return decorator

@im_not_a_robot()
@retry_on_failure()
def get_request(*args, **kwargs):
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    headers = kwargs['headers']
    response = requests.get(*args, **kwargs)
    response.raise_for_status()
    return response

def generate_query_url(url, params):
    if not url.endswith('?'):
        url += '?'
    query_params = '&'.join([f"{key}={value}" for key, value in params.items() if value])
    return f"{url}{query_params}"

def set_conditon_params(wprcRange:tuple, population:int, spc_per_person, fee_per_person, rletTpCd="OR:SG:SMS", tradTpCd="B2:B3"):
    params = {
        'wprcMin': wprcRange[0],
        'wprcMax': wprcRange[1],
        'rprcMin': None,
        'rprcMax': population * fee_per_person,
        'spcMin': population * spc_per_person * 3.3,
        'spcMax': None,
        'rletTpCd': rletTpCd,
        'tradTpCd': tradTpCd,
    }
    return params

class NaverRealEstate:
    def __init__(self, location):
        self.location = location
        self.df = df = pd.DataFrame(columns=[
            '상품번호', '매물유형', '거래방식', '가격', '보증금', '월세',
            '계약면적', '전용면적', '층 수', '위도', '경도', '태그', '부동산'])

    def load_from_excel(self, folder) -> None :
        data_dir = os.path.join(os.getcwd(), f'data/{folder}')
        excel_files = [file for file in os.listdir(data_dir) if file.endswith('.xlsx') and self.location in file]
        if excel_files:
            excel_file = os.path.join(data_dir, excel_files[0])  # 하나의 파일만 가져옵니다.
            df = pd.read_excel(excel_file)
            print(f"저장된 {folder}/{excel_file} 를 불러왔습니다.")
        else:
            print("저장된 파일이 없습니다. crawl_data로 새로운 데이터를 가져오세요.")
        self.df = df

    def crawl_data(self, params : dict):
        
        # 지역 매개변수 가져오기
        url1 = f"https://m.land.naver.com/search/result/{self.location}"
        res1 = get_request(url=url1)
        print(f"status code : {res1.status_code} | {self.location} 지역의 매개변수를 가져왔습니다.")
        soup1 = (str)(BeautifulSoup(res1.text, 'lxml'))

        # 지역 매개변수 구성하기
        value1 = soup1.split("filter: {")[1].split("}")[0].replace(" ","").replace("'","")
        params1 = params.copy()
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

        # clusterList 가져오기
        base_url2 = "https://m.land.naver.com/cluster/clusterList?"
        query_url2 = generate_query_url(url=base_url2, params=params1)
        res2 = get_request(url=query_url2)
        print(f"status code : {res2.status_code} | clusterList를 가져왔습니다.")
        json_str2 = json.loads(json.dumps(res2.json()))

        # 검색 조건 설정하기2 
        values2 = json_str2['data']['ARTICLE']
        params2 = params.copy()
        params2['cortarNo'] = params1['cortarNo']

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
                print(f"status code : {res3.status_code} | {params2['itemId']} 데이터를 가져왔습니다.")
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
                        }
                
                print(f"수집한 데이터 : {len(self.df)}")

    def save_to_excel(self, folder=None):
        if folder == None:
            today = datetime.today()
            folder = today.strftime("%y%m%d")
        self.df.to_excel(f'data/{folder}/{self.location}.xlsx', index=False)

    def save_to_excel(self, folder=None):
        if folder is None:
            today = datetime.today()
            folder = today.strftime("%y%m%d")
        folder_path = f'data/{folder}'
        os.makedirs(folder_path, exist_ok=True)

        file_path = f'{folder_path}/{self.location}.xlsx'
        self.df.to_excel(file_path, index=False)
        print(f"{len(self.df)}개의 매물이 {file_path}에 저장되었습니다.")

    def drop_df_duplicates(self) :
        df_copy = self.df.copy()
        df_copy['층 수'] = df_copy['층 수'].str.split('/').str.get(0)
        df_copy.drop_duplicates(subset=['위도', '경도', '층 수', '가격', '월세', '전용면적', '거래방식'], keep='first', inplace=True)
        df_copy['층 수'] = self.df['층 수']

        self.df = df_copy