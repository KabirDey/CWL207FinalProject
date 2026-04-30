import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse

# Master list to hold all scraped dictionaries
movie_dataset = []

def get_imdb_id(film_name):

    # Official IMDb databse API blocked this script even with headers, so we use hidden autocomplete API

    """Searches IMDb using their hidden autocomplete API to bypass scraping blocks."""
    print(f"  -> [IMDb] Searching API for: '{film_name}'...")
    try:
        safe_name = urllib.parse.quote(film_name.lower())
        first_letter = safe_name[0] if safe_name and safe_name[0].isalpha() else 'a'
        url = f"https://v3.sg.media-imdb.com/suggestion/{first_letter}/{safe_name}.json"
        
        # Sets a custom User-Agent to make scraper identify as a standard web browser, helping bypass basic anti-bot filters that block automated scripts

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'd' in data and len(data['d']) > 0:
                for result in data['d']:
                    if result.get('id', '').startswith('tt'):
                        formatted_id = result['id']
                        matched_title = result.get('l', 'Unknown Title')
                        matched_year = result.get('y', 'Year Unknown')
                        
                        print(f"     [IMDb] Match found! -> {formatted_id} ({matched_title}, {matched_year})")
                        return formatted_id
                        
            print("     [IMDb] No results found.")
        else:
            print(f"     [IMDb] API blocked the request (Status: {response.status_code})")
            
    except Exception as e:
        print(f"     [IMDb] Search error: {e}")
        
    return "Not Found"

def extract_data_by_label(soup, label_keyword):
    """Hunts the HTML for a specific label (like 'Director') and extracts the text next to it."""
    label = soup.find(lambda tag: tag.name in ['b', 'strong', 'td', 'th'] and label_keyword.lower() in tag.text.lower())
    
    if label:
        if label.name in ['td', 'th']:
            next_cell = label.find_next_sibling('td')
            if next_cell:
                return next_cell.text.strip().replace('\n', ', ')
        
        next_sibling = label.next_sibling
        if next_sibling and isinstance(next_sibling, str):
            return next_sibling.strip().strip(':').strip()
            
        parent_text = label.parent.text
        return parent_text.replace(label.text, '').strip().strip(':').strip()
        
    return ""

def parse_pakmag_page(url, page_id, era):
    """Fetches the URL, parses the HTML, and returns a dictionary of data."""
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        title_element = soup.find('h1')
        if not title_element:
            return None 
        
        film_name = title_element.text.strip()
        
        # 1. Extract Custom Year and Language
        year_str = ""
        language_str = ""
        
        credits_header = soup.find(lambda tag: tag.name in ['b', 'h2', 'h3', 'div'] and 'Film credits of' in tag.text)
        if credits_header:
            match = re.search(r'\((.*?) - (\d{4})\)', credits_header.text)
            if match:
                language_str = match.group(1).strip()
                year_str = match.group(2).strip()
                
        if not year_str:
            release_date = soup.find(lambda tag: tag.name in ['b', 'td', 'span', 'div'] and 'Released date:' in tag.text)
            if release_date:
                year_match = re.search(r'\d{4}', release_date.parent.text)
                if year_match:
                    year_str = year_match.group(0)

        metadata_compiled = f"Year: {year_str} | Language: {language_str}"

        # 2. Extract All Requested Table Data
        director_str = extract_data_by_label(soup, "Director")
        producer_str = extract_data_by_label(soup, "Producer")
        writer_str = extract_data_by_label(soup, "Writer")
        musician_str = extract_data_by_label(soup, "Musician")
        singer_str = extract_data_by_label(soup, "Singer")
        poet_str = extract_data_by_label(soup, "Poet")
        camera_str = extract_data_by_label(soup, "Camera")
        other_str = extract_data_by_label(soup, "Other") 
        
        actor_str = extract_data_by_label(soup, "Cast") 
        if not actor_str: 
            actor_str = extract_data_by_label(soup, "Actors")

        # FIX FOR THE INFINITE LOOP

        # If the page loads but has absolutely no director, actors, or year, 
        # it is likely a dead page masquerading as a real one. Reject it.
        # This is due to the failsafe not working as an empty page was returned rather than no page

        if not year_str and not director_str and not actor_str:
            return None

        # 3. Get IMDb ID (doing this last saves API calls if the page is dead)
        imdb_id = get_imdb_id(film_name)

        # 4. Return the expanded dictionary
        return {
            'pageid': page_id,
            'era': era,
            'film_name': film_name,
            'imdb_id': imdb_id,
            'directors': director_str,
            'producers': producer_str,
            'writers': writer_str,
            'actors': actor_str,
            'musicians': musician_str,
            'singers': singer_str,
            'poets': poet_str,
            'camera': camera_str,
            'others': other_str,
            'metadata': metadata_compiled
        }

    except Exception as e:
        print(f"Failed to process {url}: {e}")
        return None



try:
    
    # 1. Scrape Post-Partition Data
    
    print("Starting Post-Partition Scraping...")
    consecutive_fails = 0
    max_fails = 20  
    pid = 1

    while True: 
        url = f"https://pakmag.net/film/details.php?pid={pid}"
        print(f"Scraping Post-Partition ID: {pid}...")
        
        data = parse_pakmag_page(url, pid, "Post-Partition")
        if data:
            movie_dataset.append(data)
            consecutive_fails = 0
        else:
            consecutive_fails += 1
            print(f"  -> Page empty or invalid. (Fail {consecutive_fails}/{max_fails})")
            if consecutive_fails >= max_fails:
                print(f"Reached {max_fails} consecutive failures. Assuming end of Post-Partition database.")
                break
            
        pid += 1
        time.sleep(1.5)

    
    # 2. Scrape Pre-Partition Data
    
    print("\nStarting Pre-Partition Scraping...")
    consecutive_fails = 0
    pid = 1

    while True:
        url = f"https://pakmag.net/film/predetails.php?pid={pid}"
        print(f"Scraping Pre-Partition ID: {pid}...")
        
        data = parse_pakmag_page(url, pid, "Pre-Partition")
        if data:
            movie_dataset.append(data)
            consecutive_fails = 0
        else:
            consecutive_fails += 1
            print(f"  -> Page empty or invalid. (Fail {consecutive_fails}/{max_fails})")
            if consecutive_fails >= max_fails:
                print(f"Reached {max_fails} consecutive failures. Assuming end of Pre-Partition database.")
                break
            
        pid += 1

         # So that API doesn't detect python script, by sending hundreds of requests per second 

        time.sleep(1.5) 

except KeyboardInterrupt:
    # This catches the manual stop (Ctrl+C) and prevents data loss --> in case script needs to be ended prematurely
    print("\n" + "="*50)
    print("🚨 SCRAPING INTERRUPTED BY USER 🚨")
    print("Catching data and preparing to save...")
    print("="*50 + "\n")


# 3. Export to CSV (Runs normally OR if interrupted)

if len(movie_dataset) > 0:
    print(f"\nExporting {len(movie_dataset)} records to CSV...")
    df = pd.DataFrame(movie_dataset)
    df.to_csv('pakmag_FULL_dataset.csv', index=False, encoding='utf-8')
    print("Successfully saved 'pakmag_FULL_dataset.csv'.")
else:
    print("\nNo valid data was scraped, so no CSV was created.")
