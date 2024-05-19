import re
import asyncio
import geoip2.database
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import whois
from ipwhois import IPWhois

async def resolve_domain(domain):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{domain}') as response:
                ip_address = socket.gethostbyname(domain)
                return ip_address
    except Exception as e:
        print(f'Error resolving domain {domain}: {e}')
        return None

# 이하 동일한 코드

async def main():
    target_file = 'target.txt'
    domain_pattern = r'\b(?:https?://)?(?:www\.)?([^/\n\s]+)'
    reader = geoip2.database.Reader('GeoLite2-Country.mmdb')

    with open(target_file, 'r') as file:
        data = file.read()

    domains = re.findall(domain_pattern, data)
    ip_addresses = await asyncio.gather(*(resolve_domain(domain) for domain in domains if domain))

    visited_ips = set()
    kr_ips = set()  # 한국(KR) IP 주소를 저장할 세트

    def process_ip(ip):
        if ip and ip not in visited_ips:
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
    asyncio.run(main())
