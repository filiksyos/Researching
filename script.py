import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from notion_client import Client

# Notion API Setup
NOTION_TOKEN = "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"
DATABASE_ID = "14b926a21809818d8760cb140275e656"

notion = Client(auth=NOTION_TOKEN)

# Function to scrape Google search links
def scrape_google_links(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract top 5 search result links
    links = []
    domains = set()  # To track unique domains
    for a in soup.select("a"):
        href = a.get("href")
        if href and href.startswith("/url?q="):
            link = href.split("/url?q=")[1].split("&")[0]
            
            # Filter out unwanted links (e.g., Google Maps or invalid URLs)
            if "maps.google.com" in link or "google.com/maps" in link:
                continue  # Skip Google Maps links
            if not link.startswith("http"):  # Skip non-HTTP links
                continue
            
            # Extract domain and ensure uniqueness
            domain = urlparse(link).netloc
            if domain not in domains:
                domains.add(domain)
                links.append(link)
            
            # Stop after collecting 5 unique links
            if len(links) == 5:
                break
    return links

# Function to find a Notion page by its name
def find_page_by_name(page_name):
    try:
        query = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "Name",
                "title": {
                    "equals": page_name
                }
            }
        )
        results = query.get("results", [])
        return results[0] if results else None
    except Exception as e:
        print(f"Error finding page '{page_name}': {e}")
        return None

# Function to add links to a page as clickable mentions
def add_links_to_page(page_id, links):
    try:
        for link in links:
            notion.blocks.children.append(
                page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": link,  # Visible text
                                        "link": {"url": link},  # Clickable link
                                    },
                                }
                            ]
                        },
                    }
                ],
            )
        print(f"Links added to page {page_id} as clickable mentions.")
    except Exception as e:
        print(f"Error updating page: {e}")

if __name__ == "__main__":
    # Define resource categories and their search queries
    resources = {
        "Courses": "Python course",
        "YouTube Videos": "Python YouTube video",
        "Books": "Python book",
        "PDFs": "Python PDF",
        "Blogs": "Python programming blogs",
        "Podcasts": "Python podcasts",
        "Apps": "Python learning apps",
        "Tiktok Shorts": "Python tips Tiktok shorts",
        "Interactive Tutorials": "Interactive Python tutorials",
        "GitHub Tutorials": "Python GitHub projects tutorials"
    }

    for page_name, query in resources.items():
        print(f"Processing page: {page_name}")
        # Find the corresponding page in Notion
        page = find_page_by_name(page_name)
        if not page:
            print(f"Page '{page_name}' not found in database.")
            continue

        # Scrape Google search links
        links = scrape_google_links(query)
        print(f"Top 5 links for '{page_name}': {links}")

        # Add links to the found page
        add_links_to_page(page["id"], links)
