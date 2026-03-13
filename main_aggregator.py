import requests
from bs4 import BeautifulSoup
import time
import csv
from datetime import datetime

# --- STEP 1: Setup & Spokane Data Sources ---
today = datetime.now()
seen_links = set()
all_matches = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# List of Spokane-specific resources including the new NA program entry
sites_to_scrape = [
    {"name": "Spokane Housing Authority", "url": "https://www.spokanehousing.org/"},
    {"name": "SNAP Spokane (Housing)", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/"},
    {"name": "Pioneer Human Services", "url": "https://pioneerhumanservices.org/career-services/guiding-reentry-opportunities-for-workforce-development/"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/"},
    {"name": "SCC Workforce Transitions", "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs"},
    {"name": "STA Opportunity (Bus Pass)", "url": "https://www.spokanetransit.com/opportunity/"},
    {"name": "NA Spokane (Recovery)", "url": "https://www.waswena.org/"}
]

print(f"--- Spokane Resource Aggregator | {today.strftime('%B %d, %Y')} ---")
search_term = input("Enter search (e.g., 'grant', 'jobs', 'recovery'): ").lower()

# --- STEP 2: Live Web Scraping ---
for site in sites_to_scrape:
    try:
        print(f"Checking {site['name']}...")
        time.sleep(1)  # Polite delay to avoid IP blocks
        response = requests.get(site['url'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        for item in soup.find_all('a'):
            name = item.get_text().strip()
            link = item.get('href')

            if name and link and "http" in link:
                if search_term in name.lower() or search_term in link.lower():
                    all_matches.append({
                        "site": site['name'],
                        "name": name,
                        "link": link,
                        "deadline": "2026-03-26"  # Placeholder deadline
                    })
    except Exception as e:
        print(f"Skipping {site['name']} (Error: {e})")

# --- STEP 3: Priority Logic & Export ---
if not all_matches:
    print(f"\nNo matches found for '{search_term}'.")
else:
    print(f"\n--- Results for: {search_term.upper()} ---")

    with open("spokane_resources.csv", "w", newline='', encoding='utf-8') as csvfile:
        fieldnames = ['priority', 'name', 'site', 'link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for match in all_matches:
            if match['link'] not in seen_links:
                seen_links.add(match['link'])

                # Priority Logic based on the placeholder deadline
                deadline_date = datetime.strptime(match['deadline'], "%Y-%m-%d")
                days_left = (deadline_date - today).days
                priority = "URGENT" if days_left <= 3 else "NORMAL"

                # Print to Screen
                print(f"[{priority}] {match['name']}")
                print(f"Source: {match['site']} | Link: {match['link']}\n")

                # Save to CSV
                writer.writerow({
                    'priority': priority,
                    'name': match['name'],
                    'site': match['site'],
                    'link': match['link']
                })

print(f"Done! Found {len(seen_links)} unique items. Exported to 'spokane_resources.csv'.")