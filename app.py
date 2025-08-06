# app.py
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import numpy as np
from collections import OrderedDict

# .env 파일 로드
load_dotenv()
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')

app = Flask(__name__)

def get_coordinates(address):
    """주소 -> 좌표 변환 (Kakao Local API)"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {'query': address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200 and response.json()['documents']:
        doc = response.json()['documents'][0]
        return float(doc['x']), float(doc['y'])
    return None, None

def search_places(lng, lat, keyword, radius_km):
    """키워드로 장소 검색 (Kakao Place API)"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {'Authorization': f'KakaoAK {KAKAO_API_KEY}'}
    params = {
        'query': keyword, 'x': lng, 'y': lat,
        'radius': int(radius_km * 1000),
        'size': 15, 'sort': 'accuracy'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    return []

def process_restaurants(restaurants, bayes_prior, min_reviews):
    """식당 리스트의 베이즈 통계를 계산 (필터링 없음)"""
    processed_list = []
    
    # 이 함수에서 사용할 평점/리뷰 수를 미리 생성
    # (실제 데이터가 있다면 이 부분을 대체)
    simulated_data = {}
    for rest in restaurants:
        place_id = rest.get('id')
        simulated_data[place_id] = {
            'avg_rating': np.random.uniform(3.5, 5.0),
            'review_count': np.random.randint(10, 500)
        }

    for rest in restaurants:
        place_id = rest.get('id')
        avg_rating = simulated_data[place_id]['avg_rating']
        review_count = simulated_data[place_id]['review_count']
        
        # 베이즈 평균 계산
        bayes_avg = (avg_rating * review_count + bayes_prior * min_reviews) / (review_count + min_reviews)
        
        # 분산 계산을 위한 가상 평점 분포 생성
        ratings = np.random.normal(avg_rating, 0.5, review_count)
        std_dev = np.std(ratings)

        processed_list.append({
            'id': place_id,
            'name': rest.get('place_name'),
            'phone': rest.get('phone') or '정보 없음',
            'lat': float(rest.get('y')),
            'lng': float(rest.get('x')),
            'bayes_avg': round(bayes_avg, 2),
            'review_count': review_count,
            'std_dev': round(std_dev, 2)
        })
    # 베이즈 평균이 높은 순으로 정렬
    processed_list.sort(key=lambda x: x['bayes_avg'], reverse=True)
    return processed_list

@app.route('/')
def index():
    kakao_js_key = os.getenv('KAKAO_JS_KEY')
    return render_template('index.html', kakao_js_key=kakao_js_key)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    address = data.get('address')
    radius = float(data.get('radius', 5))
    min_reviews = int(data.get('min_reviews', 50))
    fixed_bayes_prior = float(data.get('bayes_prior', 3.5))
    
    lng, lat = get_coordinates(address)
    if not lng:
        return jsonify({'error': '주소 변환에 실패했습니다.'}), 400

    keywords = ['한식', '일식', '중식', '양식', '카페']
    categorized_results = {}
    
    # 1. 하이브리드 bayes_prior 모델 구현
    for keyword in keywords:
        places = search_places(lng, lat, keyword, radius)
        
        # 검색된 식당이 10개 미만이면 고정 prior, 10개 이상이면 동적 prior 사용
        if len(places) < 10:
            current_prior = fixed_bayes_prior
        else:
            # 동적 prior 계산을 위해 임시 평균 평점 계산 (실제 평점 데이터가 없으므로 시뮬레이션)
            temp_ratings = [np.random.uniform(3.5, 5.0) for _ in places]
            current_prior = np.mean(temp_ratings)

        if places:
            processed = process_restaurants(places, current_prior, min_reviews)
            categorized_results[keyword] = processed
    
    # 2. '전체' 카테고리 추가
    unique_restaurants = {}
    for category_list in categorized_results.values():
        for restaurant in category_list:
            # 식당 ID를 키로 사용하여 중복 제거
            unique_restaurants[restaurant['id']] = restaurant
            
    # 전체 리스트를 베이즈 평균으로 정렬
    overall_list = sorted(list(unique_restaurants.values()), key=lambda x: x['bayes_avg'], reverse=True)

    # 최종 결과를 순서대로 담기 ('전체'가 맨 앞에 오도록)
    final_results = OrderedDict()
    if overall_list:
        final_results['전체'] = overall_list
    
    # 나머지 카테고리 추가
    for keyword in keywords:
        if keyword in categorized_results:
            final_results[keyword] = categorized_results[keyword]
            
    return jsonify({
        'results': final_results,
        'center': {'lat': lat, 'lng': lng}
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

