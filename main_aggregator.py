import requests
from bs4 import BeautifulSoup
import time
import csv
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- STEP 1: Setup & Data Sources ---
today = datetime.now()
seen_links = set()
all_matches = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

sites_to_scrape = [
    {"name": "Spokane Housing Authority", "url": "https://www.spokanehousing.org/"},
    {"name": "SNAP Spokane (Housing)", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/"},
    {"name": "Pioneer Human Services", "url": "https://pioneerhumanservices.org/career-services/guiding-reentry-opportunities-for-workforce-development/"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/"},
    {"name": "SCC Workforce Transitions", "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs"},
    {"name": "STA Opportunity (Bus Pass)", "url": "https://www.spokanetransit.com/opportunity/"},
    {"name": "NA Spokane (Recovery)", "url": "https://waswena.org/meetings/"}
]

# Fallback data for when sites block the scraper
fallback_resources = [
    {"site": "NA Spokane (Manual)", "name": "The Nooner (Daily 12pm)", "link": "https://waswena.org/", "deadline": "2026-12-31"},
    {"site": "NA Spokane (Manual)", "name": "Hugz Not Drugz (Mon 6pm)", "link": "https://waswena.org/", "deadline": "2026-12-31"},
    {"site": "NA Spokane (Manual)", "name": "Roots Hall Meetings (Daily)", "link": "https://waswena.org/", "deadline": "2026-12-31"}
]

print(f"--- Spokane Resource Aggregator | {today.strftime('%B %d, %Y')} ---")
search_term = input("Enter search (e.g., 'grant', 'jobs', 'meetings'): ").lower()

# --- STEP 2: Scraping + Fallback Logic ---
for site in sites_to_scrape:
    try:
        print(f"Checking {site['name']}...")
        time.sleep(1)
        response = requests.get(site['url'], headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        for item in soup.find_all('a'):
            name = item.get_text().strip()
            link = item.get('href')
            if name and link and "http" in link:
                if search_term in name.lower() or search_term in link.lower():
                    all_matches.append({"site": site['name'], "name": name, "link": link, "deadline": "2026-03-26"})
    except Exception:
        print(f"Skipping {site['name']} (Direct scraping blocked)")

# If searching for recovery/meetings, add the fallbacks automatically
if "meeting" in search_term or "recovery" in search_term or "na" in search_term:
    all_matches.extend(fallback_resources)

# --- STEP 3: Export ---
if not all_matches:
    print(f"\nNo matches found for '{search_term}'.")
else:
    with open("spokane_resources.csv", "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['priority', 'name', 'site', 'link'])
        writer.writeheader()
        for match in all_matches:
            if match['link'] not in seen_links:
                seen_links.add(match['link'])
                deadline_date = datetime.strptime(match['deadline'], "%Y-%m-%d")
                priority = "URGENT" if (deadline_date - today).days <= 3 else "NORMAL"
                print(f"[{priority}] {match['name']} ({match['site']})")
                writer.writerow({'priority': priority, 'name': match['name'], 'site': match['site'], 'link': match['link']})

print(f"\nDone! Exported to 'spokane_resources.csv'.")