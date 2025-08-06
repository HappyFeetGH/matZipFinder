from dotenv import load_dotenv
import os
import requests
import numpy as np
import json

load_dotenv()
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')
if not KAKAO_API_KEY:
    print("오류: .env에 KAKAO_API_KEY를 설정하세요.")
    exit(1)

def get_coordinates(address):
    """주소 → 좌표 변환 (Kakao Local API)"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {'query': address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['documents']:
            return float(data['documents'][0]['x']), float(data['documents'][0]['y'])
    print("주소 변환 실패.")
    return None, None

def search_restaurants(lng, lat, radius_km=5, keyword='식당'):
    """반경 내 식당 검색 (Kakao Place API)"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {
        'query': keyword,
        'x': lng, 'y': lat,
        'radius': int(radius_km * 1000),
        'size': 15,  # 최대 15개로 수정 (Kakao API 제한)
        'sort': 'accuracy'  # 정확도 우선
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    print(f"검색 실패. 응답 코드: {response.status_code}")
    print(f"응답 메시지: {response.text}")  # 디버깅용 추가
    return []


def model_tasty_restaurants(restaurants, min_reviews=50, bayes_prior=3.5, min_bayes_score=4.0):
    tasty_list = []
    for rest in restaurants:
        name = rest.get('place_name', 'Unknown')
        category = rest.get('category_group_name', '기타')  # 카테고리 추가
        address = rest.get('address_name', '주소 없음')    # 주소 추가
        phone = rest.get('phone', '전화번호 없음')         # 전화번호 추가
        distance = rest.get('distance', 0)                 # 거리 추가 (미터)

        # 임시 평점/리뷰 (실제 Kakao 평점으로 대체 가능)
        import numpy as np
        avg_rating = np.random.uniform(3.5, 5.0)
        review_count = np.random.randint(10, 500)
        ratings = np.random.normal(avg_rating, 0.5, review_count)

        bayes_avg = (avg_rating * review_count + bayes_prior * min_reviews) / (review_count + min_reviews)
        std_dev = np.std(ratings)

        if review_count >= min_reviews and bayes_avg >= min_bayes_score and std_dev < 0.5:
            tasty_list.append({
                'name': name,
                'category': category,      # 필터링용
                'address': address,
                'phone': phone,
                'distance': distance,      # 가까운 순 정렬용
                'bayes_avg': round(bayes_avg, 2),
                'review_count': review_count,
                'std_dev': round(std_dev, 2)
            })
    return tasty_list


# 메인 실행
if __name__ == "__main__":
    print("== 맛집 검색 알파 버전 (상세 주소 지원) ==")
    print("팁: 정확한 검색을 위해 상세 주소를 입력하세요.")
    #address = input("주소 입력 (예: 전북특별자치도 전주시 완산구 홍산중앙로 37): ")
    address = "전북 전주시 완산구 모악로 4758"
    lng, lat = get_coordinates(address)
    if not lng or not lat:
        exit(1)
    
    radius_input = input("반경 (km, 기본 5): ")
    radius = float(radius_input) if radius_input.strip() else 5.0
    
    print(f"좌표: {lng}, {lat} | 반경: {radius}km")
    #restaurants = search_restaurants(lng, lat, radius)
    restaurants = search_restaurants(lng, lat, radius, "한식")
    print(f"검색된 식당 수: {len(restaurants)}")
    if not restaurants:
        print("식당 없음.")
        exit(0)
    
    results = model_tasty_restaurants(restaurants)
    if results:
        print("\n추천 맛집:")
        for r in results:
            print(f"- {r['name']} | 베이즈 평균: {r['bayes_avg']} | 리뷰: {r['review_count']} | 분산: {r['std_dev']}")
        with open('tasty_restaurants.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("결과를 tasty_restaurants.json 파일에 저장했습니다.")
    else:
        print("조건 맞는 맛집 없음.")
