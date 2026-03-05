import requests
from bs4 import BeautifulSoup
import time

# --- STEP 1: Setup ---
seen_links = set()
all_matches = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

sites_to_scrape = [
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/"},
    {"name": "Spokane Public Library", "url": "https://www.spokanelibrary.org/digital/"},
    {"name": "City of Spokane Jobs", "url": "https://my.spokanecity.org/jobs/"},
    {"name": "Spokane County Resources", "url": "https://www.spokanecounty.gov/543/Community-Resources"},
    {"name": "Catholic Charities Spokane", "url": "https://www.cceasternwa.org/all-services"},
    {"name": "Spokane 211", "url": "https://wa211.org/"}
]

search_term = input("Enter search term (try 'housing', 'jobs', or 'help'): ").lower()

# --- STEP 2: Scrape ---
for site in sites_to_scrape:
    try:
        print(f"Checking {site['name']}...")
        time.sleep(1.5) # Wait a beat so we don't get blocked
        
        response = requests.get(site['url'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for item in soup.find_all('a'):
            name = item.get_text().strip()
            link = item.get('href')

            if name and link and "http" in link:
                # This checks if your word is in the link text or the link itself
                if search_term in name.lower() or search_term in link.lower():
                    all_matches.append({"site": site['name'], "name": name, "link": link})

    except Exception:
        print(f"Skipping {site['name']} (Connection issue)")

# --- STEP 3: Display & Save ---
with open("resources.txt", "w") as file:
    file.write(f"--- RESOURCES FOUND FOR: {search_term.upper()} ---\n\n")
    if not all_matches:
        print(f"\nNo matches found for '{search_term}'.")
    else:
        count = 0
        for match in all_matches:
            if match['link'] not in seen_links:
                count += 1
                seen_links.add(match['link'])
                output = f"[{count}] {match['name']}\nSource: {match['site']}\nLink: {match['link']}\n"
                print(output)
                file.write(output + "\n")

print(f"\nDone! Found {len(seen_links)} resources. Check 'resources.txt' for the list.")