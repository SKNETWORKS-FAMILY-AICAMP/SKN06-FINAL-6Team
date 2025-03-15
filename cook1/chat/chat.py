import os
from chat.lcel.lcel import mkch
from chat.utils.memories import mkhisid
from chat.utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수

def chat(user_id):
    print("Chatbot이 시작되었습니다!")  # 디버깅용

    history_id = mkhisid(user_id)
    cchain = mkch()

    while True:
        query = input("텍스트 또는 이미지 입력 > ")
        if query.lower() == "종료":
            break

        input_parts = query.split()
        detected_ingredients = set()  # 감지된 재료 저장
        text_input = []  # 텍스트 입력 저장

        for part in input_parts:
            if os.path.exists(part) and part.lower().endswith((".jpg", ".jpeg", ".png")):
                print(f"🖼 이미지 감지 중... ({part})")
                detected_ingredients.update(detect_ingredients(part))  # 감지된 재료 업데이트
            else:
                text_input.append(part)

        # ✅ 감지된 식재료 리스트 출력 (중복 제거 후 정렬)
        detected_ingredients = sorted(detected_ingredients)
        if detected_ingredients:
            print("\n📌 재료 리스트 (보이는 범위 내)")
            print(" / ".join(detected_ingredients))

        # ✅ 최종 Query 구성 (이미지에서 감지된 재료 + 사용자가 입력한 텍스트)
        combined_query = " ".join(text_input)
        query_with_ingredients = f"{combined_query} 감지된 재료: {', '.join(detected_ingredients)}" if detected_ingredients else combined_query


        # 🔥 LLM에 질문을 전달하여 요리 추천 받기
        res = cchain.stream(
            {"question": query_with_ingredients},
            config={"configurable": {"user_id": user_id, "history_id": history_id}}
        )

        print("AI: ", end="", flush=True)
        for chunk_gen in res:
            for chunk in chunk_gen:
                print(chunk.content, end="", flush=True)  # 실시간 출력
        print()  # 줄 바꿈

chat("test_user")