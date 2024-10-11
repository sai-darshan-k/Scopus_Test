import requests
import pandas as pd
import time
import logging
import json
from ratelimit import limits, sleep_and_retry  # type: ignore

# Setting up for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Loading configuration
with open('config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['API_KEY']
CALLS_PER_SECOND = 1
SECONDS_PER_CALL = 1 / CALLS_PER_SECOND

@sleep_and_retry
@limits(calls=CALLS_PER_SECOND, period=SECONDS_PER_CALL)
def make_request(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses
    return response

def extract_scopus_data(author_id):
    try:
        headers = {"X-ELS-APIKey": API_KEY, "Accept": "application/json"}
        
        # Get author details
        author_details_url = f"https://api.elsevier.com/content/author?author_id={author_id}"
        author_details_resp = make_request(author_details_url, headers=headers)
        
        author_details = author_details_resp.json()
        
        if 'author-retrieval-response' not in author_details:
            logging.warning(f"No 'author-retrieval-response' found for author_id {author_id}")
            return []
        
        author_name = (
            author_details['author-retrieval-response'][0]['author-profile']['preferred-name']['given-name'] + " " +
            author_details['author-retrieval-response'][0]['author-profile']['preferred-name']['surname']
        )
        
        # Get publications
        publications_url = "https://api.elsevier.com/content/search/scopus"
        params = {
            "query": f"au-id({author_id})",
            "count": "25",
            "sort": "pubyear",
        }
        resp = make_request(publications_url, params=params, headers=headers)
        
        results = resp.json().get("search-results", {}).get("entry", [])
        
        papers_2023_2024 = []
        for result in results:
            pub_year = int(result["prism:coverDate"][:4])
            if pub_year in [2023, 2024]:
                paper_title = result["dc:title"]
                citations = int(result.get('citedby-count', 0))
                papers_2023_2024.append({
                    "Faculty Name": author_name,
                    "Paper Title": paper_title,
                    "Citations": citations,
                    "Year": pub_year
                })
        
        return papers_2023_2024

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred for author_id {author_id}: {e}")
        return []

def main():
    profile_links = [
        "https://www.scopus.com/authid/detail.uri?authorId=57223100630",
        "https://www.scopus.com/authid/detail.uri?authorId=55079543700",
        "https://www.scopus.com/authid/detail.uri?authorId=35737586100",
        "https://www.scopus.com/authid/detail.uri?authorId=57189239708",
        "https://www.scopus.com/authid/detail.uri?authorId=55881946700",
        "https://www.scopus.com/authid/detail.uri?authorId=57044254900",
        "https://www.scopus.com/authid/detail.uri?authorId=57055221400",
        "https://www.scopus.com/authid/detail.uri?authorId=59256484700",
        "https://www.scopus.com/authid/detail.uri?authorId=57162822500",
        "https://www.scopus.com/authid/detail.uri?authorId=57205027677",
        "https://www.scopus.com/authid/detail.uri?authorId=57192668092",
        "https://www.scopus.com/authid/detail.uri?authorId=55811681700",
        "https://www.scopus.com/authid/detail.uri?authorId=57205128308",
        "https://www.scopus.com/authid/detail.uri?authorId=57789387000",
        "https://www.scopus.com/authid/detail.uri?authorId=35069671200",
        "https://www.scopus.com/authid/detail.uri?authorId=35332112400",
        "https://www.scopus.com/authid/detail.uri?authorId=58529182900",
        "https://www.scopus.com/authid/detail.uri?authorId=57193578932",
        "https://www.scopus.com/authid/detail.uri?authorId=57212476297",
        "https://www.scopus.com/authid/detail.uri?authorId=57201949000",
        "https://www.scopus.com/authid/detail.uri?authorId=55263618900",
        "https://www.scopus.com/authid/detail.uri?authorId=58244012600",
        "https://www.scopus.com/authid/detail.uri?authorId=57200798153",
        "https://www.scopus.com/authid/detail.uri?authorId=59010451200",
        "https://www.scopus.com/authid/detail.uri?authorId=57201030358",
        "https://www.scopus.com/authid/detail.uri?authorId=57211135848",
        "https://www.scopus.com/authid/detail.uri?authorId=56708741500",
        "https://www.scopus.com/authid/detail.uri?authorId=57209182380",
        "https://www.scopus.com/authid/detail.uri?authorId=56168895700",
        "https://www.scopus.com/authid/detail.uri?authorId=57219413559"
    ]

    data = []
    for link in profile_links:
        author_id = link.split('authorId=')[-1]
        logging.info(f"Processing author_id: {author_id}")
        scopus_data = extract_scopus_data(author_id)
        data.extend(scopus_data)
        time.sleep(1)  # Adding a delay between processing each author

    df = pd.DataFrame(data)
    df.to_excel("scopus_data_2023_2024_updated.xlsx", index=False)
    logging.info("Data extraction complete")

if __name__ == "__main__":
    main()
