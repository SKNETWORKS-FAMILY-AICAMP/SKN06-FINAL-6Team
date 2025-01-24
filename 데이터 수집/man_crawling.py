import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def food_info(page):
    '''
    모든 요리 이름에 대한 정보를 크롤링합니다.
    '''
    base_url = "https://www.10000recipe.com"
    search_url = f"{base_url}/recipe/list.html"

    while True:
        # 각 페이지를 순차적으로 크롤링
        page_url = f"{search_url}?order=reco&page={page}"
        print(f"크롤링 중: {page_url}")
        response = requests.get(page_url, verify=False)

        if response.status_code != 200:
            print(f"HTTP 응답 오류: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        # 레시피 링크 추출
        recipe_links = [link.get('href') for link in soup.find_all('a', class_='common_sp_link')]
        if not recipe_links:
            print(f"페이지 {page}에서 레시피를 찾을 수 없습니다.")
            break

        print(f"페이지 {page}에서 {len(recipe_links)}개의 레시피 링크를 찾았습니다.")

        page_recipes = []

        # 각 레시피 링크에 대해 크롤링을 실행
        for recipe_url in recipe_links:
            full_url = base_url + recipe_url
            recipe_info = get_recipe_info(full_url)
            if recipe_info:
                page_recipes.append(recipe_info)

        # 페이지 크롤링이 끝난 후, 모든 레시피를 DB에 저장
        save_page_to_db(page_recipes)

        # 다음 페이지로 이동
        page += 1
        if page == 3001:
            break
        time.sleep(2)  # 과도한 부하 방지를 위해 대기

def get_recipe_info(url):
    '''
    주어진 URL에서 레시피 정보를 가져옵니다.
    '''
    print(f"레시피 크롤링 중: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"레시피를 가져오는 데 실패했습니다: {url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # 요리 이름 추출
    recipe_name_element = soup.find('div', class_='view2_summary')
    recipe_name = recipe_name_element.find('h3').get_text(strip=True) if recipe_name_element else "이름 정보를 찾을 수 없음"

    # 요리 소개 추출
    intro_element = soup.find('div', class_='view2_summary_in')
    intro = intro_element.get_text(strip=True) if intro_element else "소개 정보를 찾을 수 없음"

    # 요리 정보 추출
    info_element = soup.find('div', class_='view2_summary_info')
    info = info_element.get_text(strip=True) if info_element else "정보를 찾을 수 없음"

    # 요리 사진 추출
    photo_element = soup.find('div', class_='centeredcrop')
    photo = photo_element.find('img')['src'] if photo_element else "사진 URL을 찾을 수 없음"

    # 요리 재료 추출
    ingredients_element = soup.find('div', class_='ready_ingre3')
    ingredients = ingredients_element.get_text(separator=', ', strip=True) if ingredients_element else "재료 정보를 찾을 수 없음"

    # 조리 방법 추출
    steps_element = soup.find_all('div', class_='view_step_cont')
    steps = [step.get_text(strip=True) for step in steps_element] if steps_element else ["레시피 정보를 찾을 수 없음"]

    return {
        'name': recipe_name,
        'intro': intro,
        'info': info,
        'photo': photo,
        'ingredients': ingredients,
        'recipe': steps
    }

def save_page_to_db(recipes):
    '''
    페이지의 모든 레시피 정보를 SQLite 데이터베이스에 저장합니다.
    '''
    if not recipes:
        print("저장할 레시피가 없습니다.")
        return

    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()

    # 테이블 생성 (존재하지 않을 경우)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            intro TEXT,
            info TEXT,
            photo TEXT,
            ingredients TEXT NOT NULL,
            recipe TEXT NOT NULL
        )
    ''')

    for info in recipes:
        # 레시피 이름이 이미 존재하는지 확인
        cursor.execute("SELECT COUNT(*) FROM recipes WHERE name = ?", (info['name'],))
        if cursor.fetchone()[0] > 0:
            print(f"'{info['name']}' 레시피는 이미 저장되어 있습니다. 저장하지 않습니다.")
            continue

        # 데이터 삽입
        cursor.execute(''' 
            INSERT INTO recipes (name, intro, info, photo, ingredients, recipe)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (info['name'], info['intro'], info['info'], info['photo'], info['ingredients'], "\n".join(info['recipe'])))
        print(f"레시피 '{info['name']}'가 데이터베이스에 저장되었습니다.")

    conn.commit()
    conn.close()

# 프로그램 실행
if __name__ == "__main__":
    food_info(2991) # 2851부터 시작함

