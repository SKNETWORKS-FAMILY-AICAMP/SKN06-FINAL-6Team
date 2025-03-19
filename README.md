# SKN06-FINAL-6Team
강채연 김동훈 임연경 전수연 조해원

### 🧑‍🤝‍🧑 팀원

| 김동훈 | 조해원 | 강채연 | 전수연 | 임연경 |
|-------|------|------|------|------|
| <img src="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EA%B9%80%EB%8F%99%ED%9B%88.jpg" alt="image" width="250" height="250"/> | <img src="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EC%A1%B0%ED%95%B4%EC%9B%90.jpg" alt="image" width="250" height="250"/> | <img src="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EA%B0%95%EC%B1%84%EC%97%B0.jpg" alt="image" width="250" height="250"/> | <img src="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EC%A0%84%EC%88%98%EC%97%B0.jpg" alt="image" width="250" height="250"/> |  <img src="https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EC%9E%84%EC%97%B0%EA%B2%BD.png" alt="image" width="250" height="250"/> |
| 백엔드 | 프론트엔드  | 팀장  | 백엔드 | 프론트엔드 |

</br>

# 👩🏻‍🍳 레시피 추천 챗봇 🧑🏻‍🍳 (06. LLM활용 고객 상담 챗봇)

### ✔️ 개발 기간

2025.01.21 ~ 2025.03.20(38일간)

### ✔️ 개요
1. 자취생과 1인 가구 증가 : 혼자 생활하면서 겪는 어려움(요리, 식비 절약 등)에 대한 해결책이 필요하다
2. 요린이 : ‘요리+어린이=요린이’라는 신조어, 이들이 간단하고 쉽게 요리할 수 있는 솔루션이 필요하다
3. 배달 이용 증가 : 비용 부담과 건강 문제 때문에 단순히 배달에 의존하기보다, 이를 효율적으로 활용하거나 대체할 수 있는 방안이 필요하다

### ✔️ 목표

1인 가구와 자취생, 주부들을 위한 맞춤형 레시피 추천 챗봇을 개발하여 쉽고 건강한 식생활을 지원한다.

### ✔️ 프로젝트 내용
맞춤형 레시피 추천, 대화형 요리 가이드, 대체 재료 추천 및 트렌드 반영

</br>

#### ✔️ Stacks

![Discord](https://img.shields.io/badge/discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

![Python](https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
<img src="https://img.shields.io/badge/scikitlearn-%23F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white"/>

</br>

![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=Git&logoColor=white)
![Github](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white)

#### ✔️ Requirements


## 챗봇 이름 및 로고

  꾸깃꾸깃(Cook it, Cook Eat!)
  > 요리를 하고 맛있게 먹자!
  >
  > 냉장고 속 재료를 꾸깃꾸깃 활용!
  >
  > 요리 고민도 꾸깃꾸깃 접어두세요!
  >

## 경쟁 서비스
  ### 냉장고 파먹기
  주요기능
  > 즐겨찾기 기능 : 사용자가 원하는 레시피를 저장.
  >
  > 여러 식재료를 입력하면 레시피에 필요한 보유 재료와 부족한 재료를 구분하여 표시.
  >
  > 선택한 레시피를 클릭하면 ‘만개레시피’ 사이트로 이동하여 레시피 제공 (같은 메뉴의 다양한 레시피 확인)
  >
  > 검색 기능 : 특정 재료 또는 요리법 검색 가능.
  >

  단점 및 한계
  >만개레시피 사이트에서 가져오는 방식이므로 관련 없는 레시피가 함께 추천
  >
  
  ### 거꾸로 레시피
  주요기능
  > 북마크 기능: 사용자가 원하는 레시피를 저장.
  >
  > 한 가지 이상의 식재료를 입력하면 해당 재료 중 하나라도 포함된 레시피를 추천.
  >
  > 소비기한 알림: 음식물 쓰레기를 줄이는데 도움.
  >
  
  단점 및 한계
  > 아이폰에서만 사용 가능.
  >
  > 등록된 레시피 종류가 적음.
  >
  > 단순한 재료 매칭 기반으로 이루어져 사용자 맞춤형 추천 기능이 부족.
  >
  
  ### 냉장고 즉석 레시피
  주요기능
  > 사용자가 가진 재료를 입력하면 간단한 요리법부터 비건요리까지 추천.
  >
  > 업로드한 사진에서 재료를 인식해 요리 추천.
  >
  > 요리 과정 중 유용한 팁이나 셰프의 꿀팁 제공.
  >
  > ChatGPT 사이트를 통해 서비스를 하고 있어 GPT 기본 기능 사용 가능. (TTS, 예상 완성 이미지 생성해 제공)
  > 
  
  단점 및 한계
  > 리뷰 기능이 없어 사용자가 처음 보는 요리라면 맛에 대한 확신이 부족.
  >
  > 실제 요리 완성 사진이 아닌 생성된 요리 완성 이미지 제공.
  >

## 차별점
  기술적 차별화
  > AI 챗봇을 활용하여 실시간으로 사용자가 입력한 재료 분석 후, 레시피 추천
  >
  > “냉장고 속 재료” 기반의 개인 맞춤형 레시피 제공
  >
  
  사용자 경험 개선
  > 음성 입력 또는 사진 분석(재료 인식)으로 인터페이스 단순화
  >
  
  웹기반 플렛폼
  > 기존의 앱 기반 서비스와 달리 운영체제(OS) 제한 없이 접근 가능
  >
  
  사용자 참여형
  > 사용자들이 선택한 레시피에 대해 리뷰를 작성, 열람가능
  >

## 활용 방안 및 기대 효과
1. 사용자의 요리 고민 해결
> AI가 사용자 맞춤형 레시피를 추천하여 "오늘 뭐 먹지?"에 대한 고민을 덜어줍니다.
> 
2. 음식 낭비 방지 (남은 재료 활용 추천)
>냉장고 속 남은 재료를 활용한 맞춤형 요리를 추천하여 식재료 낭비를 줄입니다.
>
3. 요리 초보자도 쉽게 따라할 수 있는 요리 가이드
> AI 챗봇이 단계별 대화형 요리 가이드를 제공하여 누구나 쉽게 요리할 수 있도록 돕습니다.
> 
4. 맞춤형 서비스 제공으로 사용자 만족도 증가
> 개인 취향과 재료를 반영한 맞춤형 추천을 통해 사용자 경험을 향상시킵니다.
> 

## data 수집 및 전처리
### 수집데이터
1. 만개레시피
2. JTBC(냉장고를 부탁해)
3. 편스토랑

### 전처리
1. 만개레시피
> ingredients(재료) : 불용어 처리(구매)
> 
> name(요리명) : 띄어쓰기, 맞춤법, 요리명으로 이름 변경(돼지고기 김치찌개와 같이 특정 재료가 포함된 경우는 유지)
>
> ex) 맛있는 돼지 김치찌개 -> 돼지 김치찌개
> 
> intro(음식소개), recipe(조리순서) : 띄어쓰기, 맞춤법, 어체 수정("~합니다." 또는 "~하세요")
>

2. JTBC(냉장고를 부탁해)
> name(요리명) : 불용어 처리(~의), 요리사 이름 일치     ex) '샘 킴'-> '샘킴'
>
> ingredients(재료) :불용어 처리(재료, 특수문자), 공백 추가하여 가독성 향상
>
> recipe(조리순서) : 불용어 처리(조리방법), 공백을 추가해 가독성 향상
>
> img, video : 결측치 처리('no img', 'no video')
>

3. 편스토랑
> name(요리명) : 불용어 처리(해당 회차 번호, HTML 엔터키) , '이름 - 요리' 레시피 형태로 정제, 중복 데이터 삭제
> 
> ingredients(재료) : 불용어 처리(개행문자, 공백, 특수문자), 각 재료별 문장 형태 일치
> 
> recipe(조리순서) : 불용어 처리(특수문자, 불필요한 공백, 불필요한 문장 - 해당 레시피는 편스토랑 인스타그램에도 확인할 수 있습니다.)
>

## 와이어프레임
![image](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/%EC%99%80%EC%9D%B4%EC%96%B4%ED%94%84%EB%A0%88%EC%9E%84.png)
## DB설계 
![image](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN06-FINAL-6Team/blob/main/%EC%B5%9C%EC%A2%85%ED%8F%89%EA%B0%80%20%EC%82%B0%EC%B6%9C%EB%AC%BC/readme%20%EC%82%AC%EC%A7%84/DB%20Table.png)
## 화면 설계
|home화면|채팅화면|
|---|---|


## 팀원 회고
김동훈
> ㅇㅇ
>
조해원
> ,,,
>
강채연
> 주어진 시간도 짧았지만 특히 마지막 3주간은 학교와 병행하며 프로젝트에 적극적으로 참여하지 못한 점이 아쉽고 팀장으로서 죄송합니다. 또 어려움이 많았지만 개인 시간을 할애하는 것까지 마다하지 않으며 열심히 참여해주신 모든 팀원 분들께 감사합니다. 이번 프로젝트를 통해 기획 단계에서부터 구현 가능한 항목에 대해 세부적으로 체크해야하는 것의 중요성을 깨달았고, LLM 사용 프로젝트에서 가장 중요한 점은 모델의 동작 방식을 명확히 이해하여 프롬프트 엔지니어링을 수행하는 과정인 것 같습니다. 프롬프트 엔지니어링 과정 중에 이전에 작업했던 항목들로 돌아가야할 수도 있음을 인지하고 충분한 시간을 확보하고 작업해야겠습니다.
>
전수연
> ㅇ
> 
임연경
> ㅇㅇ
>
