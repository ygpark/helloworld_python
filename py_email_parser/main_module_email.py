import email
import hashlib
import os
import json
# from pymongo import MongoClient

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
filepath = os.path.join(dirname, 'a.eml')

def process_eml_file(file_path):
    with open(file_path, 'r') as f:
        msg = email.message_from_file(f)

    # 이메일 메시지 정보 추출
    subject = msg['Subject']
    from_address = msg['From']
    to_address = msg['To']
    cc_address = msg['Cc']

    # 발신지 IP 주소 추출
    ip_addresses = []
    
    # X-Originating-IP 헤더 확인
    if 'X-Originating-IP' in msg:
        ip_addresses.extend(msg['X-Originating-IP'].split(', '))
    
    # Received 헤더 확인
    if 'Received' in msg:
        received_headers = msg.get_all('Received', [])
        for header in received_headers:
            for part in header.split(';'):
                if 'from' in part.lower() and 'by' in part.lower():
                    ip_address = part.split('[')[1].split(']')[0]
                    ip_addresses.append(ip_address)
    
    # X-Forwarded-For 헤더 확인
    if 'X-Forwarded-For' in msg:
        ip_addresses.extend(msg['X-Forwarded-For'].split(', '))
    
    # 기타 헤더 필드 확인
    for header in ['X-Remote-IP', 'X-Sender-IP', 'True-IP', 'Client-IP', 'Originating-IP']:
        if header in msg:
            ip_addresses.append(msg[header])

    # 첨부파일 정보 추출
    attachments = []
    for part in msg.walk():
        if part.get_filename():
            filename = part.get_filename()
            file_content = part.get_payload(decode=True)

            # 첨부파일 해시값 계산
            md5 = hashlib.md5(file_content).hexdigest()
            sha1 = hashlib.sha1(file_content).hexdigest()
            sha256 = hashlib.sha256(file_content).hexdigest()
            sha512 = hashlib.sha512(file_content).hexdigest()

            attachments.append({
                'filename': filename,
                'hash': {
                    'md5': md5,
                    'sha1': sha1,
                    'sha256': sha256,
                    'sha512': sha512
                }
            })

    # MongoDB에 데이터 저장
    # client = MongoClient('mongodb://localhost:27017/')
    # db = client['email_analysis']
    # collection = db['email_messages']

    document = {
        'ip': {
            'x-originating-ip': ip_addresses
        },
        'attachments': attachments,
        'message_info': {
            'subject': subject,
            'from_address': from_address,
            'to_address': to_address,
            'cc_address': cc_address
        }
    }
    # print(document)
    return document
    # collection.insert_one(document)

rst = process_eml_file(filepath)
print(json.dumps(rst, indent=4))