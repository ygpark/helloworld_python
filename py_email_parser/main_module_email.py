import email
from email import policy
from email.parser import BytesParser
from email.header import decode_header
import os

# 파일 경로 설정
filepath = os.path.join(os.getcwd(), 'a.eml')

# 바이트로 파일 열기
with open(filepath, 'rb') as email_file:
    # 바이트 파서와 정책 설정으로 이메일 메시지 파싱
    email_message = BytesParser(policy=policy.default).parse(email_file)

# 이메일 헤더 출력
for header, value in email_message.items():
    decoded_header = decode_header(value)
    header_value = ' '.join(
        str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0])
        for t in decoded_header
    )
    print(header, ':', header_value)

# 멀티파트 이메일 처리
if email_message.is_multipart():
    for part in email_message.walk():
        content_type = part.get_content_type()
        filename = part.get_filename()
        if filename:
            # 파일명의 인코딩 문제 해결
            decoded_filename = decode_header(filename)
            # 파일명 정확히 출력
            filename = ' '.join(
                str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else str(t[0])
                for t in decoded_filename
            )
            print("Filename:", filename)
        # print("Content Type:", content_type)
        # 헤더 일부 출력
        # print("Header Snippet:", part.as_string()[:50])

        # HTML 컨텐츠의 경우 예시 처리
        if content_type == 'text/html':
            message = part.get_payload(decode=True)
            print(message.decode('utf-8'))  # UTF-8로 디코딩하여 출력
