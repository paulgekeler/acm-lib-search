"""Contains all logic crammed into one file."""
from typing import List, Dict, Tuple
import argparse
import re
import json
import traceback
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup

class SearchResult:
    """A container for a search result.
    
    Attributes are either of specified type or None, if nothing was found.
    """
    def __init__(self, title: str, authors: List[str], conference: str,
                 abstract: str, eprint_url: str, doi: str,
                 total_citations: int, total_downloads: int, date: str):
        self.title = title
        self.authors = authors
        self.conference = conference
        self.abstract = abstract
        self.eprint_url = eprint_url
        self.doi = doi
        self.total_citations = total_citations
        self.total_downloads = total_downloads
        self.date = date
    
    def to_dict(self) -> Dict:
        return self.__dict__
    
    def __repr__(self):
        return f"SearchResult <title: '{self.title}'>"


def setup_chromedriver(executable_path: str=None) -> webdriver:
    """Sets up a headless chromedriver instance.
    
    Args:
        executable_path (str): Path to the chromedriver if it is not in PATH.

    Returns:
        The chromedriver instance.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    if executable_path is not None:
        service = webdriver.ChromeService(executable_path=executable_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        print("INFO: Using chromedriver without executable path. Ensure driver is in PATH.")
        driver = webdriver.Chrome(options=options)
    return driver

def quit_driver(driver: webdriver) -> None:
    """Quit the webdriver."""
    driver.quit()

def search_acm_for_title(title: str, driver: webdriver) -> List[str]:
    """Search acm library for top 20 results on title.
    
    Params:
        title:
            Title to search for.
        driver:
            Selenium WebDriver instance.
    
    Returns:
        Html string of top 20 results as a list.
    """
    driver.get("https://dl.acm.org")
    WebDriverWait(driver, 10).until(
        expected_conditions.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll"))
    ).click()

    search_box = driver.find_element(By.XPATH, '//div/input[@type="search"]')

    search_box.click()
    search_box.send_keys(f"{title}")
    search_box.send_keys(Keys.RETURN)

    WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_all_elements_located((By.XPATH, "//div/ul/li"))
        )

    results = driver.find_elements(By.XPATH, '//div/ul/li[@class="search__item issue-item-container"]')

    results_html = []

    for result in results:
        html = driver.execute_script("return arguments[0].outerHTML;", result)
        results_html.append(html)
    return results_html

def parse_authors(bs: BeautifulSoup) -> List[str]:
    authors = []
    span_authors = bs.find_all('span', class_='hlFld-ContribAuthor')
    if span_authors is not None:
        for elem in span_authors:
            author_tag = elem.a
            author = author_tag["title"]
            authors.append(author)
        return authors
    else:
        return []

def parse_abstract(bs: BeautifulSoup) -> str:
    abstract_tag_parent = bs.find('div', class_='issue-item__abstract truncate-text trunc-done')
    if abstract_tag_parent is not None:
        abstract_tag = abstract_tag_parent.p
        abstract = abstract_tag.text
        abstract = re.sub(r'\n', ' ', abstract)
        return abstract + "..."
    else:
        return ""

def parse_doi(bs: BeautifulSoup) -> str:
    doi_tag = bs.find('a', class_='issue-item__doi dot-separator')
    if doi_tag is not None:
        return doi_tag.string
    else:
        return ""

def parse_date(bs: BeautifulSoup) -> str:
    date_tag = bs.find('div', class_='bookPubDate simple-tooltip__block--b')
    if date_tag is not None:
        date = date_tag.string
        return re.sub(r'\s+', ' ', date)
    else:
        return ""
    
def parse_title(bs: BeautifulSoup) -> str:
    title_parent_tag = bs.find('span', class_='hlFld-Title')
    if title_parent_tag is not None:
        title_chunks = []
        for chunk in title_parent_tag.strings:
            title_chunks.append(chunk)
        title = " ".join(title_chunks)
        return re.sub(r'\s+', ' ', title)
    else:
        return ""

def parse_conference(bs: BeautifulSoup) -> str:
    conference_tag = bs.find('span', class_='epub-section__title')
    if conference_tag is not None:
        text = conference_tag.text
        return re.sub(r'\s+', ' ', text)
    else:
        return ""
    
def parse_pdf_link(bs: BeautifulSoup) -> str:
    pdf_tag = bs.find('a', {'data-title': 'PDF'})
    if pdf_tag is not None:
        return pdf_tag["href"]
    else:
        return ""
    
def parse_total_citations(bs: BeautifulSoup) -> int:
    citation_parent_tag = bs.find('div', class_='citation')
    if citation_parent_tag is not None:
        citation_tag = citation_parent_tag.span
        return int(citation_tag.text)
    else:
        return -1
    
def parse_total_downloads(bs: BeautifulSoup) -> int:
    downloads_parent_tag = bs.find('div', class_='metric')
    if downloads_parent_tag is not None:
        download_tag = downloads_parent_tag.span
        return int(download_tag.text)
    else:
        return -1

def parse_html(html: str) -> SearchResult:
    """Parse the html content of the search page.
    
    Args:
        html (str): Html of a search result web element on the DOM.

    Returns:
        An instance of SearchResult with all found information.
    """
    bs = BeautifulSoup(html, multi_valued_attributes=None)
    title = parse_title(bs)
    authors = parse_authors(bs)
    conference = parse_conference(bs)
    abstract = parse_abstract(bs)
    doi = parse_doi(bs)
    pdf_link = parse_pdf_link(bs)
    date = parse_date(bs)
    tot_downloads = parse_total_downloads(bs)
    tot_citations = parse_total_citations(bs)
    return SearchResult(
        title, authors, conference,
        abstract, pdf_link, doi,
        tot_citations, tot_downloads, date
    )

def get_search_results_from_html(*args) -> List[SearchResult]:
    search_res = []
    for html in args:
        search_res.append(parse_html(html))

def get_top_search_result_from_html(*args) -> SearchResult:
    """Only parse the top search result.
    
    Args:
        Variable number of html results.

    Returns:
        The search result.
    """
    return parse_html(args[0])


class ACMLibSearcher:
    """A simple wrapper containing the search functions.
    
    Usage:
        1. Create an instance with optional chromedriver path:
            searcher = ACMLibSearcher(chromedriver_path="/path/")
        2. Search for a paper title by calling one of the search methods:
            e.g. results = searcher.search_top_20("Paper title")
        3. Optionally save them to a json file with
            _ = searcher.save_results("name_of_file.json")
    """
    def __init__(self, chromedriver_path: str=None):
        self.driver = setup_chromedriver(executable_path=chromedriver_path)

    def search_top_20(self, paper_title: str, to_dict=True) -> List[SearchResult] | List[Dict]:
        """Search for the top 20 results by title.
        
        Args:
            paper_title (str): The title to search for.
            to_dict (bool): Whether to return a list of dict instead of SearchResult (optional)

        Returns:
            A list of either dictionaries or SearchResults containing the results.
        """
        results = search_acm_for_title(paper_title, self.driver)
        parsed_res = get_search_results_from_html(results)
        self.parsed_res = parsed_res
        if to_dict:
            return [res.to_dict() for res in parsed_res]
        return parsed_res

    def search_top_1(self, paper_title: str, to_dict=True) -> SearchResult | Dict:
        """Search for the top 1 result by title.
        
        Args:
            paper_title (str): The title to search for.
            to_dict (bool): Whether to return a dict instead of SearchResult (optional)

        Returns:
            A dictionary or SearchResult containing the result.
        """
        results = search_acm_for_title(paper_title, self.driver)
        parsed_res = get_top_search_result_from_html(results)
        self.parsed_res = parsed_res
        if to_dict:
            return parsed_res.to_dict()
        return parsed_res

    def save_results(self, file_path: str) -> bool:
        """Write results to disk as a json file.
        
        Args:
            file_path (str): Name and path to file.
        
        Raises:
            ValueError, if self.parsed_res is None.
            
        Returns:
            True if successful, else False.
        """
        if not self.parsed_res:
            raise ValueError("self.parsed_res is empty. Nothing to write.")
        write_results_to_disk(file_path, self.parsed_res)

def parse_args() -> Tuple[str, str]:
    parser = argparse.ArgumentParser(description="A quick and dirty search tool for the ACM Digital Library.")
    parser.add_argument('--paper_title', type=str, required=True, help='Title of the paper')
    parser.add_argument('--chromedriver_path', type=str, required=False, help='Path to the chromedriver.')
    args = parser.parse_args()
    if not args.chromedriver_path:
        return args.paper_title, ""
    return args.paper_title, args.chromedriver_path

def write_results_to_disk(file_path: str | Path, results: SearchResult | List[SearchResult]) -> bool:
    if isinstance(results, SearchResult):
        results = [results]
    try:
        with open(file_path, 'a') as f:
            for result in results:
                json.dump(result.to_dict(), f, indent=2)
        return True
    except Exception as e:
        traceback.print_exc()
        return False

if __name__ == '__main__':
    paper_title, webdriver_path = parse_args()
    if len(webdriver_path) == 0:
        driver = setup_chromedriver()
    else:
        driver = setup_chromedriver(
            executable_path=webdriver_path)
    
    scraped_results = search_acm_for_title(paper_title, driver)

    quit_driver()

    res = get_top_search_result_from_html(scraped_results)
    if write_results_to_disk("results.json", res):
        print("Done")
    else:
        print("Failed to save. Something went wrong. Aborting...")



