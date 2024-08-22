#### ACM Digital Library Search Tool

A short and rudimentary Python implementation to search for titles at *https://dl.acm.org*.
Based on Selenium and BeautifulSoup.
Currently only supports searches for paper titles.

##### Requires

Chromedriver installed on device *https://developer.chrome.com/docs/chromedriver/downloads*. As of now the only supported webdriver.

##### Limitations

- Do not use it too frequently in short periods of time, ACM might block your IP
- Keep in mind, ACM technically disallows bots

##### Installation

Options:
- `git clone https://github.com/paulleo13/acm-lib-search.git`
- via pip: `pip install acm-lib-search` (! WARNING: Does not work as of right now. Haven't gotten around to fix it yet.)

##### How to use

You can use the tool either via the command line with `python acm_lib_search.py --paper_title="Sample paper title" --chromedriver_path="/optional/path/to/chromedriver"` (The chromedriver flag is optional and only necessary if the driver is not in your *PATH* variable).
Then the top result is saved to a file named `results.json` in the current working directory.

Or import the `ACMLibSearcher` class from `acm_lib_search` and search for results as follows:
1. Create an instance with optional chromedriver path:
    ```python
    searcher = ACMLibSearcher(chromedriver_path="/path/")
    ```
2. Search for a paper title by calling one of the search methods e.g. 
    ```python
    results = searcher.search_top_20("Paper title")
    ```
3. Optionally save them to a json file with
    ```python
    _ = searcher.save_results("name_of_file.json")
    ```


