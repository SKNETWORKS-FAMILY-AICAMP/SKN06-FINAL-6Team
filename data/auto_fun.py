import re
import traceback
import sqlite3
import pandas as pd
from datetime import datetime

import requests
from bs4 import BeautifulSoup as BS
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse, RetrievalMode, QdrantVectorStore
from langchain_community.document_loaders import DataFrameLoader

from dotenv import dotenv_values
from dotenv import load_dotenv

load_dotenv()

def crawling():
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

    res = drv.find_elements(By.CSS_SELECTOR, "#bbs_page_post_list a")[0].get_attribute("onclick")

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
    df = pd.DataFrame(columns=["id", "name", "ingredients", "recipe", "img"])

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

        # 게시글 날짜가 현재 날짜보다 일주일 이상 이전 데이터일 때 종료하기
        post_diff = datetime.today() - datetime.strptime(page_json["post"]["valid_begin_date"], "%Y-%m-%d %H:%M:%S")
        print(post_diff)

        if post_diff.days > 7:
                print(f"exception_link: {exception_link}")
                break

        # 요리 이름, 본문 html 추출
        title = page_json['post']['post_title']
        contents = page_json['post']['post_contents']
        id = page_json['post']['post_no']
        recontent = re.sub("\u003C", "<", contents)
        html = re.sub("\u003E", ">", recontent)
        bs = BS(html, "html.parser")

        # 이미지 추출
        img = bs.findAll("img")[0]['src']
        # img = [img['src'] for img in imgs]
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
            df = pd.concat([df, pd.DataFrame({'id':[id], 'name': [title], 'ingredients': [ingredients], 'recipe': [recipe], 'img': [img]})], ignore_index=True)
        except:
            try:
                # 케이스 2) [재료] / [만드는 법]으로 나뉜 경우
                while "[재료]" not in text:
                    name, ingredients = text.split("[재료]", 1)
                    ingredients, recipe = text.split("[만드는 법]", 1)
                    df = pd.concat([df, pd.DataFrame({'id':[id], 'name': [f"{title}-{name}"], 'ingredients': [ingredients], 'recipe': [recipe], 'img': [img]})], ignore_index=True)
            except:
                try:
                    # 케이스 3) [(요리명) 재료] / [(요리명) 레시피로 나뉜 경우]
                    # 1. [(요리명) 재료] 찾기
                    recipe_pattern = r"\[(.*?) 재료\]\n(.*?)(?=\n\[|\n■|$)"
                    recipes = re.findall(recipe_pattern, text, re.DOTALL)

                    # 이름과 재료 저장하기
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
                            df = pd.concat([df, pd.DataFrame({'id':[id], 'name': [f"{title}-{name}"], 'ingredients': [ingredients], 'recipe': [recipe.strip()], 'img': [img]})], ignore_index=True)
                except:
                    exception_()
        
        # 다음 페이지 파라미터 전송하기
        id = page_json['next']['id']
        post_no = page_json['next']['post_no']

        # 확인용 url 출력
        print(res.url)
        print(df)

    def clean_name(name):
        if name:
            # 회차 제거 (예: "[257회] " 제거)
            name = re.sub(r"\[\d+회\]\s*", "", name)
            # HTML 엔티티 제거 (예: "&lt;", "&gt;")
            name = re.sub(r"&lt;|&gt;", "", name)
            return name.strip()
        return name

    # name 컬럼 정리 적용
    df["clean_name"] = df["name"].apply(clean_name)

    # 정리된 데이터 컬럼 반영
    df = df[["id", "clean_name", "ingredients", "recipe", "img"]]
    df.rename(columns={"clean_name": "name"}, inplace=True)

    # '레시피' 뒤에 있는 모든 텍스트 제거 함수 (요리명 유지)
    def clean_recipe_suffix(name):
        if name:
            return re.sub(r"(레시피).*", r"\1", name).strip()  # '레시피' 이후 모든 텍스트 삭제
        return name

    # name 컬럼 정리 적용
    df["clean_name"] = df["name"].apply(clean_recipe_suffix)

    # 정리된 데이터 컬럼 반영
    df = df[["id","clean_name", "ingredients", "recipe", "img"]]
    df.rename(columns={"clean_name": "name"}, inplace=True)

    # 재료 목록 전처리 함수
    def clean_ingredients(ingredients):
        if ingredients:
            # 개행 문자 및 불필요한 공백 제거
            ingredients = ingredients.replace("\n", " ").strip()
            # 특수 문자 정리 (예: 연속된 공백 제거)
            ingredients = re.sub(r"\s+", " ", ingredients)
            return ingredients
        return ingredients

    # ingredients 컬럼 정리 적용
    df["clean_ingredients"] = df["ingredients"].apply(clean_ingredients)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "clean_ingredients", "recipe", "img"]]
    df.rename(columns={"clean_ingredients": "ingredients"}, inplace=True)

    # 특수 문자 제거 함수
    def remove_special_chars(text):
        if text:
            # 특수 문자 제거 (예: ■, ★, ※ 등)
            text = re.sub(r"[■★※●◆◇■□▽▼○◎]", "", text)
            # 불필요한 공백 정리
            text = re.sub(r"\s+", " ", text).strip()
            return text
        return text

    # ingredients 컬럼에서 특수 문자 제거 적용
    df["clean_ingredients"] = df["ingredients"].apply(remove_special_chars)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "clean_ingredients", "recipe", "img"]]
    df.rename(columns={"clean_ingredients": "ingredients"}, inplace=True)

    # 특수 문자 및 불필요한 기호 제거 함수 (추가 기호 포함)
    def clean_recipe_text(text):
        if text:
            # 기본 특수 문자 및 추가 기호 제거 (!, ~, *, @ 등)
            text = re.sub(r"[■★※●◆◇■□ㅁ♥▽▼○◎!~*@#%^&+=<>?|]", "", text)
            # 불필요한 공백 정리
            text = re.sub(r"\s+", " ", text).strip()
            return text
        return text

    # recipe 컬럼에서 특수 문자 및 추가 기호 제거 적용
    df["clean_recipe"] = df["recipe"].apply(clean_recipe_text)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)

    # 레시피 번호 매기기 방식 정리 함수 (0. 삭제 + 이모티콘 번호 변경)
    def refine_numbering_v2(text):
        if text:
            # "0." 삭제 (특정 패턴 포함 가능)
            text = re.sub(r"\b0\.\s*", "", text)
            # ①, ② 같은 이모티콘을 1., 2. 형식으로 변경
            text = re.sub(r"[①❶]", "1.", text)
            text = re.sub(r"[②❷]", "2.", text)
            text = re.sub(r"[③❸]", "3.", text)
            text = re.sub(r"[④❹]", "4.", text)
            text = re.sub(r"[⑤❺]", "5.", text)
            text = re.sub(r"[⑥❻]", "6.", text)
            text = re.sub(r"[⑦❼]", "7.", text)
            text = re.sub(r"[⑧❽]", "8.", text)
            text = re.sub(r"[⑨❾]", "9.", text)
            text = re.sub(r"[⑩❿]", "10.", text)
            # 불필요한 공백 정리
            text = re.sub(r"\s+", " ", text).strip()
            return text
        return text

    # recipe 컬럼에서 번호 매기기 방식 수정 적용
    df["clean_recipe"] = df["recipe"].apply(refine_numbering_v2)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)

    def remove_instagram_text(text):
        if text:
            return text.replace("레시피는 편스토랑 인스타그램에서도 확인할 수 있습니다 funstaurant_kbs", "").strip()
        return text


    # recipe 컬럼에서 번호 매기기 방식 수정 적용
    df["clean_recipe"] = df["recipe"].apply(remove_instagram_text)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)

    def remove_instagram_text2(text):
        if text:
            return text.replace("레시피는 편스토랑 인스타그램에도 확인할 수 있습니다 funstaurant_kbs", "").strip()
        return text


    # recipe 컬럼에서 번호 매기기 방식 수정 적용
    df["clean_recipe"] = df["recipe"].apply(remove_instagram_text2)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)

    def remove_instagram_text3(text):
        if text:
            return text.replace("레시피는 편스토랑 인스타그램 에서도 확인할 수 있습니다 funstaurant_kbs", "").strip()
        return text


    # recipe 컬럼에서 번호 매기기 방식 수정 적용
    df["clean_recipe"] = df["recipe"].apply(remove_instagram_text3)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)

    def remove_instagram_text4(text):
        if text:
            return text.replace("레시피는 편스토랑 인스타그램에서도 확인할 수 있습니다", "").strip()
        return text


    # recipe 컬럼에서 번호 매기기 방식 수정 적용
    df["clean_recipe"] = df["recipe"].apply(remove_instagram_text4)

    # 정리된 데이터 컬럼 반영
    df = df[["id","name", "ingredients", "clean_recipe", "img"]]
    df.rename(columns={"clean_recipe": "recipe"}, inplace=True)
    print(f"전처리 {df.columns}")

    conn = sqlite3.connect("chat/db/funs.db")
    cursor = conn.cursor()

    # 데이터 저장
    for i in range(len(df)):
        cursor.execute(f'''
            INSERT INTO menu (id, name, img, ingredients, recipe) VALUES (
                "{df['id'][i]}", "{df['name'][i]}", "{df['img'][i]}", "{df['ingredients'][i]}", "{df['recipe'][i]}"
            )
        ''')
    conn.commit()
    conn.close()
    df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe']
    df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
    loader = DataFrameLoader(df, page_content_column="page_content")
    docs = loader.load()

    # vector db에 저장
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
    urls = dotenv_values()["QDRANT_SERVER_URL"]
    qdrant = QdrantVectorStore.from_existing_collection(embedding=embeddings, sparse_embedding=sparse_embeddings, collection_name="funs", url=urls, retrieval_mode=RetrievalMode.HYBRID)
    qdrant.add_documents(docs)

crawling()