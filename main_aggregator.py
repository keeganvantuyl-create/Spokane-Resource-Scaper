import asyncio
import csv
import re
import os
import glob
import sys
import itertools
import winsound  # Added for the finish notification
from datetime import datetime
from urllib.parse import urljoin, quote
from playwright.async_api import async_playwright

# --- CONFIG ---
TODAY = datetime.now()
TS_STR = TODAY.strftime('%Y-%m-%d_%H-%M')
TIMESTAMP = TODAY.strftime('%Y-%m-%d %I:%M %p')
HIST_DIR = "history"
HTML_FILE = "dashboard.html"
DATE_PATTERN = r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?(?:, \d{4})?|\d{1,2}/\d{1,2}/\d{2,4})'

if not os.path.exists(HIST_DIR): os.makedirs(HIST_DIR)

JUNK = ['link', 'contact us', 'news', 'press', 'stories', 'portal', 'login', 'lobby', 'search', 'faq', 'home', 'about',
        'privacy']
SMART_MAP = {
    "job": ["job", "career", "employment", "hiring", "work", "opening"],
    "grant": ["grant", "fund", "aid", "assistance", "scholarship"],
    "housing": ["rent", "housing", "shelter", "utility", "eviction"]
}

SITES = [
    {"name": "Spokane Housing Authority", "url": "https://www.spokanehousing.org/", "addr": "25 W Nora Ave, 99205",
     "ph": "509-333-3333"},
    {"name": "SNAP Spokane", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/",
     "addr": "3102 W Whistalks Wy, 99224", "ph": "509-456-7627"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/",
     "addr": "130 S Arthur St, 99202", "ph": "509-532-3120"},
    {"name": "SCC Workforce Transitions",
     "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs",
     "addr": "1810 N Greene St, 99217", "ph": "509-533-7249"},
    {"name": "STA Opportunity", "url": "https://www.spokanetransit.com/opportunity/",
     "addr": "701 W Riverside Ave, 99201", "ph": "509-328-7433"},
    {"name": "Catholic Charities EWA", "url": "https://www.cceasternwa.org/housing", "addr": "12 E 5th Ave, 99202",
     "ph": "509-358-4250"},
    {"name": "City of Spokane CHHS", "url": "https://my.spokanecity.org/chhs/resources/",
     "addr": "808 W Spokane Falls Blvd, 99201", "ph": "509-625-6325"},
    {"name": "Pioneer Human Services", "url": "https://pioneerhumanservices.org/training/",
     "addr": "1302 W Gardner Ave, 99201", "ph": "509-325-2355"},
    {"name": "Goodwill Industries NW",
     "url": "https://www.discovergoodwill.org/supportive-services-for-veteran-families/",
     "addr": "130 E 3rd Ave, 99202", "ph": "509-838-4246"},
    {"name": "Career Path Services", "url": "https://www.careerpathservices.org/", "addr": "701 W 2nd Ave, 99201",
     "ph": "509-326-6900"},
    {"name": "Union Gospel Mission", "url": "https://www.uniongospelmission.org/recovery",
     "addr": "1224 E Trent Ave, 99202", "ph": "509-535-8510"},
    {"name": "The Arc of Spokane", "url": "https://www.arc-spokane.org/supported-employment",
     "addr": "320 E 2nd Ave, 99202", "ph": "509-328-6326"},
    {"name": "Next Generation Zone", "url": "https://nextgenzone.org/", "addr": "901 E 2nd Ave, 99202",
     "ph": "509-340-7800"}
]


async def spinner(stop_event):
    for char in itertools.cycle(['|', '/', '-', '\\']):
        if stop_event.is_set(): break
        sys.stdout.write(f'\rScanning {len(SITES)} sites {char} ')
        sys.stdout.flush()
        await asyncio.sleep(0.1)
    sys.stdout.write('\rScan Complete!              \n')


def parse_deadline(date_str):
    if date_str == "Check Site": return 999, "Check Site", ""
    try:
        clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        if not re.search(r'\d{4}', clean): clean = f"{clean} {TODAY.year}"
        formats = ["%B %d %Y", "%m/%d/%Y", "%m/%d/%y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                diff = (dt - TODAY).days
                return diff, f"{date_str} ({diff}d left)", dt.strftime('%Y%m%d')
            except:
                continue
    except:
        pass
    return 998, date_str, ""


def get_historical_links(query):
    links = set()
    files = glob.glob(f"{HIST_DIR}/search_{query}_*.html")
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            links.update(re.findall(r'href=[\'"]?([^\'" >]+)', f.read()))
    return links


async def scrape_site(context, site, terms):
    results = []
    page = await context.new_page()
    try:
        await page.goto(site['url'], wait_until="domcontentloaded", timeout=25000)
        links = await page.locator("a").all()
        for link in links:
            text = (await link.inner_text()).strip()
            href = (await link.get_attribute("href") or "").lower()
            if not text or len(text) < 4 or any(j in text.lower() for j in JUNK): continue
            if any(t in text.lower() or t in href for t in terms):
                full_url = urljoin(site['url'], await link.get_attribute("href"))
                if not full_url.startswith("http") or "facebook" in full_url: continue
                ctx_t = await link.evaluate("el => el.parentElement.parentElement.innerText")
                d_match = re.search(DATE_PATTERN, ctx_t)
                raw_d = d_match.group(0) if d_match else "Check Site"
                days, stat, ics = parse_deadline(raw_d)
                results.append(
                    {"p": "URGENT" if days < 14 or "grant" in text.lower() else "NORMAL", "n": text, "s": site['name'],
                     "l": full_url, "d": stat, "days": days, "ics": ics, "a": site['addr'], "ph": site['ph']})
    except:
        pass
    finally:
        await page.close()
    return results


async def main():
    print(f"--- Spokane Scraper | {TIMESTAMP} ---")
    query = input("Search (job/grant/housing): ").strip().lower().rstrip('s')
    if not query: return
    search_list = SMART_MAP.get(query, [query])
    past_links = get_historical_links(query)

    stop_event = asyncio.Event()
    spinner_task = asyncio.create_task(spinner(stop_event))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        tasks = [scrape_site(ctx, site, search_list) for site in SITES]
        batches = await asyncio.gather(*tasks)
        all_matches = [m for b in batches for m in b]
        await browser.close()

    stop_event.set()
    await spinner_task

    if all_matches:
        all_matches.sort(key=lambda x: (x['days']))
        html_content = f"""<html><head><style>
            body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
            table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            th, td {{ padding: 12px; border-bottom: 1px solid #eee; text-align: left; }}
            th {{ background: #2c3e50; color: white; }}
            .URGENT {{ color: red; font-weight: bold; border-left: 4px solid red; }}
            .NEW {{ background: #28a745; color: white; padding: 2px 5px; border-radius: 3px; font-size: 10px; }}
            .btn {{ background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }}
        </style></head><body>
        <h2>Results: {query.upper()}</h2>
        <div style="margin-bottom:10px">{TIMESTAMP} | Found {len(all_matches)} items</div>
        <table><thead><tr><th>Action</th><th>Priority</th><th>Resource</th><th>Deadline</th><th>Contact</th></tr></thead><tbody>"""

        for m in all_matches:
            new_tag = '<span class="NEW">NEW</span>' if m['l'] not in past_links else ''
            cal_btn = f"<button class='btn' style='background:#f39c12' onclick='cal(\"{m['n']}\",\"{m['ics']}\")'>📅 Cal</button>" if \
            m['ics'] else ""
            m_url = f"https://www.google.com/maps/search/{quote(m['s'] + ' ' + m['a'])}"
            html_content += f"<tr><td><button class='btn' onclick='save(\"{m['n']}\",\"{m['l']}\")'>Save</button> {cal_btn}</td><td class='{m['p']}'>{m['p']}</td><td><a href='{m['l']}' target='_blank'><b>{m['n']}</b></a> {new_tag}<br><small>{m['s']}</small></td><td>{m['d']}</td><td><a href='tel:{m['ph']}'>📞 {m['ph']}</a><br><a href='{m_url}' target='_blank' style='font-size:11px;color:#3498db'>📍 Directions</a></td></tr>"

        html_content += """</tbody></table><script>
        function save(n,l){let s=JSON.parse(localStorage.getItem('s')||'[]');if(!s.find(i=>i.l===l)){s.push({n,l});localStorage.setItem('s',JSON.stringify(s));alert('Saved!');}}
        function cal(n,d){
            let ics = "BEGIN:VCALENDAR\\nVERSION:2.0\\nBEGIN:VEVENT\\nDTSTART:"+d+"T090000\\nSUMMARY:Deadline: "+n+"\\nEND:VEVENT\\nEND:VCALENDAR";
            let blob = new Blob([ics], {type: 'text/calendar'});
            let a = document.createElement('a'); a.download = 'reminder.ics'; a.href = window.URL.createObjectURL(blob); a.click();
        }
        </script></body></html>"""

        with open(HTML_FILE, "w", encoding='utf-8') as f:
            f.write(html_content)
        with open(f"{HIST_DIR}/search_{query}_{TS_STR}.html", "w", encoding='utf-8') as f:
            f.write(html_content)

        # Play Windows Success Sound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        os.startfile(HTML_FILE)
    else:
        print("No results.")


if __name__ == "__main__":
    asyncio.run(main())