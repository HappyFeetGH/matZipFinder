# app.py
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import numpy as np

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
        'query': keyword,
        'x': lng, 'y': lat,
        'radius': int(radius_km * 1000),
        'size': 15,
        'sort': 'accuracy'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    return []

def process_restaurants(restaurants, bayes_prior, min_reviews):
    """모든 식당의 베이즈 통계를 계산 (필터링 없이)"""
    processed_list = []
    for rest in restaurants:
        # 임시 평점/리뷰 생성 (실제 데이터는 별도 API나 크롤링 필요)
        avg_rating = np.random.uniform(3.5, 5.0)
        review_count = np.random.randint(10, 500)
        ratings = np.random.normal(avg_rating, 0.5, review_count)
        
        bayes_avg = (avg_rating * review_count + bayes_prior * min_reviews) / (review_count + min_reviews)
        std_dev = np.std(ratings)

        processed_list.append({
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
    # KAKAO_JS_KEY를 .env에서 읽어와 템플릿에 전달
    kakao_js_key = os.getenv('KAKAO_JS_KEY')
    return render_template('index.html', kakao_js_key=kakao_js_key)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    address = data.get('address')
    radius = float(data.get('radius', 5))
    min_reviews = int(data.get('min_reviews', 50))
    bayes_prior = float(data.get('bayes_prior', 3.5))
    
    lng, lat = get_coordinates(address)
    if not lng:
        return jsonify({'error': '주소 변환에 실패했습니다.'}), 400

    keywords = ['한식', '일식', '중식', '양식', '카페']
    all_results = {}

    for keyword in keywords:
        places = search_places(lng, lat, keyword, radius)
        if places:
            processed = process_restaurants(places, bayes_prior, min_reviews)
            all_results[keyword] = processed
            
    return jsonify({
        'results': all_results,
        'center': {'lat': lat, 'lng': lng}
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

