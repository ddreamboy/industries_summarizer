from urllib.parse import urlparse
import os
import re
from datetime import datetime
from typing import Dict, List, Optional


def extract_name_from_url(url: str) -> str:
    '''Extracts the domain name from a URL.'''
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain[4:] if domain.startswith('www.') else domain


def parse_line(line: str, pattern: str) -> Optional[str]:
    '''Extracts a value from a string using a regular expression.'''
    match = re.search(pattern, line)
    return match.group(1) if match else None


def process_file(filepath: str) -> Dict[str, Optional[str]]:
    '''Processes a file and extracts data.'''
    data = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()
        for line in content:
            if '"url"' in line:
                data['url'] = parse_line(line, r'"url": "(https?://[^"]+)"')
            if '"reliable"' in line:
                data['reliable'] = parse_line(line, r'"reliable": "(Yes|No)"')
            if '"reason"' in line:
                data['reason'] = parse_line(line, r'"reason": "([^"]+)"')
    return data


def process_reports(industry: str) -> None:
    '''Processes reports for a given industry and saves the final report.'''
    folder_path = os.path.join('reports', industry, 'for_each_summary')
    timestamp = datetime.now().strftime(r'%Y%m%d_%H%M%S')
    output_file = os.path.join('reports', industry, f'{industry}_total_report_{timestamp}.md')

    if not os.path.exists(folder_path):
        print(f'Directory {folder_path} does not exist. Skipping processing for industry {industry}.')
        return

    selected_sources: List[Dict[str, str]] = []
    rejected_sources: List[Dict[str, str]] = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            filepath = os.path.join(folder_path, filename)
            data = process_file(filepath)
            url = data.get('url', '')
            if url:
                pretty_url = f'[{extract_name_from_url(url)}]({url})'
                source = {'url': pretty_url, 'reason': data.get('reason', '')}
                if data.get('reliable') == 'Yes':
                    selected_sources.append(source)
                else:
                    rejected_sources.append(source)

    report = generate_report(selected_sources, rejected_sources, industry)
    save_report(output_file, report)
    print(f'Report successfully created in file {output_file}')


def generate_report(selected_sources: List[Dict[str, str]],
                    rejected_sources: List[Dict[str, str]],
                    industry: str) -> str:
    '''Makes a report in Markdown format.'''
    industry = ' '.join(industry.split('_')).capitalize()
    report = f'## Report on information source search for RND platform in the {industry} industry**\n\n'
    report += f'### **Selected sources ({len(selected_sources)}):**\n\n| **Source** | **Reasons for selection** |\n|---|---|\n'
    for source in selected_sources:
        report += f'| {source["url"]} | {source["reason"]} |\n'

    report += f'\n\n### **Rejected sources ({len(rejected_sources)}):**\n\n| **Source** | **Reasons for rejection** |\n|---|---|\n'
    for source in rejected_sources:
        report += f'| {source["url"]} | {source["reason"]} |\n'

    return report


def save_report(filepath: str, report: str) -> None:
    '''Saves the report to a file.'''
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(report)


def main() -> None:
    '''Main function to process reports for predefined industries.'''
    industries = ['venture_capital', 'document_automation']
    for industry in industries:
        process_reports(industry)


if __name__ == '__main__':
    main()
