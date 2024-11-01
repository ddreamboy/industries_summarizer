import os
from tqdm import tqdm
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from .report_parser import process_reports


class ReportGenerator:
    def __init__(self, base_url: str = 'http://127.0.0.1:11434'):
        """
        Initializes the ReportGenerator with a base URL for the language model API.

        Args:
            base_url (str): The base URL for the language model API.
        """
        self.base_url = base_url
        self.llm = ChatOllama(model='llama3:instruct', base_url=self.base_url)
        self.prompt_template = PromptTemplate(
            template=(
                'Analyze the following summary and decide whether the source should '
                'be approved or rejected for this task TASK - "1. Identify if the '
                'source is relevant for industry: {industry}. 2. Explain briefly why '
                'this source is valuable or why it may not meet quality criteria. 3. '
                'Prioritize industry-focused insights, case studies, and regulatory '
                'or research relevance.\n\nFor rejected sources, note any major '
                'reasons for unsuitability. Format as structured responses with '
                'answers to these predefined questions:\n\n1. Is this a reliable '
                'source for {industry}? (Yes/No) Strictly adhere to the structure of '
                'the formation of .json dictionary, you should always have 1 json '
                'dictionary with url, reliable and reason, never more, without '
                'comments, just 1 json dictionary with url, reliable and reason.\n\n'
                'Summary:\n"{summary}"\n\nPast Reports:\n"{report_template}"'
            ),
            input_variables=['summary', 'report_template', 'industry']
        )

    def process_summary(self, summary: str, report_template: str, industry: str) -> str:
        """
        Processes a summary using the language model to generate a report.

        Args:
            summary (str): The summary to be analyzed.
            report_template (str): The template for the report.
            industry (str): The industry for which the summary is being analyzed.

        Returns:
            str: The generated report.
        """
        prompt = self.prompt_template.format(
            summary=summary, report_template=report_template, industry=industry
        )
        result = self.llm.invoke(prompt)
        report = result.content
        return report

    def load_summaries(self, industry: str) -> list:
        """
        Loads summaries from markdown files for a given industry.

        Args:
            industry (str): The industry for which summaries are to be loaded.

        Returns:
            list: A list of tuples containing filenames and their corresponding summaries.
        """
        directory = os.path.join('summarized_sources', industry)
        summaries = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith('.md'):
                    with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                        summary = f.read()
                    summaries.append((filename, summary))
        return summaries

    def generate_report(self, summaries: list, industry: str) -> None:
        """
        Generates reports for a list of summaries and saves them to files.

        Args:
            summaries (list): A list of tuples containing filenames and their corresponding summaries.
            industry (str): The industry for which reports are to be generated.
        """
        report_template = (
            '{\n'
            '    url: "https://www.example.com",\n'
            '    reliable: "Yes/No",\n'
            '    reason: "Why is this a reliable source for current industry? 1 - 2 '
            'sentences"\n'
            '}'
        )
        report_dir = os.path.join('reports', industry, 'for_each_summary')
        os.makedirs(report_dir, exist_ok=True)

        for filename, summary in tqdm(summaries, desc='Processing summaries', unit='summary'):
            report_filename = f"{os.path.splitext(filename)[0]}_report.md"
            report_path = os.path.join(report_dir, report_filename)

            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                continue

            report_content = self.process_summary(summary, report_template, industry)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)


def main() -> None:
    """
    The main function to generate reports for predefined industries.
    """
    generator = ReportGenerator()
    industries = ['e_commerce']
    for industry in industries:
        summaries = generator.load_summaries(industry)
        generator.generate_report(summaries, industry)
        process_reports(industry)


if __name__ == '__main__':
    main()
