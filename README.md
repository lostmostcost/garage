# Naver Garage (네이버 부동산 크롤러)

이 프로젝트는 네이버 부동산의 데이터를 수집하기 위한 웹 스크래퍼입니다. 팀 프로젝트를 진행할 작업실을 탐색하기 위해 개발되었습니다.

조건에 맞는 부동산 데이터를 수집하고 분석, 시각화합니다.

## 시작하기

이 지침은 개발 및 테스트를 목적으로 로컬 기기에서 프로젝트의 사본을 실행하는 데 필요한 정보를 제공합니다.

### 사전 요구 사항

- Python 3.7 이상
- Jupyter Notebook

### 설치하기

1. 저장소를 복제합니다.
2. 필요한 Python 패키지를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```

### 사용하기
- main.ipynb

    1. 첫번째 셀에서 수집 정보의 조건을 설정합니다.

        ```Python
        # 네이버 부동산 크롤러 객체 생성
        from modules import NaverRealEstate, set_conditon_params

        # 검색할 지역의 리스트를 입력합니다.
        locations = ['마포구', '서대문구', '용산구', '중구', '종로구', '성동구', '동대문구', 
                    '광진구', '송파구', '강남구', '서초구', '동작구', '관악구', '구로구', '영등포구']

        real_estate_objects = {}

        for location in locations:
            real_estate_objects[location] = NaverRealEstate(location=f"서울시 {location}")

        # 검색 조건 설정 (wprcRange: 보증금 범위
        #              population: 팀 인원
        #              spc_per_person: 1인당 평수
        #              fee_per_person: 1인당 최대 회비,
        #              rletTpCd: 원룸-OR 사무실-SMS 상가-SG 오피스텔-OPST
        #              tradTpcd: 매매-A1 전세-B1 월세-B2 단기임대-B3)
        params = set_conditon_params(wprcRange=(1, 2000), population=3, spc_per_person=3, fee_per_person=15, rletTpCd="OR:SG:SMS", tradTpCd="B2:B3")
        ```
    
    <br>
    2. 두번째 셀을 실행하여 데이터를 크롤링 합니다.
    
    (크롤링 이후에는 엑셀로 저장된 데이터를 불러와 사용할 수 있습니다.)

    <br>
    3. 필요한 데이터 처리 및 시각화를 순차적으로 실행합니다. 