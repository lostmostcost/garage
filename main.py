from modules import NaverRealEstate
import pandas as pd

def set_conditions(min_unit_area, population, max_fee) :
    areaMin = min_unit_area * population * 3.3
    rprcMax = max_fee * population
    return {'areaMin' : areaMin,
            'rprcMax' : rprcMax}

conditions = set_conditions(min_unit_area=2.5, population=3, max_fee=15)

locations = ['마포구', '서대문구', '용산구', '중구', '성동구', '동대문구', '광진구',
             '송파구', '강남구', '서초구', '동작구', '관악구', '구로구', '영등포구']

real_estate_objects = {}

for location in locations:
    real_estate_objects[location] = NaverRealEstate(location=f"서울시 {location}")

real_estate_data = {}

for location, obj in real_estate_objects.items():
    #obj.crawl_data(wprcMin=None, wprcMax=2000, rprcMin=None, rprcMax=conditions['rprcMax'], rletTpCd="OR:SG:SMS", tradTpCd="B2:B3")
    obj.drop_duplicates()
    obj.filter_rows_above_areaMin(conditions['areaMin'])
    real_estate_data[location] = obj.df