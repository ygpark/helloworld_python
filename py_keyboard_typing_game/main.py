import os
import re

def clean_text(text):
    # 띄어쓰기 2개 이상을 1개로 바꾸는 정규표현식
    cleaned_text = re.sub(r'\s+', ' ', text)
    return cleaned_text

def typing_practice(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        content = clean_text(content)  # 띄어쓰기 정리
        start = 0
        while start < len(content):
            end = start + 80
            print(content[start:end], end='')  # 줄바꿈 제거
            print()
            user_input = input("")
            start = end
            # 사용자 입력과 비교하여 다음 80글자 출력 로직은 여기에 추가하세요.
            # 사용자 입력이 일치하는지 확인하고, 일치하지 않는 경우 오류 메시지 출력 등을 구현할 수 있습니다.

file_path = os.path.join(os.getcwd(), 'a.txt')
typing_practice(file_path)