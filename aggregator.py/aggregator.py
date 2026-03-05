import requests
from bs4 import BeautifulSoup
import time

# --- STEP 1: Setup ---
seen_links = set()
all_matches = []
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

sites_to_scrape = [
    # HOUSING
    {"name": "Spokane Housing Authority", "url": "https://www.spokanehousing.org/"},
    {"name": "SNAP Spokane (Housing)", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/"},
    
    # JOBS & REENTRY
    {"name": "Pioneer Human Services", "url": "https://pioneerhumanservices.org/career-services/guiding-reentry-opportunities-for-workforce-development/"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/"},
    {"name": "Revive Center", "url": "https://rc4rc.org/"},
    
    # GRANTS & COLLEGE
    {"name": "SCC Workforce Transitions", "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs"},
    {"name": "CCS Foundation Scholarships", "url": "https://ccsfoundation.org/Apply-for-Scholarships"},
    {"name": "National Reentry Resource Center", "url": "https://nationalreentryresourcecenter.org/"},
    
    # TRANSPORTATION
    {"name": "STA Opportunity (Bus Pass)", "url": "https://www.spokanetransit.com/opportunity/"}
]

search_term = input("Enter search (e.g., 'grant', 'jobs', 'bus', 'housing'): ").lower()

# --- STEP 2: Scrape ---
for site in sites_to_scrape:
    try:
        print(f"Checking {site['name']}...")
        time.sleep(1) # Be polite to the servers
        
        response = requests.get(site['url'], headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for item in soup.find_all('a'):
            name = item.get_text().strip()
            link = item.get('href')

            if name and link and "http" in link:
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

print(f"\nDone! Found {len(seen_links)} resources. Saved to 'resources.txt'.")