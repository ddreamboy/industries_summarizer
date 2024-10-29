import os
import json
import asyncio
import logging
from urllib.parse import urlparse
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.runnables import RunnableSequence
from aiofiles import open as aio_open
from .get_root_project_dir import get_project_root


# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Logging setup
logging.basicConfig(
    filename='logs/summarizer.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Set environment variable USER_AGENT
os.environ['USER_AGENT'] = (
    'Mozilla/5.0 (Windows NT 10.4; WOW64; en-US) AppleWebKit/537.2 '
    '(KHTML, like Gecko) Chrome/49.0.1521.155 Safari/536'
)


class Summarizer:
    def __init__(self, base_url: str = 'http://127.0.0.1:11434', 
                 max_concurrent_tasks: int = 2, need_save_summary: bool = True):
        self.base_url = base_url
        self.llm_chain = self.setup_summarization_chain()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.need_save_summary = need_save_summary
        self.processed_links_file = os.path.join(
            get_project_root(), 'summarized_sources', 'processed_links.json'
        )
        self.processed_links = self.load_processed_links()
        self.total_links = 0
        self.summarized_links = 0

    def setup_summarization_chain(self) -> RunnableSequence:
        prompt_template = PromptTemplate(
            template=(
                'As an industry-specific summarizer, create a concise summary of the '
                'provided content with 2-3 sentences, tailored for RND platform analysis. '
                'Focus on these aspects:\n\n'
                '1. Identify if the source is relevant for industry: "{industry}".\n'
                '2. Explain briefly why this source is valuable or why it may not meet '
                'quality criteria.\n'
                '3. Prioritize industry-focused insights, case studies, and regulatory or '
                'research relevance.\n\n'
                'For rejected sources, note any major reasons for unsuitability. Format as '
                'structured responses with answers to these predefined questions:\n\n'
                '1. Is this a reliable source for {industry}? (Yes/No)\n'
                '2. Key strengths or limitations:\n'
                '3. Primary topics covered:\n\n'
                'Conclude with [End of Summary, Message #X]. Generate output as markdown.\n\n'
                '"{text}"\n\n'
                'SUMMARY:'
            ),
            input_variables=['text', 'industry'],
        )

        llm = ChatOllama(model='llama3:instruct', base_url=self.base_url)
        llm_chain = RunnableSequence(prompt_template, llm)
        return llm_chain

    def load_processed_links(self) -> dict:
        if os.path.exists(self.processed_links_file):
            with open(self.processed_links_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_processed_link(self, url: str, industry: str, filepath: str) -> None:
        if industry not in self.processed_links:
            self.processed_links[industry] = {}
        self.processed_links[industry][url] = filepath
        with open(self.processed_links_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_links, f, ensure_ascii=False, indent=2)

    async def load_document(self, url: str) -> str:
        try:
            loader = WebBaseLoader(url)
            return loader.load()
        except Exception as e:
            logging.error(f'Error loading document from {url}: {e}')
            return None

    async def summarize(self, url: str, industry: str) -> str:
        docs = await self.load_document(url)
        if docs is None:
            return None
        try:
            result = self.llm_chain.invoke({'text': docs, 'industry': industry})
            summary = result.content
            if self.need_save_summary:
                await self.save_summary(url, industry, summary)
            return summary
        except Exception as e:
            logging.error(f'Error summarizing document from {url}: {e}')
            return None

    def extract_name_from_url(self, url: str) -> str:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    async def save_summary(self, url: str, industry: str, summary: str) -> None:
        try:
            root_directory = os.path.join(get_project_root(), 'summarized_sources')
            industry_directory = os.path.join(root_directory, industry)
            os.makedirs(industry_directory, exist_ok=True)
            filename = f'{self.extract_name_from_url(url)}.md'
            filepath = os.path.join(industry_directory, filename)

            async with aio_open(filepath, 'w', encoding='utf-8') as f:
                await f.write(f'URL: {url}\n\n{summary}')

            relative_filepath = os.path.relpath(filepath, get_project_root())
            self.save_processed_link(url, industry, relative_filepath)
        except Exception as e:
            logging.error(f'Error saving summary for {url}: {e}')

    async def process_url(self, url: str, industry: str, progress_bar) -> str:
        if url in self.processed_links.get(industry, {}):
            progress_bar.set_postfix_str(f'URL already processed: {url}')
            progress_bar.update(1)
            return

        async with self.semaphore:
            progress_bar.set_postfix_str(f'Processing: {url}')
            summary = await self.summarize(url, industry)
            if summary is not None and self.need_save_summary:
                await self.save_summary(url, industry, summary)
                self.summarized_links += 1
            progress_bar.update(1)
            return summary