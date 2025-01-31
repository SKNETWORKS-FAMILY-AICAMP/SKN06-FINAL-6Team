import re
import traceback
import sqlite3
import pandas as pd

import requests
from bs4 import BeautifulSoup as BS
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# 사이트의 첫 게시글을 눌렀을 때 goView()의 두세번째 파라미터 (id와 post_no)를 추출하고 이를 이용해 이후 게시글을 크롤링한다.
drv = webdriver.Chrome(options=chrome_options)
url = "https://program.kbs.co.kr/2tv/enter/fun_staurant/pc/board.html?smenu=e817ba"
drv.get(url)
drv.implicitly_wait(3)

pattern = r"goView\('(?:.*?)', '([^']*)', '([^']*)'"
# 사이트가 iframe 태그 사용하므로 switch_to.frame()을 사용해 iframe 요소로 변경
drv.switch_to.frame("one_board")

res = drv.find_elements(By.CSS_SELECTOR, "#bbs_page_post_list a")[1].get_attribute("onclick")

# 찾을 요소 찾았으므로 다시 default_content로 변경
drv.switch_to.default_content()
# id와 post_no 추출했으므로 드라이버 종료
drv.quit()

# id와 post_no 찾기
matches = re.findall(pattern, res)

 # id와 post_no 추출
for match in matches:
    id = match[0]
    post_no = match[1]

# 크롤링 결과 저장할 데이터프레임 생성
df = pd.DataFrame(columns=["title", "ingredients", "recipe", "img"])

# 크롤링 중 오류 발생한 링크 저장할 변수 선언
exception_link = set()

# 정의한 경우의 수 외의 오류 발생 시 예외처리
def exception_():
    traceback.print_exc()
    print(f"res.url: {res.url}")
    exception_link.add(res.url)
    print(f"{text}\n\n")

while True:
    res = requests.get(f"https://cfpbbsapi.kbs.co.kr/board/v1/read_post?bbs_id=T2019-0286-04-296340&id={id}&post_no={post_no}")
    page_json = res.json()

    # 요리 이름, 본문 html 추출
    title = page_json['post']['post_title']
    contents = page_json['post']['post_contents']
    recontent = re.sub("\u003C", "<", contents)
    html = re.sub("\u003E", ">", recontent)
    bs = BS(html, "html.parser")

    # 이미지 추출출
    imgs = bs.findAll("img")
    img = [img['src'] for img in imgs]
    # 본문에서 텍스트만 추출
    text = bs.get_text(separator="\n", strip=True)
    # 필요없는 문자 반환
    text = text.replace("*레시피는 편스토랑 인스타그램에서도 확인할 수 있습니다♥@funstaurant_kbs", "")
    try:
        # 케이스 1) ■ 요리 재료 / ■ 만드는 법으로 나뉜 경우
        if "■ 요리 재료" in text:
            text = text.replace("■ 요리 재료", "")
            # 케이스 1-1) [기본 재료]가 있는 경우
            if text.find("[기본 재료]"):
                text = text.replace("[기본 재료]", "")
        elif "■ 요리재료" in text:
            text = text.replace("■ 요리재료", "")

        # 케이스 1-1) 재료와 레시피가 중복으로 적힌 경우
        recipe_pattern = r"\[(.*?) 재료\]\n(.*?)(?=\n\[|\n■|$)"
        if re.findall(recipe_pattern, text, re.DOTALL):
            name = re.findall(recipe_pattern, text, re.DOTALL)[0][0]
            title = f"{title}-{name}"
            if re.findall(r"■ <(.*?)> 레시피\n(.*?)(?=\n■|$)", recipe_section, re.DOTALL):
                recipe = re.findall(r"■ <(.*?)> 레시피\n(.*?)(?=\n■|$)", recipe_section, re.DOTALL)[0][1]
        ingredients, recipe = text.split("■ 만드는 법")
        df = pd.concat([df, pd.DataFrame({'title': [title], 'ingredients': [ingredients], 'recipe': [recipe], 'img': [img]})], ignore_index=True)
    except:
        try:
            # 케이스 2) [재료] / [만드는 법]으로 나뉜 경우
            while "[재료]" not in text:
                name, ingredients = text.split("[재료]", 1)
                ingredients, recipe = text.split("[만드는 법]", 1)
                df = pd.concat([df, pd.DataFrame({'title': [f"{title}-{name}"], 'ingredients': [ingredients], 'recipe': [recipe], 'img': [img]})], ignore_index=True)
        except:
            try:
                # 케이스 3) [(요리명) 재료] / [(요리명) 레시피로 나뉜 경우]
                # 1. [(요리명) 재료] 찾기
                recipe_pattern = r"\[(.*?) 재료\]\n(.*?)(?=\n\[|\n■|$)"
                recipes = re.findall(recipe_pattern, text, re.DOTALL)

                # 이름과 재료 저장하기기
                recipe_dict = {}
                for name, ingredients in recipes:
                    recipe_dict[name.strip()] = ingredients.strip()

                # 2. 레시피 시작점 찾기
                recipe_start_idx = text.find("■")
                recipe_section = text[recipe_start_idx:] if recipe_start_idx != -1 else ""

                # 3. 요리 이름과 레시피 매칭하기
                recipe_steps = re.findall(r"■ <(.*?)> 레시피\n(.*?)(?=\n■|$)", recipe_section, re.DOTALL)

                for name, recipe in recipe_steps:
                    if name in recipe_dict:
                        # 해당 요리의 재료 가져오기
                        ingredients = recipe_dict[name]
                        df = pd.concat([df, pd.DataFrame({'title': [f"{title}-{name}"], 'ingredients': [ingredients], 'recipe': [recipe.strip()], 'img': [img]})], ignore_index=True)
            except:
                exception_()
    #  # 마지막 페이지일 때 종료하기
    if page_json['next'] is None:
            print(f"exception_link: {exception_link}")
            break
    
    # 다음 페이지 파라미터 전송하기
    id = page_json['next']['id']
    post_no = page_json['next']['post_no']

    # 확인용 url 출력
    print(res.url)

# db 생성
conn = sqlite3.connect("funstaurant.db")
cursor = conn.cursor()

# 테이블 생성 (존재하지 않을 경우)
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS funstaurant (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        photo TEXT,
        ingredients TEXT NOT NULL,
        recipe TEXT NOT NULL
    )
''')

# 데이터 저장
for i in range(len(df)):
    cursor.execute(f'''
        INSERT INTO funstaurant (name, photo, ingredients, recipe) VALUES (
            "{df['title'][i]}", "{df['img'][i]}", "{df['ingredients'][i]}", "{df['recipe'][i]}"
        )
    ''')
conn.commit()
conn.close()