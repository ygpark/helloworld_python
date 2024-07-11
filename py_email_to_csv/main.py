import os
import csv
import email
from email.header import decode_header
import argparse
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime, parseaddr
import multiprocessing
import re
from email.parser import BytesParser
from email.policy import default

link_count = 20  # 링크 개수를 여기서 설정

def get_exclude_links_set_from_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exclude_links_file = os.path.join(current_dir, 'exclude_links.txt')
    # 파일에서 링크를 읽어 세트로 변환합니다
    with open(exclude_links_file, 'r') as file:
        return set(line.strip() for line in file if line.strip())


def decode_mime_words(encoded_string):
    try:
        parts = decode_header(encoded_string)
        decoded_parts = []
        for word, encoding in parts:
            if isinstance(word, bytes):
                try:
                    decoded_parts.append(word.decode(encoding or 'utf-8'))
                except (LookupError, UnicodeDecodeError):
                    decoded_parts.append(word.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(word)
        return ' '.join(decoded_parts)
    except Exception as e:
        print(f"Error decoding: {encoded_string}. Error: {str(e)}")
        return encoded_string

def extract_links(html_content):
    link_pattern = r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"'
    return re.findall(link_pattern, html_content, re.IGNORECASE)

def parse_email(file_path):
    try:
        with open(file_path, 'rb') as f:
            parser = BytesParser(policy=default)
            msg = parser.parse(f)
        
        subject = decode_mime_words(msg.get('Subject', ''))
        from_addr = decode_mime_words(msg.get('From', ''))
        to_addr = decode_mime_words(msg.get('To', ''))
        cc = decode_mime_words(msg.get('Cc', ''))
        bcc = decode_mime_words(msg.get('Bcc', ''))
        
        from_name, from_email = parseaddr(from_addr)
        from_name = decode_mime_words(from_name)
        from_email = decode_mime_words(from_email)

        to_name, to_email = parseaddr(to_addr)
        to_name = decode_mime_words(to_name)
        to_email = decode_mime_words(to_email)
        
        send_time = ''
        if msg.get('Date'):
            try:
                send_time = parsedate_to_datetime(msg.get('Date')).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                send_time = msg.get('Date', '')

        receive_time = ''
        received_header = msg.get('Received', '')
        if received_header:
            try:
                receive_time = parsedate_to_datetime(received_header.split(';')[-1].strip()).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                receive_time = received_header.split(';')[-1].strip()

        originating_ip = ''
        if not '@gmail.com' in from_email.lower():
            originating_ip = msg.get('X-Originating-IP', '').replace('[','').replace(']','')

        exclude_links = get_exclude_links_set_from_file()
        
        download_links = []
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                links = extract_links(html_content)
                download_links = [
                    link for link in links 
                    if not any(exclude in link.lower() for exclude in exclude_links)
                ][:link_count]
                break
        
        download_links.extend([''] * (link_count - len(download_links)))
        
        folder_name = os.path.basename(os.path.dirname(file_path))
        file_name = os.path.basename(file_path)
        
        return [folder_name, file_path, file_name, subject, from_name, from_email, to_name, to_email, cc, bcc, send_time, receive_time, originating_ip] + download_links
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return [os.path.basename(os.path.dirname(file_path)), '', '', '', '', '', '', '', ''] + [''] * link_count

def process_directory(directory):
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.eml'):
                file_path = os.path.join(root, file)
                results.append(parse_email(file_path))
    return results

def process_chunk(chunk):
    return [parse_email(file_path) for file_path in chunk]

def start_analysis(start_directory, output_file_path):
    parser = argparse.ArgumentParser(description='Analyze .eml files and output to CSV')
    parser.add_argument('-d', '--directory', help='Working directory path')
    args = parser.parse_args()

    working_directory = args.directory if args.directory else start_directory

    file_paths = []
    for root, _, files in os.walk(working_directory):
        for file in files:
            if file.endswith('.eml'):
                file_paths.append(os.path.join(root, file))

    if not file_paths:
        print(f"No .eml files found in {working_directory}")
        return

    cpu_count = multiprocessing.cpu_count()
    chunk_size = max(1, len(file_paths) // cpu_count)
    chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]

    with multiprocessing.Pool(processes=cpu_count) as pool:
        results = pool.map(process_chunk, chunks)

    flattened_results = [item for sublist in results for item in sublist]

    with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = ['폴더 이름', 'Path', 'File Name', '제목', 'From Name', 'From Email', 'To Name', 'To Email', 'CC', 'BCC', 'Send Time', 'Receive Time', '발신IP'] + [f'링크{i}' for i in range(1, link_count + 1)]
        writer.writerow(headers)
        writer.writerows(flattened_results)

    print(f"분석이 완료되었습니다. 결과는 {output_file_path}에 저장되었습니다.")

def main():
    output_path = r"/path/to/output/"
    target_path1 = r"/path/to/eml/"
    
    start_analysis(target_path1, os.path.join(output_path, 'output.csv'))
 

if __name__ == '__main__':
    main()