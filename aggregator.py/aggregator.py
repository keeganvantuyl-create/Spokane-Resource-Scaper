import requests
from bs4 import BeautifulSoup

# List of sites to scrape (Example structure)
sites_to_scrape = [
    {"name": "Spokane Resources", "url": "https://example.com/spokane-help"},
    # Add your real target URLs here
]

all_matches = []
search_term = input("Enter search term (e.g., 'grants' or 'nonprofit'): ")

# --- STEP 3: Scrape and Filter ---
for site in sites_to_scrape:
    try:
        # This is where your specific site-scraping logic lives
        # For example purposes, let's assume 'name' and 'address' are extracted here
        response = requests.get(site['url'], timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
       
        # Simulated loop through site elements
        # for item in soup.find_all('a'):
        #     name = item.get_text()
        #     address = item.get('href')

        # # Improved filter: Checks the link name and the URL itself
        # if name and address and "http" in address:
        #     if search_term.lower() in name.lower() or search_term.lower() in address.lower():
        #         all_matches.append({
        #             "site": site['name'],
        #             "name": name,
        #             "link": address
        #         })

    except Exception as e:
        print(f"Skipping {site['name']} (Connection issue)")

# --- STEP 4: Save and Display Results ---
with open("resources.txt", "w") as file:
    file.write(f"--- AGGREGATED RESOURCES FOR: {search_term.upper()} ---\n\n")

    if not all_matches:
        print(f"\nNo matches found for '{search_term}'.")
        file.write("No matches found during this search.")
    else:
        # Use set to avoid showing the exact same link twice if found multiple times
        seen_links = set()
        count = 0
       
        for match in all_matches:
            if match['link'] not in seen_links:
                count += 1
                output = f"[{count}] {match['name']}\nSource: {match['site']}\nLink: {match['link']}\n"
               
                print(output)
                file.write(output + "\n")
                seen_links.add(match['link'])

print(f"\nDone! Found {len(seen_links)} unique resources. Saved to 'resources.txt'.")