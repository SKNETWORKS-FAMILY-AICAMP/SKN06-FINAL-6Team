import time
import pandas as pd

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

drv = webdriver.Chrome()

def name_link() -> pd.DataFrame:
    """
    사이트에서 이름과 영상 link를 가져오는 함수
    """
    url = "https://tv.jtbc.co.kr/vod/pr10010331/pm10031085"
    drv.get(url)

    df = pd.DataFrame(columns=["name", "video"])
    last = drv.find_elements(By.CSS_SELECTOR, ".clfix._pagination .last")[0].text
    for cnt in range(int(last)):
        name = drv.find_elements(By.CSS_SELECTOR, "#skip_pass .card_list.c_three_3line .txt .font18._dot-apply")
        vid = drv.find_elements(By.CSS_SELECTOR, "#skip_pass .card_list.c_three_3line li a")
        print(cnt, len(name), len(vid))
        for i in range(len(vid)):
            df = pd.concat([df, pd.DataFrame({'name': [name[i].text], 'video': [vid[i].get_attribute("href")]})], ignore_index=True)
        
        nextpage = drv.find_elements(By.CSS_SELECTOR, ".clfix._pagination .next")
        if nextpage:
            nextpage[0].click() # 다음 페이지 없으면 종료
        time.sleep(1)
    return df

def name_img() -> pd.DataFrame:
    """
    사이트에서 이름과 이미지를 가져오는 함수
    """
    url = "https://tv.jtbc.co.kr/vod/pr10010331/pm10031085/vo10333489/view"
    drv.get(url)

    df = pd.DataFrame(columns=["name", "img"])
    cnt = 0
    while True:
        name = drv.find_elements(By.CSS_SELECTOR, ".v_player_con .on strong")
        img = drv.find_elements(By.CSS_SELECTOR, "#jtbc-video-player video")
        df = pd.concat([df, pd.DataFrame({'name': [name[0].text], 'img': [img[0].get_attribute("poster")]})], ignore_index=True)
        
        print(cnt, end=" ")
        cnt += 1

        try:
            next_button = drv.find_elements(By.CSS_SELECTOR, ".clfix.ui_slider_item.current ._next-vod")[0] # 현 슬라이드에 다음 태그가 있는지 확인
            next_button.click()
        except IndexError:
            try:
                next_button = drv.find_elements(By.CSS_SELECTOR, ".clfix.ui_slider_item ._next-vod")[0] # 현재 슬라이드에 없을 경우 다음 슬라이드에서 next-voi 클래스 찾음
                next_button.click()
            except IndexError:
                print("더 이상 다음 비디오가 없습니다.") # 없을 경우 종료
                break
        time.sleep(1)
    return df

if __name__ == "__main__":
    imgdf = name_img()
    linkdf = name_link()
    df = pd.merge(imgdf, linkdf)
    df.to_csv("name-img-vid.csv")
    drv.quit()