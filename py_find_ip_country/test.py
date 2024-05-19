from ipwhois import IPWhois

def get_whois_info(ip_address):
    obj = IPWhois(ip_address)
    result = obj.lookup_whois()
    return result

def get_description(whois_info):
    rst = []
    for net in whois_info.get('nets', []):
        description = net.get('description')
        if description and description != None:
            rst.append(description)
    return rst

if __name__ == '__main__':
    ip_address = '118.39.10.109'  # 조회할 IP 주소
    whois_info = get_whois_info(ip_address)
    print(get_description(whois_info))


