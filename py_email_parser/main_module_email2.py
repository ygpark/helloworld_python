import email
import hashlib
import socket
import geoip2.database
import json
import os
import re
from urllib.parse import urlparse
import requests
import asyncio
import aiofiles
import aiohttp
from urllib.parse import unquote

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
filepath = os.path.join(dirname, 'f.eml')
download_dir = os.path.join(dirname, 'downloads')
geolite2_filepath = os.path.join(dirname, 'GeoLite2-Country.mmdb')

async def download_file(url, session, download_dir):
    async with session.get(url) as response:
        if response.status == 200:
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                # 먼저 filename*= 형태로 인코딩된 파일명을 찾습니다.
                filename_match = re.findall(r'filename\*=[^\'\']+\'\'(.*?)$', content_disposition, flags=re.IGNORECASE)
                if filename_match:
                    file_name = unquote(filename_match[0])
                else:
                    # filename*= 형태가 없으면 filename= 형태의 파일명을 사용합니다.
                    filename_match = re.findall(r'filename="([^"]+)"', content_disposition)
                    file_name = filename_match[0] if filename_match else url.split('/')[-1]
            else:
                file_name = url.split('/')[-1]

            # 파일 경로에서 유효하지 않은 문자 제거
            file_name = re.sub(r'[\\/*?:"<>|]', "", file_name)
            file_path = os.path.join(download_dir, file_name)

            async with aiofiles.open(file_path, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await f.write(chunk)
            return file_path
        else:
            print(f"Failed to download {url}: Status {response.status}")
            return None

async def download_urls(urls, download_dir):
    async with aiohttp.ClientSession() as session:
        tasks = [download_file(url, session, download_dir) for url in urls]
        downloaded_files = await asyncio.gather(*tasks)
        return downloaded_files

def extract_urls(message_text):
    url_pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    urls = re.findall(url_pattern, message_text)
    unique_urls = set(urls)  # 중복 제거
    return [urlparse(url).geturl() for url in unique_urls]

def decode_header_value(header_value):
    if header_value is None:
        return ''

    decoded_parts = email.header.decode_header(header_value)
    decoded_value = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            if encoding is None:
                decoded_value += part.decode('utf-8')
            else:
                decoded_value += part.decode(encoding)
        else:
            decoded_value += part
    return decoded_value

def get_domain_name(ip_address):
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
        return hostname
    except:
        return None

def get_geo_info(ip_address):
    if is_valid_ip(ip_address):
        try:
            reader = geoip2.database.Reader(geolite2_filepath)
            response = reader.country(ip_address)
            return response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            return "Unknown"
    else:
        return "Invalid IP"

def is_valid_ip(ip_address):
    try:
        socket.inet_pton(socket.AF_INET, ip_address)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip_address)
            return True
        except socket.error:
            return False

async def read_file_async(file_path):
    async with aiofiles.open(file_path, mode='r') as f:
        return await f.read()

async def fetch_url_async(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def process_email_async(file_path):
    email_content = await read_file_async(file_path)
    
    # 이메일 내용 처리 로직 추가
    msg = email.message_from_string(email_content)

    # 이메일 메시지 정보 추출
    subject = decode_header_value(msg['Subject'])
    from_address = decode_header_value(msg['From'])
    to_address = decode_header_value(msg['To'])
    cc_address = decode_header_value(msg['Cc'])

    # 이메일 본문 추출
    message_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset()
                message_text += part.get_payload(decode=True).decode(charset or 'utf-8')
    else:
        charset = msg.get_content_charset()
        message_text = msg.get_payload(decode=True).decode(charset or 'utf-8')

    # URL 추출
    urls = extract_urls(message_text)
    downloaded_files = await download_urls(urls, download_dir)
    print("Downloaded files:", downloaded_files)


    # 발신지 IP 주소 추출
    ip_info = {}
    
    # X-Originating-IP 헤더 확인
    if 'X-Originating-IP' in msg:
        for ip_address in msg['X-Originating-IP'].replace('[','').replace(']','').split(', '):
            domain_name = get_domain_name(ip_address)
            country = get_geo_info(ip_address)
            ip_info[ip_address] = {
                "header": "x-originating-ip",
                "domain": domain_name,
                "country": country
            }
    
    # Received 헤더 확인
    if 'Received' in msg:
        received_headers = msg.get_all('Received', [])
        for header in received_headers:
            for part in header.split(';'):
                if 'from' in part.lower() and 'by' in part.lower():
                    ip_address = part.split('[')[1].split(']')[0]
                    domain_name = get_domain_name(ip_address)
                    country = get_geo_info(ip_address)
                    ip_info[ip_address] = {
                        "header": "Received",
                        "domain": domain_name,
                        "country": country
                    }
    
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

    document = {
        'message_info': {
            'subject': subject,
            'from_address': from_address,
            'to_address': to_address,
            'cc_address': cc_address
        },
        'urls' : urls,
        'ip': ip_info,
        'attachments': attachments,
    }
    return document

    
async def main():
    result = await process_email_async(filepath)
    print(json.dumps(result, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
    