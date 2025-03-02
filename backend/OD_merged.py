import os
import pandas as pd
import sqlite3
import torch
import clip
from ultralytics import YOLO
from PIL import Image
import numpy as np
from torchvision import transforms
from dotenv import load_dotenv

from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever, BM25Retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from collections import Counter

# ✅ 환경 변수 로드
load_dotenv()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # OpenMP 충돌 방지 설정

# ✅ YOLO 및 CLIP 모델 로드
device = "cuda" if torch.cuda.is_available() else "cpu"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# YOLO 모델 파일 경로 설정
yolo_model_path = os.path.join(BASE_DIR, "OD", "YOLO", "detect", "workspace", "runs", "detect", "train3", "weights", "best.pt")
yolo_model = YOLO(yolo_model_path)

# CLIP 모델 로드
clip_model, preprocess = clip.load("ViT-B/32", device=device)



# ✅ YOLO 감지 클래스의 한글 변환 딕셔너리 (누락된 항목 추가)
ingredient_translations = {
    "Potato": "감자",
    "egg": "달걀",
    "cucumber": "오이",
    "green chilies": "청양고추",
    "spring onion": "쪽파",
    "pear": "배",
    "Capsicum": "피망",
    "Green Peas": "완두콩",
    "tomato": "토마토",
    "green beans": "꽈리고추",
    "ham": "햄",
    "apple": "사과",
    "Onion": "양파",
    "brinjal": "가지",
    "lemon": "레몬",
    "chocolate": "초콜릿",
    "Bitter melon": "여주",
    "goat_cheese": "염소 치즈",
    "papaya": "파파야",
    "heavy_cream": "생크림",
    "flour": "밀가루",
    "strawberry": "딸기",
    "beet": "비트",
    "half carrot": "반 개의 당근",
    "strawberries": "딸기",
    "cauliflower": "콜리플라워",
    "zucchini": "주키니",
    "swiss yoghurt": "스위스 요구르트",
    "chilli": "고추",
    "peas": "완두콩",
    "Sapodilla": "사포딜라",
    "corn": "옥수수",
    "orange": "오렌지",
    "butter": "버터",
    "olive": "올리브",
    "peach": "복숭아",
    "jalapeno": "할라피뇨",
    "scarletgourds": "붉은 박",
    "sauce": "소스",
    "redonion": "적양파",
    "chillies": "고추",
    "chicken": "닭고기",
    "pumpkin": "호박",
    "Green Chili": "풋고추",
    "mineral water": "생수",
    "shrimp": "새우",
    "mango": "망고",
    "half onion": "반 개의 양파",
    "Ginger": "생강",
    "raddish": "무",
    "basil": "바질",
    "sweet potato": "고구마",
    "beef": "소고기",
    "chicken_breast": "닭가슴살",
    "beans": "콩",
    "charger": "충전기",
    "swiss butter": "스위스 버터",
    "red grapes": "적포도",
    "milk": "우유",
    "parsley": "파슬리",
    "watermelon": "수박",
    "Lady finger": "오크라",
    "bell_pepper": "파프리카",
    "sausage": "소시지",
    "beetroot": "비트",
    "Brinjal": "가지",
    "sweet_potato": "고구마",
    "mushroom": "버섯",
    "Cluster bean": "클러스터 콩",
    "bottle": "병",
    "Curry Leaf": "커리 잎",
    "potato": "감자",
    "Hyacinth Beans": "히아신스 콩",
    "Cabbage": "양배추",
    "grape": "포도",
    "peppers": "고추",
    "shallot": "샬롯",
    "ginger": "생강",
    "bittergourd": "여주",
    "sugar": "설탕",
    "eggplant": "가지",
    "cheese": "치즈",
    "kiwi": "키위",
    "fig": "무화과",
    "Calabash": "조롱박",
    "Tomato": "토마토",
    "Cauliflower": "콜리플라워",
    "swiss jam": "스위스 잼",
    "Garlic": "마늘",
    "courgettes": "애호박",
    "eggs": "달걀",
    "dates": "대추",
    "broccoli": "브로콜리",
    "mushrooms": "버섯",
    "ground_beef": "다진 소고기",
    "pineapple": "파인애플",
    "pomogranate": "석류",
    "aubergine": "가지",
    "blueberries": "블루베리",
    "carrot": "당근",
    "red onion": "적양파",
    "bottlegourd": "호리병박",
    "haft-cabbage": "반 개의 양배추",
    "lettuce": "상추",
    "green_beans": "꽈리고추",
    "capsicum": "피망",
    "garlic": "마늘",
    "onion": "양파",
    "cabbage": "양배추",
    "bell pepper": "파프리카",
    "spounggourd": "수세미오이",
    "spinach": "시금치",
    "lime": "라임",
    "Sponge Gourd": "수세미 오이",
    "banana": "바나나",
    "bread": "빵",
    "asparagus": "아스파라거스",
    "coriander": "고수"
}

# ✅ CLIP 사전 정의된 클래스 리스트
possible_labels = [
        # ✅ 채소
        "양파 (Onion)", "대파 (Green Onion)", "쪽파 (Spring Onion)", "마늘 (Garlic)", "배추 (Napa Cabbage)", 
        "양배추 (Cabbage)", "깻잎 (Perilla Leaf)", "시금치 (Spinach)", 
        "부추 (Chives)", "미나리 (Water Parsley)", "쑥갓 (Crown Daisy)", "청경채 (Bok Choy)", 
        "당근 (Carrot)", "무 (Radish)", "감자 (Potato)", "고구마 (Sweet Potato)", "호박 (Pumpkin)",
        "가지 (Eggplant)", "오이 (Cucumber)", "피망 (Bell Pepper)", "파프리카 (Capsicum)", "콩나물 (Bean Sprouts)", "홍고추 (Red Pepper)",

        # ✅ 버섯류
        "버섯 (Mushroom)", "새송이버섯 (King Oyster Mushroom)", "표고버섯 (Shiitake Mushroom)", 
        "팽이버섯 (Enoki Mushroom)", "느타리버섯 (Oyster Mushroom)", 

        # ✅ 과일
        "사과 (Apple)", "배 (Pear)", "귤 (Tangerine)", "오렌지 (Orange)", "레몬 (Lemon)", 
        "자몽 (Grapefruit)", "바나나 (Banana)", "포도 (Grape)", "수박 (Watermelon)", 
        "딸기 (Strawberry)", "블루베리 (Blueberry)", "체리 (Cherry)", "망고 (Mango)", 
        "파인애플 (Pineapple)", "키위 (Kiwi)", "복숭아 (Peach)", "자두 (Plum)", 

        # ✅ 육류
        "소고기 (Beef)", "돼지고기 (Pork)", "닭고기 (Chicken)", "양고기 (Lamb)", 
        "삼겹살 (Pork Belly)", "목살 (Pork Shoulder)", "갈비 (Ribs)", "안심 (Tenderloin)", 
        "등심 (Sirloin)", "닭다리살 (Chicken Thigh)", "닭날개 (Chicken Wing)", 

        # ✅ 해산물
        "새우 (Shrimp)", "오징어 (Squid)", "문어 (Octopus)", "낙지 (Small Octopus)", 
        "꽃게 (Blue Crab)", "대게 (Snow Crab)", "바지락 (Clam)", "홍합 (Mussel)", 
        "전복 (Abalone)", "굴 (Oyster)", "고등어 (Mackerel)", "갈치 (Hairtail)", 
        "연어 (Salmon)", "참치 (Tuna)", "광어 (Flounder)", "조기 (Croaker)",

        # ✅ 유제품
        "우유 (Milk)", "치즈 (Cheese)", "요거트 (Yogurt)", "버터 (Butter)", "생크림 (Whipping Cream)", "크림치즈 (Cream Cheese)",
        "연유 (Condensed Milk)", "아이스크림 (Ice Cream)",

        # ✅ 곡류 및 견과류
        "쌀 (Rice)", "현미 (Brown Rice)", "찹쌀 (Glutinous Rice)", "보리 (Barley)", 
        "아몬드 (Almond)", "호두 (Walnut)", "잣 (Pine Nut)", "캐슈넛 (Cashew)", "피스타치오 (Pistachio)",
        "해바라기씨 (Sunflower Seed)", "콩 (Soybean)", "검정콩 (Black Bean)", "녹두 (Mung Bean)",
        "팥 (Red Bean)", "참깨 (Sesame)", "퀴노아 (Quinoa)", "옥수수 (Corn)",

        # ✅ 기타
        "두부 (Tofu)", "떡 (Rice Cake)", "어묵 (Fish Cake)", "김 (Seaweed)", "해초 (Seaweed)", 
        "라면 (Instant Noodles)", "국수 (Noodles)", "만두 (Dumplings)", "피자 (Pizza)",
        "햄버거 (Hamburger)", "샌드위치 (Sandwich)", "케이크 (Cake)", "쿠키 (Cookie)", "파스타 (Pasta)",   
]

# CLIP 토큰화
text_inputs = clip.tokenize(possible_labels).to(device)
text_features = clip_model.encode_text(text_inputs).detach()

# def translate_ingredients(ingredients):
#     """ YOLO 감지 클래스가 한글 변환 딕셔너리에 있으면 변환, 없으면 그대로 반환 """
#     return [ingredient_translations.get(ing, ing) for ing in ingredients]

# ✅ 유사도 임계값 설정
def detect_ingredients(image_path):
    """ YOLO + CLIP을 활용한 식재료 감지 """

    image = Image.open(image_path).convert("RGB")
    image_width, image_height = image.size
    results = yolo_model(image_path, conf=0.1)

    detected_ingredients = set()
    yolo_detected = False
    expand_ratio = 1.2  # YOLO 감지 박스 확장 비율
    grid_size = 150  # YOLO 미감지 영역에 대해 CLIP이 분석할 그리드 크기

    # ✅ YOLO 감지 객체 분석
    for result in results:
        for box in result.boxes:
            confidence = box.conf[0].item()
            label = result.names[int(box.cls[0])]

            if confidence >= 0.4:
                print(f"✅ YOLO 감지: {label} (신뢰도 {confidence:.2f})")
                detected_ingredients.add(label)
                yolo_detected = True
            else:
                print(f"⚠️ YOLO 신뢰도 {confidence:.2f} (0.4 미만), CLIP으로 보완 분석...")

                # YOLO 감지 박스 크기 확장
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                box_width = x2 - x1
                box_height = y2 - y1

                x1 = max(0, x1 - int((expand_ratio - 1) / 2 * box_width))
                y1 = max(0, y1 - int((expand_ratio - 1) / 2 * box_height))
                x2 = min(image_width, x2 + int((expand_ratio - 1) / 2 * box_width))
                y2 = min(image_height, y2 + int((expand_ratio - 1) / 2 * box_height))

                cropped_img = image.crop((x1, y1, x2, y2))

                # CLIP으로 보완 분석
                image_input = preprocess(cropped_img).unsqueeze(0).to(device)
                image_features = clip_model.encode_image(image_input).detach()
                similarity = (image_features @ text_features.T).softmax(dim=-1)

                for idx, conf in enumerate(similarity.squeeze(0).tolist()):
                    if conf >= 0.2:
                        detected_ingredients.add(possible_labels[idx])
                        print(f"✅ CLIP 보완 결과: {possible_labels[idx]} (유사도 {conf:.2f})")

    # ✅ YOLO가 감지한 객체가 없을 경우, 전체 이미지를 그리드로 분할하여 CLIP 분석
    if not yolo_detected:
        print("⚠️ YOLO가 감지한 식재료 없음, CLIP으로 전체 이미지 분석...")

        for y in range(0, image_height, grid_size):
            for x in range(0, image_width, grid_size):
                x1 = x
                y1 = y
                x2 = min(x + grid_size, image_width)
                y2 = min(y + grid_size, image_height)

                grid_img = image.crop((x1, y1, x2, y2))

                image_input = preprocess(grid_img).unsqueeze(0).to(device)
                image_features = clip_model.encode_image(image_input).detach()
                similarity = (image_features @ text_features.T).softmax(dim=-1)

                for idx, conf in enumerate(similarity.squeeze(0).tolist()):
                    if conf >= 0.2:
                        detected_ingredients.add(possible_labels[idx])
                        print(f"✅ CLIP 분석 결과: {possible_labels[idx]} (유사도 {conf:.2f})")

    # ✅ 감지된 재료를 한글로 변환
    translated_ingredients = [ingredient_translations.get(ing, ing) for ing in detected_ingredients]

    # ✅ 변환된 값 디버깅 로그
    print(f"변환된 재료 리스트: {translated_ingredients}")

    return list(translated_ingredients)




### 임베딩 모델
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 모델
model = ChatOpenAI(model="gpt-4o-mini")

### 메모리
memory = ConversationBufferMemory(llm=model, max_token_limit=200, return_messages=True, memory_key="history")

def load(case):
    if case == "fun":
        conn = sqlite3.connect("funs.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe']
        df.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    elif case == "ref":
        conn = sqlite3.connect("fridges.db")
        df = pd.read_sql("SELECT * FROM menu", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipes']
        df.drop(columns=['name', 'ingredients', 'recipes'], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs
    
    else:
        conn = sqlite3.connect("data.db")
        df = pd.read_sql("SELECT * FROM processed_data", conn)

        df['page_content'] = df['name'] + " " + df['ingredients'] + " " + df['recipe'] + " " + df['category'] + " " + df['info'] + " " + df['intro']
        df.drop(columns=['name', 'ingredients', 'recipe', "info", "intro"], inplace=True)
        conn.close()
        loader = DataFrameLoader(df, page_content_column="page_content")
        docs = loader.load()
        return docs

def fun(query=None):
    '''
    편스토랑 retriever
    '''
    ## load
    docs = load("fun")

    # ## vectordb 저장 -> 최초 일회만 실행
    # fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 편스토랑 임베딩 후 db
    # fais.save_local("fun_faiss") # 로컬 저장
    
    ## vectordb 로드
    fais = FAISS.load_local("fun_faiss", embeddings, allow_dangerous_deserialization=True) # 로컬 저장 로드

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr

def ref(query=None):
    '''
    냉장고를 부탁해 retriever
    '''
    ## load
    docs = load("ref")

    # ## vectordb 저장 -> 최초 일회만 실행
    # fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 냉부 임베딩 후 db
    # fais.save_local("ref_faiss") # 로컬 저장

    ## vectordb 로드
    fais = FAISS.load_local("ref_faiss", embeddings, allow_dangerous_deserialization=True)

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr

def man(query=None):
    '''
    만개의 레시피 retriever
    '''
    ## load
    docs = load("man")

    # ## vectordb 저장 -> 최초 일회만 실행
    # fais = FAISS.from_documents(documents=docs, embedding=embeddings) # 만개 임베딩 후 db
    # fais.save_local("man_faiss") # 로컬 저장

    # vectordb 로드
    fais = FAISS.load_local("man_faiss", embeddings, allow_dangerous_deserialization=True)

    ## bm25 retriever, faiss retriever 앙상블
    bm25_retr = BM25Retriever.from_documents(docs)
    bm25_retr.k = 3
    fais_retr = fais.as_retriever(search_kwargs={"k": 3})
    return bm25_retr, fais_retr





def mkch():
    retrievers = []
    for case in ["fun", "ref", "man"]:
        docs = load(case)
        fais = FAISS.load_local(f"{case}_faiss", embeddings, allow_dangerous_deserialization=True)
        bm25_retr = BM25Retriever.from_documents(docs)
        bm25_retr.k = 3
        fais_retr = fais.as_retriever(search_kwargs={"k": 3})
        retrievers.extend([bm25_retr, fais_retr])

    retriever = EnsembleRetriever(retrievers=retrievers)

    messages = [
        ("ai", """
        너는 사용자의 질문(question)에 맞는 요리 세가지를 알려주는 ai야.

        요리 소개할 때 이름을 언급한 뒤, 한 줄 정도 간단한 요리 소개를 하고 재료를 알려줘.
        사용자가 네가 추천해준 요리 안에서 요리를 선택하면 레시피와 함께 해당 요리의 사진, 영상 데이터를 알려줘.
        메뉴 이름, 재료, 레시피, 사진, 영상은 fun_faiss, man_faiss, ref_faiss에 있는 데이터를 그대로 가져와.
        만약 사진 혹은 영상이 없으면, 사진이나 영상은 알려주지마.
        답변을 context에서 찾을 수 없으면 모른다고 대답해.
        답변으로 요리 세가지를 알려줄 때는 사용자가 입력한 재료가 정확히 들어간 순서대로 답변하고
        사용자가 입력한 재료가 여러가지라면 입력된 재료가 많은 요리 순서대로 답변해.
        만약 사용자가 입력한 재료가 들어간 요리가 없으면 그 요리는 제외하고 답변해.
        {context}"""),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{question}"),
    ]

    prompt_template = ChatPromptTemplate(messages)

    chain = RunnableLambda(lambda x: x['question']) | {
        "context": retriever,
        "question": RunnablePassthrough(),
        "history": RunnableLambda(lambda _: memory.load_memory_variables({})["history"])
    } | prompt_template | model | StrOutputParser()

    return chain


    # 메모리
    def load_history(input):
        return memory.load_memory_variables({})["history"]

    # retriever 로드 => 추후 함수 선택 코드 넣어야 함
    rbm25_retr, rfais_retr = ref()
    fbm25_retr, ffais_retr = fun()
    mbm25_retr, mfais_retr = man()

    retriever = EnsembleRetriever(retrievers=[rbm25_retr, rfais_retr, fbm25_retr, ffais_retr,mbm25_retr, mfais_retr],) # weights=[0.25, 0.25, 0.25, 0.25],)

    # Chain 구성 retriever(관련 문서 조회) -> prompt_template(prompt 생성) model(정답) -> output parser
    chain = RunnableLambda(lambda x:x['question']) | {"context": retriever, "question":RunnablePassthrough() , "history": RunnableLambda(load_history)}  | prompt_template | model | StrOutputParser()
    return chain



        
# ✅ 챗봇 응답 시 한국어로 변환된 재료 리스트 함께 출력
def chat():
    """ 사용자가 입력한 텍스트 또는 여러 개의 이미지를 분석하여 요리를 추천하는 함수 """
    chain = mkch()

    while True:
        query = input("텍스트 또는 이미지 경로 입력 (여러 개 입력 시 띄어쓰기로 구분, 종료하려면 'exit' 입력) > ")
        if query.lower() == "exit":
            break

        input_parts = query.split()
        detected_ingredients = set()
        text_input = []

        for part in input_parts:
            if os.path.exists(part) and part.lower().endswith((".jpg", ".jpeg", ".png")):
                print(f"🖼 이미지 감지 중... ({part})")
                detected_ingredients.update(detect_ingredients(part))
            else:
                text_input.append(part)

        # ✅ 감지된 식재료 리스트 출력 (한글 변환 적용됨)
        if detected_ingredients:
            print("\n📌 **재료 리스트 (보이는 범위 내)**")
            for ingredient in detected_ingredients:
                print(f"✅ {ingredient}")

        # ✅ 최종 Query 구성 (이미지에서 감지된 재료 + 사용자가 입력한 텍스트)
        combined_query = " ".join(text_input)
        query_with_ingredients = f"{combined_query} 감지된 재료: {', '.join(detected_ingredients)}"

        print(f"Final Query: {query_with_ingredients}")

        res = chain.invoke({"question": query_with_ingredients})
        memory.save_context(inputs={"human": query_with_ingredients}, outputs={"ai": res})

        if detected_ingredients:
            print("\n📝 인식된 재료들:")
            print(" / ".join(detected_ingredients))
            print("\n🍽️ 추천 요리 목록:")

        print(res)

chat()




