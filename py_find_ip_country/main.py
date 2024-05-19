import re
import socket
import geoip2.database
from concurrent.futures import ThreadPoolExecutor
import whois
from ipwhois import IPWhois

def check_socket(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, 80))
    sock.close()

    if result == 0:
        return True
    else:
        return False

def get_whois_info(ip_address):
    obj = IPWhois(ip_address)
    result = obj.lookup_whois()
    return result

def extract_names1(whois_info):
    names_list = []
    if whois_info is None:
        return names_list

    nir_info = whois_info.get('nir', {})
    
    if nir_info is None:
        return names_list
    
    nets_info = nir_info.get('nets', [])
    for net in nets_info:
        if isinstance(net, dict):
            name = net.get('name')
            if name:
                names_list.append(name)
    return names_list


def extract_names(whois_info):
    names_list = []
    if whois_info is None:
        return names_list

    nets_info = whois_info.get('nets', [])
    for net in nets_info:
        if isinstance(net, dict):
            name = net.get('description')
            if name and name[0] != '*':
                names_list.append(name[0:20])
    return names_list

def remove_brackets_from_ip(content):
    modified_content = content.replace('[.]', '.')
    return modified_content

def extract_ip_countries(filename):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    reader = geoip2.database.Reader('GeoLite2-Country.mmdb')

    with open(filename, 'r') as file:
        data = file.read()

    data = remove_brackets_from_ip(data)

    ip_addresses = re.findall(ip_pattern, data)
    visited_ips = set()
    kr_ips = set()  # 한국(KR) IP 주소를 저장할 세트

    def process_ip(ip):
        if ip not in visited_ips:
            is_alive = check_socket(ip)
            try:
                country = reader.country(ip)
                whois_info = get_whois_info(ip)
                print(f'IP 주소: {ip.ljust(30)}, ({country.country.iso_code})\t, 활성: {is_alive}\t, 통신사: {extract_names(whois_info)}')
                if is_alive and country.country.iso_code == 'KR':  # 한국(KR) 아이피 주소인 경우
                    kr_ips.add(f'IP 주소: {ip.ljust(30)}, ({country.country.iso_code})\t, 활성: {is_alive}\t, 통신사: {extract_names(whois_info)}')
                visited_ips.add(ip)
            except Exception as e:
                print(f'IP 주소: {ip.ljust(30)}, \t (--) {e}')

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_ip, ip_addresses)

    # 한국(KR) IP 주소 출력
    print('\n한국(KR) IP 주소:')
    sorted_kr_ips = sorted(kr_ips)  # IP 주소를 정렬
    for ip in sorted_kr_ips:
        print(ip)


if __name__ == '__main__':
    target_file = 'target.txt'
    extract_ip_countries(target_file)
