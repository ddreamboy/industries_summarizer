import concurrent.futures
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import logging
from .get_root_project_dir import get_project_root


# Create directory for logs if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Logging setup
logging.basicConfig(
    filename='logs/search_result_aggregator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


class SearchResultAggregator:
    def __init__(self, queries_filename: str, start: int = 3, stop: int = 6,
                 max_workers: int = 20, save_results: bool = True):
        self.queries_filename = (queries_filename if queries_filename.endswith('.json')
                                 else f'{queries_filename}.json')
        self.start = start
        self.stop = stop
        self.max_workers = max_workers
        self.save_results = save_results
        self.queries = self.load_queries()
        self.raw_sources_dir = get_project_root() / 'raw_sources'
        self.raw_sources_dir.mkdir(exist_ok=True)
        self.sources_path = self.raw_sources_dir / f'raw_sources_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    def save_to_json(self, data: dict, filename: str = None) -> None:
        filename = filename or self.sources_path
        try:
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                for industry, industry_data in data.items():
                    if industry in existing_data:
                        existing_data[industry].update(industry_data)
                    else:
                        existing_data[industry] = industry_data
                data = existing_data
            else:
                existing_data = data
        except json.JSONDecodeError:
            existing_data = data

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def load_queries(self) -> dict:
        queries_path = get_project_root() / 'search_queries'
        filename = queries_path / self.queries_filename
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f'No query file found: {self.queries_filename}')

    def get_search_results(self, query: str) -> list:
        url = f'https://www.google.com/search?q={query}&num={self.stop}&start={self.start}'
        headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/91.0.4472.124 Safari/537.36')
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            search_results = soup.find_all('div', class_='yuRUbf')
            links = [result.find('a')['href'] for result in search_results
                     if result.find('a')['href'].startswith('http')]
            return links[self.start:self.stop]
        return []

    def analyze_link(self, link: str) -> dict:
        try:
            response = requests.get(link, timeout=10)  # Set timeout to 10 seconds
            if response.history:
                logging.info(f'Link redirected to: {response.url}')
                link = response.url

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.find('title')
            title = title_tag.text if title_tag else 'Title not found'

            return {
                'link': link,
                'title': title,
            }

        except requests.exceptions.RequestException as e:
            logging.error(f'Error fetching data: {e}')
            return {'link': link, 'error': f'Error fetching data: {e}'}
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            return {'link': link, 'error': f'Unexpected error: {e}'}

    def process_query(self, industry: str, query: str) -> tuple:
        logging.info(f'Processing query: {query}')
        links = self.get_search_results(query)
        query_results = [self.analyze_link(link) for link in links] if links else []
        if not links:
            logging.warning('No search results found.')
        return query, query_results

    def run(self) -> dict:
        all_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for industry, queries_list in self.queries.items():
                logging.info(f'Processing industry: {industry}')
                future_to_query = {executor.submit(self.process_query, industry, query): query
                                   for query in queries_list}
                industry_results = {}
                for future in concurrent.futures.as_completed(future_to_query):
                    query = future_to_query[future]
                    try:
                        query, results = future.result()
                        industry_results[query] = results
                    except Exception as exc:
                        logging.error(f'{query} generated an exception: {exc}')
                all_results[industry] = industry_results
                if self.save_results:
                    self.save_to_json(all_results)
        logging.info('Processing completed.')
        return all_results

    def get_links_by_industry(self) -> dict:
        links_by_industry = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for industry, queries_list in self.queries.items():
                future_to_query = {executor.submit(self.get_search_results, query): query
                                   for query in queries_list}
                industry_links = []
                for future in concurrent.futures.as_completed(future_to_query):
                    query = future_to_query[future]
                    try:
                        links = future.result()
                        industry_links.extend(links)
                    except Exception as exc:
                        logging.error(f'{query} generated an exception: {exc}')
                links_by_industry[industry] = industry_links
        return links_by_industry

    def stream_links_by_industry(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for industry, queries_list in self.queries.items():
                future_to_query = {executor.submit(self.get_search_results, query): query
                                   for query in queries_list}
                for future in concurrent.futures.as_completed(future_to_query):
                    query = future_to_query[future]
                    try:
                        links = future.result()
                        for link in links:
                            yield industry, link
                    except Exception as exc:
                        logging.error(f'{query} generated an exception: {exc}')