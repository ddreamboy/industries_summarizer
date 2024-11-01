import os
import asyncio
import logging
from tqdm.asyncio import tqdm
from scripts.search_results_aggregator import SearchResultAggregator
from scripts.summarizer import Summarizer
from scripts.report_generator import ReportGenerator
from scripts.report_parser import process_reports

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Logging setup
logging.basicConfig(
    filename='logs/main.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

async def process_links(
    aggregator: SearchResultAggregator, 
    summarizer: Summarizer, 
    report_generator: ReportGenerator,
    industry: str
) -> None:
    logging.info('Start processing links')
    
    links = list(aggregator.stream_links_by_industry())
    summarizer.total_links = len(links)
    logging.info(f'Found {summarizer.total_links} links to process')

    progress_bar = tqdm(total=summarizer.total_links, desc='Processing links', unit='link')

    tasks = []
    for industry, link in links:
        logging.info(f'Creating task for link: {link} (industry: {industry})')
        task = asyncio.create_task(summarizer.process_url(link, industry, progress_bar))
        tasks.append(task)
    
    # Wait for all tasks to complete with exception handling
    await asyncio.gather(*tasks, return_exceptions=True)
    
    summaries = report_generator.load_summaries(industry)
    report_generator.generate_report(summaries, industry)
    process_reports(industry)

    logging.info('Link processing completed')
    progress_bar.close()


async def main() -> None:
    industry = 'sales_industry'
    aggregator = SearchResultAggregator(
        queries_filename=industry, start=3, stop=6, max_workers=20
    )
    summarizer = Summarizer(max_concurrent_tasks=3, need_save_summary=True)
    report_generator = ReportGenerator()
    await process_links(aggregator, summarizer, report_generator, industry)

if __name__ == '__main__':
    asyncio.run(main())
