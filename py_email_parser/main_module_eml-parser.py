import datetime
import json
import eml_parser
import os
import re
import ipaddress
import socket
import datetime
from functools import lru_cache
import subprocess

filepath = os.path.join(os.getcwd(), 'c.eml')

def nslookup(ip_address):
    try:
        host_info = socket.gethostbyaddr(ip_address)
        return host_info[0]  # 호스트 이름 반환
    except socket.herror as e:
        return None

@lru_cache(maxsize=None)
def ip_to_domain(ip):
    try:
        if is_private_ip(ip) is True:
            return None

        domain = nslookup(ip)
        # domain = socket.gethostbyaddr(ip)
        return domain
    except socket.herror:
        return None
    except socket.timeout:
        return None
    
# 캐시된 결과의 유효성을 확인하여 날짜가 변경되었는지 검사
def is_cache_valid():
    last_refreshed = getattr(ip_to_domain, 'last_refreshed', None)
    if last_refreshed is None:
        return False
    today = datetime.date.today()
    return last_refreshed.date() == today

# 캐시를 갱신
def refresh_cache():
    ip_to_domain.cache_clear()
    ip_to_domain.last_refreshed = datetime.datetime.now()

# 함수 호출 전에 캐시의 유효성을 검사하고, 필요한 경우 캐시를 갱신
def cached_ip_to_domain(ip):
    if not is_cache_valid():
        refresh_cache()
    return ip_to_domain(ip)

def domain_to_ip(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.gaierror:
        return None
    

    
def is_private_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False

def get_tag(ip_str):
    tag = ''
    if is_private_ip(ip_str):
        tag += ' [Private IP] '

    domain = ip_to_domain(ip_str)
    if domain:
        tag += f' [{domain}] '
    return tag

def is_valid_ipv4(ip_str):
    # IP 주소를 확인하는 정규식 패턴
    ip_pattern = r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
    
    # 주어진 문자열이 IP 주소 패턴과 일치하는지 확인
    if re.match(ip_pattern, ip_str):
        return True
    else:
        return False

def is_valid_ipv6(ip_str):
    # IPv6 주소를 확인하는 정규식 패턴
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    
    # 주어진 문자열이 IPv6 주소 패턴과 일치하는지 확인
    if re.match(ipv6_pattern, ip_str):
        return True
    else:
        return False

def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()



with open(filepath, 'rb') as fhdl:
    raw_email = fhdl.read()

ep = eml_parser.EmlParser(include_raw_body=True, include_attachment_data=True)

parsed_eml = ep.decode_email_bytes(raw_email)


# 이메일 본문을 출력합니다.
print(parsed_eml['body'][0]['content'])

# print("첨부 파일:")

for file in parsed_eml.get('attachment', []):
    print(f'attachment: ' + file['filename'] + f" (md5: {file['hash']['md5']})")

# if 'attachment' in parsed_eml:
#     for file in parsed_eml['attachment']:
#         print(f'attachment: ' + file['filename'] + f" (md5: {file['hash']['md5']})")

if 'x-originating-ip' in parsed_eml['header']['header']:
    for ip_str in parsed_eml['header']['header']['x-originating-ip']: 
        ip_str = ip_str.replace('[','').replace(']','')
        print('발신지IP: ' + ip_str + get_tag(ip_str))

if 'x-hanmail-peer-ip' in parsed_eml['header']['header']:
    for ip_str in parsed_eml['header']['header']['x-hanmail-peer-ip']: 
        print('발신지IP: ' + ip_str + get_tag(ip_str))

if 'received_ip' in parsed_eml['header']:
    for ip_str in parsed_eml['header']['received_ip']:
        if is_valid_ipv4(ip_str) or is_valid_ipv6(ip_str):
            print('경유지IP: ' + ip_str + get_tag(ip_str))
# print()

# print("헤더:")
# print(parsed_eml['header'])
