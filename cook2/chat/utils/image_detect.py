import os
import torch
import clip
from ultralytics import YOLO
from PIL import Image
import numpy as np
from torchvision import transforms
import re

# ✅ YOLO 및 CLIP 모델 로드
device = "cpu"
BASE_DIR = os.getcwd()

YOLO_FOOD_MODEL_PATH = os.path.join(BASE_DIR,"chat","runs","detect","train_식재료","best.pt")
YOLO_FRIDGE_MODEL_PATH = os.path.join(BASE_DIR,"chat","runs","detect","train_냉장고","best.pt")

# YOLO 모델 로드
yolo_model_food = YOLO(YOLO_FOOD_MODEL_PATH)
yolo_model_fridge = YOLO(YOLO_FRIDGE_MODEL_PATH)

# CLIP 모델 로드
clip_model, preprocess = clip.load("ViT-B/32", device=device)


# ✅ YOLO 감지 클래스 한글 변환 딕셔너리
food_classes = {
    "Bitter melon": "여주", "Brinjal": "가지", "Cabbage": "양배추", "Calabash": "조롱박", "Capsicum": "피망",
    "Cauliflower": "콜리플라워", "Cluster bean": "클러스터 콩", "Curry Leaf": "커리 잎", "Garlic": "마늘", "Ginger": "생강",
    "Green Chili": "풋고추", "Green Peas": "완두콩", "Hyacinth Beans": "히아신스 콩", "Lady finger": "오크라", "Onion": "양파",
    "Potato": "감자", "Sapodilla": "사포딜라", "Sponge Gourd": "수세미 오이", "Tomato": "토마토", "apple": "사과",
    "banana": "바나나", "beans": "콩", "beef": "소고기", "beet": "비트", "beetroot": "비트루트", "bell_pepper": "파프리카",
    "bittergourd": "여주", "blueberries": "블루베리", "bottle": "병", "bottlegourd": "호리병박", "bread": "빵",
    "broccoli": "브로콜리", "butter": "버터", "carrot": "당근", "cheese": "치즈", "chicken": "닭고기",
    "chicken_breast": "닭가슴살", "chilli": "고추", "chocolate": "초콜릿", "corn": "옥수수", "cucumber": "오이",
    "egg": "달걀", "eggplant": "가지", "fig": "무화과", "flour": "밀가루", "goat_cheese": "염소 치즈", "grape": "포도",
    "green_beans": "꽈리고추", "ground_beef": "다진 소고기", "ham": "햄", "heavy_cream": "생크림", "jalapeno": "할라피뇨",
    "kiwi": "키위", "lemon": "레몬", "lettuce": "상추", "lime": "라임", "milk": "우유", "mushrooms": "버섯",
    "onion": "양파", "orange": "오렌지", "papaya": "파파야", "pear": "배", "pineapple": "파인애플", "potato": "감자",
    "pumpkin": "호박", "raddish": "무", "redonion": "적양파", "shrimp": "새우", "spinach": "시금치", "strawberry": "딸기",
    "sugar": "설탕", "sweet_potato": "고구마", "watermelon": "수박", "zucchini": "주키니"
}

fridge_classes = {
    "apple": "사과", "asparagus": "아스파라거스", "aubergine": "가지", "banana": "바나나", "basil": "바질",
    "beans": "콩", "beef": "소고기", "beetroot": "비트", "bell pepper": "파프리카", "blueberries": "블루베리",
    "broccoli": "브로콜리", "cabbage": "양배추", "carrot": "당근", "cauliflower": "콜리플라워",
    "cheese": "치즈", "chicken": "닭고기", "chillies": "고추", "coriander": "고수", "corn": "옥수수",
    "cucumber": "오이", "dates": "대추", "egg": "달걀", "flour": "밀가루", "garlic": "마늘", "ginger": "생강",
    "green beans": "꽈리고추", "green chilies": "청양고추", "lemon": "레몬", "lettuce": "상추", "lime": "라임",
    "mango": "망고", "mineral water": "생수", "mushroom": "버섯", "olive": "올리브", "onion": "양파",
    "orange": "오렌지", "parsley": "파슬리", "peach": "복숭아", "peas": "완두콩", "peppers": "고추",
    "potato": "감자", "pumpkin": "호박", "red grapes": "적포도", "red onion": "적양파", "sauce": "소스",
    "sausage": "소시지", "shallot": "샬롯", "spinach": "시금치", "spring onion": "쪽파", "strawberry": "딸기",
    "sugar": "설탕", "sweet potato": "고구마", "swiss butter": "스위스 버터", "swiss jam": "스위스 잼",
    "swiss yoghurt": "스위스 요구르트", "tomato": "토마토", "watermelon": "수박"
}

# ✅ CLIP 사전 정의된 클래스 리스트
possible_labels = [
        # ✅ 채소
        "양파 (Onion)", "대파 (Green Onion)", "쪽파 (Spring Onion)", "마늘 (Garlic)", "배추 (Napa Cabbage)", 
        "양배추 (Cabbage)", "깻잎 (Perilla Leaf)", "시금치 (Spinach)", "상추 (Lettuce)", "청경채 (Bok Choy)",
        "부추 (Chives)", "미나리 (Water Parsley)", "쑥갓 (Crown Daisy)", "고추 (Chili Pepper)", 
        "당근 (Carrot)", "무 (Radish)", "감자 (Potato)", "고구마 (Sweet Potato)", "호박 (Pumpkin)",
        "애호박 (Korean Zucchini)", "가지 (Eggplant)", "오이 (Cucumber)", "피망 (Bell Pepper)", 
        "파프리카 (Capsicum)", "콩나물 (Bean Sprouts)", "숙주나물 (Mung Bean Sprouts)", "브로콜리 (Broccoli)",
        "콜리플라워 (Cauliflower)", "고사리 (Bracken)", "토란대 (Taro Stems)", "연근 (Lotus Root)",

        # ✅ 버섯류
        "버섯 (Mushroom)", "새송이버섯 (King Oyster Mushroom)", "표고버섯 (Shiitake Mushroom)", 
        "팽이버섯 (Enoki Mushroom)", "느타리버섯 (Oyster Mushroom)", "양송이버섯 (Button Mushroom)",

        # ✅ 과일
        "사과 (Apple)", "배 (Pear)", "귤 (Tangerine)", "오렌지 (Orange)", "레몬 (Lemon)", 
        "자몽 (Grapefruit)", "바나나 (Banana)", "포도 (Grape)", "수박 (Watermelon)", 
        "딸기 (Strawberry)", "블루베리 (Blueberry)", "체리 (Cherry)", "망고 (Mango)", 
        "파인애플 (Pineapple)", "키위 (Kiwi)", "복숭아 (Peach)", "자두 (Plum)", "곶감 (Dried Persimmon)","감(Persimmon)"

        # ✅ 육류
        "소고기 (Beef)", "돼지고기 (Pork)", "닭고기 (Chicken)", "양고기 (Lamb)", 
        "삼겹살 (Pork Belly)", "목살 (Pork Shoulder)", "갈비 (Ribs)", "안심 (Tenderloin)", 
        "등심 (Sirloin)", "닭다리살 (Chicken Thigh)", "닭날개 (Chicken Wing)", "베이컨 (Bacon)", "햄 (Ham)", "닭가슴살 (Chicken Breast)"

        # ✅ 해산물
        "새우 (Shrimp)", "오징어 (Squid)", "문어 (Octopus)", "낙지 (Small Octopus)", 
        "꽃게 (Blue Crab)", "대게 (Snow Crab)", "바지락 (Clam)", "홍합 (Mussel)", 
        "전복 (Abalone)", "굴 (Oyster)", "고등어 (Mackerel)", "갈치 (Hairtail)", 
        "연어 (Salmon)", "참치 (Tuna)", "광어 (Flounder)", "조기 (Croaker)", "멸치 (Anchovy)", "미역 (Seaweed)",

        # ✅ 유제품
        "우유 (Milk)", "치즈 (Cheese)", "요거트 (Yogurt)", "버터 (Butter)", "생크림 (Whipping Cream)", 
        "크림치즈 (Cream Cheese)", "연유 (Condensed Milk)", "아이스크림 (Ice Cream)", "두유 (Soy Milk)",

        # ✅ 곡류 및 견과류
        "쌀 (Rice)", "현미 (Brown Rice)", "찹쌀 (Glutinous Rice)", "보리 (Barley)", "오트밀 (Oatmeal)",
        "아몬드 (Almond)", "호두 (Walnut)", "잣 (Pine Nut)", "캐슈넛 (Cashew)", "피스타치오 (Pistachio)",
        "해바라기씨 (Sunflower Seed)", "콩 (Soybean)", "검정콩 (Black Bean)", "녹두 (Mung Bean)",
        "팥 (Red Bean)", "참깨 (Sesame)", "퀴노아 (Quinoa)", "옥수수 (Corn)", "땅콩 (Peanut)",

        # ✅ 기본 양념 & 가공식품
        "김치 (Kimchi)", "된장 (Doenjang)", "고추장 (Gochujang)", "간장 (Soy Sauce)", "소금 (Salt)", 
        "후추 (Black Pepper)", "설탕 (Sugar)", "식초 (Vinegar)", "참기름 (Sesame Oil)", "들기름 (Perilla Oil)",
        "미림 (Cooking Wine)", "맛술 (Seasoned Cooking Wine)", "마요네즈 (Mayonnaise)", "케찹 (Ketchup)",
        "머스타드 (Mustard)", "고춧가루 (Red Pepper Powder)", "카레가루 (Curry Powder)", "소시지 (Sausage)",

        # ✅ 기타
        "두부 (Tofu)", "떡 (Rice Cake)", "어묵 (Fish Cake)", "김 (Seaweed)", "해초 (Seaweed)", 
        "라면 (Instant Noodles)", "국수 (Noodles)", "만두 (Dumplings)", "피자 (Pizza)",
        "햄버거 (Hamburger)", "샌드위치 (Sandwich)", "파스타 (Pasta)",   
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

    detected_ingredients = {}  # {한글 식재료명: confidence score}
    low_confidence_boxes = []  # CLIP 보완 분석할 박스 저장
    yolo_detected = False  # YOLO 감지 여부

    # ✅ YOLO 감지 객체 분석
    for yolo_model, class_dict in [(yolo_model_food, food_classes), (yolo_model_fridge, fridge_classes)]:
        results = yolo_model(image_path, conf=0.1, iou=0.5)  # 신뢰도 0.1 이상 감지

        for result in results:
            for box in result.boxes:
                confidence = box.conf[0].item()  # 신뢰도 값
                class_id = int(box.cls[0])  # 클래스 ID
                class_name = yolo_model.names[class_id]

                # ✅ YOLO 클래스 ID를 한글 식재료명으로 변환
                label = class_dict.get(class_name, class_name)  # 한글 변환 (없으면 영어 그대로 유지)

                # ✅ 신뢰도 기준 처리
                if confidence >= 0.4:  # YOLO 신뢰도 0.4 이상이면 CLIP 실행 X
                    detected_ingredients[label] = max(detected_ingredients.get(label, 0), confidence)
                else:
                    # 신뢰도가 0.4 미만이면 CLIP 보완 분석 실행
                    print(f"⚠️ YOLO 신뢰도 {confidence:.2f} (0.4 미만), CLIP으로 보완 분석...")
                    low_confidence_boxes.append((label, confidence, box))

                yolo_detected = True  # YOLO 감지 성공

    # ✅ CLIP 보완 분석 (YOLO 신뢰도 0.4 미만인 박스)
    for label, confidence, box in low_confidence_boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])  
        cropped_img = image.crop((x1, y1, x2, y2))

        # CLIP 분석 실행
        image_input = preprocess(cropped_img).unsqueeze(0).to(device)
        image_features = clip_model.encode_image(image_input).detach()
        similarity = (image_features @ text_features.T).softmax(dim=-1)

        for idx, conf in enumerate(similarity.squeeze(0).tolist()):
            if conf >= 0.5:  # ✅ CLIP 신뢰도 기준 0.5 이상
                ingredient_name = possible_labels[idx].split(" (")[0]  # 영어 부분 제거
                detected_ingredients[ingredient_name] = max(detected_ingredients.get(ingredient_name, 0), conf)
                print(f"✅ CLIP 보완 결과: {ingredient_name} (유사도 {conf:.2f})")

    # ✅ YOLO가 감지한 객체가 없을 경우, CLIP으로 전체 이미지 분석
    if not yolo_detected:
        print("⚠️ YOLO가 감지한 식재료 없음, CLIP으로 전체 이미지 분석...")

        grid_size = 150  # Grid 단위 설정
        for y in range(0, image_height, grid_size):
            for x in range(0, image_width, grid_size):
                grid_img = image.crop((x, y, min(x + grid_size, image_width), min(y + grid_size, image_height)))

                image_input = preprocess(grid_img).unsqueeze(0).to(device)
                image_features = clip_model.encode_image(image_input).detach()
                similarity = (image_features @ text_features.T).softmax(dim=-1)

                for idx, conf in enumerate(similarity.squeeze(0).tolist()):
                    if conf >= 0.5:  # ✅ CLIP 신뢰도 기준 0.5 이상
                        ingredient_name = possible_labels[idx].split(" (")[0]  # 영어 부분 제거
                        detected_ingredients[ingredient_name] = max(detected_ingredients.get(ingredient_name, 0), conf)
                        print(f"✅ CLIP 분석 결과: {ingredient_name} (유사도 {conf:.2f})")

    # ✅ CLIP 보완 분석 수행 후, 신뢰도 0.6 미만인 항목 제거
    detected_ingredients = {k: v for k, v in detected_ingredients.items() if v >= 0.6}

    # ✅ 모든 재료를 한글로 변환 & 중복 제거
    final_ingredients = set()
    for ing in detected_ingredients.keys():
        # ✅ 최종 감지된 재료 리스트에서 중복을 확실히 제거
        final_ingredients = {food_classes.get(ing, fridge_classes.get(ing, ing)) for ing in detected_ingredients.keys()}

    print(f"📌 최종 감지된 재료 리스트: {sorted(final_ingredients)}")  # 🔥 중복 제거 후 정렬

    return sorted(final_ingredients)  # ✅ 최종 한글 재료명 리스트 반환

if __name__ =="__main__":
    image_path = input("이미지 경로를 입력하세요: ").strip()
    detect_ingredients(image_path)