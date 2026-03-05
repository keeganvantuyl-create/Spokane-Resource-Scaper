import requests
from bs4 import BeautifulSoup

# List of sites to scrape
seen_links = set()
all_matches = []

# Added a couple of real Spokane links as examples
sites_to_scrape = [
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/"},
    {"name": "Spokane Public Library", "url": "https://www.spokanelibrary.org/digital/"},
    {"name": "City of Spokane Jobs", "url": "https://my.spokanecity.org/jobs/"},
    {"name": "Spokane County Resources", "url": "https://www.spokanecounty.gov/543/Community-Resources"},
    {"name": "Catholic Charities Spokane", "url": "https://www.cceasternwa.org/all-services"},
    {"name": "Spokane 211", "url": "https://wa211.org/"},
    {"name": "City of Spokane Home", "url": "https://my.spokanecity.org/"}
]

search_term = input("Enter search term (e.g., 'reentry' or 'housing'): ")

# --- STEP 3: Scrape and Filter ---
for site in sites_to_scrape:
    try:
        response = requests.get(site['url'], timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for all links on the page
        for item in soup.find_all('a'):
            name = item.get_text().strip()
            address = item.get('href')

            if name and address and "http" in address:
                if search_term.lower() in name.lower() or search_term.lower() in address.lower():
                    all_matches.append({
                        "site": site['name'],
                        "name": name,
                        "link": address
                    })

    except Exception as e:
        print(f"Skipping {site['name']} (Connection issue)")

# --- STEP 4: Save and Display Results ---
with open("resources.txt", "w") as file:
    file.write(f"--- AGGREGATED RESOURCES FOR: {search_term.upper()} ---\n\n")

    if not all_matches:
        print(f"\nNo matches found for '{search_term}'.")
        file.write("No matches found during this search.")
    else:
        count = 0
        for match in all_matches:
            if match['link'] not in seen_links:
                count += 1
                seen_links.add(match['link']) # Fixed the 'ifseen_links' typo here
                output = f"[{count}] {match['name']}\nSource: {match['site']}\nLink: {match['link']}\n"
                
                print(output)
                file.write(output + "\n")

print(f"\nDone! Found {len(seen_links)} unique resources. Saved to 'resources.txt'.")