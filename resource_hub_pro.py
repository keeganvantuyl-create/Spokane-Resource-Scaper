import customtkinter as ctk
import asyncio
import threading
import json
import os
import sys
import subprocess
import webbrowser
import winsound
from datetime import datetime
from urllib.parse import urljoin, quote
from playwright.async_api import async_playwright
from duckduckgo_search import DDGS
from tkinter import filedialog

# --- CONFIGURATION ---
SETTINGS_FILE = "user_settings.json"
HTML_FILE = "dashboard.html"

# Curated Spokane Resource List
SITES = [
    {"name": "Spokane Housing Authority", "url": "https://www.spokanehousing.org/"},
    {"name": "SNAP Spokane", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/"},
    {"name": "SCC Workforce Transitions",
     "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs"},
    {"name": "Catholic Charities EWA", "url": "https://www.cceasternwa.org/housing"},
    {"name": "City of Spokane CHHS", "url": "https://my.spokanecity.org/chhs/resources/"},
    {"name": "Pioneer Human Services", "url": "https://pioneerhumanservices.org/training/"},
    {"name": "Goodwill Industries NW",
     "url": "https://www.discovergoodwill.org/supportive-services-for-veteran-families/"},
    {"name": "Career Path Services", "url": "https://www.careerpathservices.org/"},
    {"name": "Union Gospel Mission", "url": "https://www.uniongospelmission.org/recovery"},
    {"name": "The Arc of Spokane", "url": "https://www.arc-spokane.org/supported-employment"},
    {"name": "Next Generation Zone", "url": "https://nextgenzone.org/"}
]

FIELD_MAP = {
    "first_name": ["first", "fname", "given-name", "name"],
    "email": ["email", "mail", "user_email"],
    "resume": ["resume", "cv", "upload", "attachment", "file"]
}


def ensure_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except:
        pass


class ResourceHubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spokane Resource Hub Pro - Keegan Van Tuyl")
        self.geometry("950x850")
        ctk.set_appearance_mode("dark")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Search & Aggregate")
        self.tabview.add("Auto-Fill Tool")
        self.tabview.add("Settings")

        self.setup_search_tab()
        self.setup_autofill_tab()
        self.setup_settings_tab()
        self.load_settings()

    def setup_search_tab(self):
        tab = self.tabview.tab("Search & Aggregate")
        self.query_entry = ctk.CTkEntry(tab, placeholder_text="Search (job/grant/housing)...", width=450)
        self.query_entry.pack(pady=10)

        self.web_search_var = ctk.BooleanVar(value=False)
        self.web_switch = ctk.CTkSwitch(tab, text="Include Live Web Search", variable=self.web_search_var)
        self.web_switch.pack(pady=5)

        self.progress_label = ctk.CTkLabel(tab, text="Ready to Scan")
        self.progress_label.pack(pady=(10, 0))
        self.progress_bar = ctk.CTkProgressBar(tab, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 10))

        self.search_btn = ctk.CTkButton(tab, text="Launch Deep Scan", fg_color="#2ecc71", command=self.run_aggregator)
        self.search_btn.pack(pady=10)

        self.results_frame = ctk.CTkScrollableFrame(tab, width=850, height=450, label_text="Scraper Results")
        self.results_frame.pack(pady=10, fill="both", expand=True)

    def setup_autofill_tab(self):
        tab = self.tabview.tab("Auto-Fill Tool")
        self.url_entry = ctk.CTkEntry(tab, placeholder_text="Target URL", width=600)
        self.url_entry.pack(pady=20)
        self.fill_btn = ctk.CTkButton(tab, text="Apply Now (Auto-Fill)", command=self.start_autofill,
                                      fg_color="#3498db")
        self.fill_btn.pack(pady=10)
        self.log_box = ctk.CTkTextbox(tab, width=800, height=400, fg_color="#1a1a1a")
        self.log_box.pack(pady=10)

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text="User Profile Settings", font=("Arial", 16, "bold")).pack(pady=20)
        self.name_entry = ctk.CTkEntry(tab, placeholder_text="Full Name", width=400)
        self.name_entry.pack(pady=10)
        self.email_entry = ctk.CTkEntry(tab, placeholder_text="Email Address", width=400)
        self.email_entry.pack(pady=10)

        res_frame = ctk.CTkFrame(tab, fg_color="transparent")
        res_frame.pack(pady=10)
        self.res_path = ctk.CTkEntry(res_frame, placeholder_text="Resume Path", width=300)
        self.res_path.pack(side="left", padx=5)
        ctk.CTkButton(res_frame, text="Browse", width=80, command=self.browse_file).pack(side="left")
        ctk.CTkButton(tab, text="Save Settings", command=self.save_settings, fg_color="#2ecc71").pack(pady=40)

    def add_result_card(self, site, title, url):
        card = ctk.CTkFrame(self.results_frame)
        card.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(card, text=f"Source: {site}\nTitle: {title[:70]}", justify="left").pack(side="left", padx=15,
                                                                                             pady=10)
        ctk.CTkButton(card, text="Apply", width=100, command=lambda u=url: self.transfer_url(u)).pack(side="right",
                                                                                                      padx=15)

    def transfer_url(self, url):
        self.url_entry.delete(0, "end");
        self.url_entry.insert(0, url)
        self.tabview.set("Auto-Fill Tool")

    async def scrape_logic(self, query):
        all_results = [];
        seen_urls = set()
        for widget in self.results_frame.winfo_children(): widget.destroy()

        self.progress_bar.set(0)
        total_steps = len(SITES) + (1 if self.web_search_var.get() else 0)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for i, site in enumerate(SITES):
                try:
                    self.after(0, lambda s=site['name']: self.progress_label.configure(text=f"Scanning: {s}"))
                    await page.goto(site['url'], timeout=12000)
                    if query.lower() in (await page.content()).lower():
                        if site['url'] not in seen_urls:
                            seen_urls.add(site['url'])
                            res = {"n": "General Resource/Job", "s": site['name'], "l": site['url']}
                            all_results.append(res)
                            self.after(0, lambda r=res: self.add_result_card(r['s'], r['n'], r['l']))
                except:
                    pass
                self.after(0, lambda v=(i + 1) / total_steps: self.progress_bar.set(v))

            if self.web_search_var.get():
                self.after(0, lambda: self.progress_label.configure(text="Deep Scanning Web..."))
                try:
                    with DDGS() as ddgs:
                        web_res = ddgs.text(f"{query} Spokane WA", max_results=15)
                        for r in web_res:
                            if r['href'] not in seen_urls:
                                seen_urls.add(r['href'])
                                res = {"n": r['title'], "s": "Web Search", "l": r['href']}
                                all_results.append(res)
                                self.after(0, lambda r=res: self.add_result_card(r['s'], r['n'], r['l']))
                except:
                    pass

            await browser.close()
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.progress_label.configure(text="Scan Complete!"))
            self.generate_html(all_results)
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            webbrowser.open(HTML_FILE)

    def generate_html(self, results):
        cards = ""
        for r in results:
            cards += f"<div class='card'><h3>{r['n']}</h3><p>{r['s']}</p><a href='{r['l']}' class='btn' target='_blank'>Apply</a></div>"

        template = f"""<html><head><style>
            body {{ background: #121212; color: #eee; font-family: sans-serif; padding: 40px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: #1e1e1e; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; }}
            .btn {{ color: #3498db; text-decoration: none; font-weight: bold; }}
        </style></head><body><h1>Spokane {datetime.now().year} Results</h1><div class='grid'>{cards}</div></body></html>"""

        with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(template)

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n");
        self.log_box.see("end")

    async def autofill_logic(self, url):
        with open(SETTINGS_FILE, "r") as f:
            user = json.load(f)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url)
            inputs = await page.query_selector_all('input')
            for btn in inputs:
                n = (await btn.get_attribute('name') or "").lower()
                if any(k in n for k in FIELD_MAP["first_name"]): await btn.fill(user["name"])
                if (await btn.get_attribute('type')) == "file": await btn.set_input_files(user["resume"])
            self.log("Fields auto-filled. Please review.")
            await asyncio.sleep(60)

    def run_aggregator(self):
        threading.Thread(target=lambda: asyncio.run(self.scrape_logic(self.query_entry.get())), daemon=True).start()

    def start_autofill(self):
        threading.Thread(target=lambda: asyncio.run(self.autofill_logic(self.url_entry.get())), daemon=True).start()

    def browse_file(self):
        p = filedialog.askopenfilename()
        if p: self.res_path.delete(0, "end"); self.res_path.insert(0, p)

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f: json.dump(
            {"name": self.name_entry.get(), "email": self.email_entry.get(), "resume": self.res_path.get()}, f)
        self.log("Profile saved.")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                d = json.load(f);
                self.name_entry.insert(0, d.get("name", ""));
                self.email_entry.insert(0, d.get("email", ""));
                self.res_path.insert(0, d.get("resume", ""))


if __name__ == "__main__":
    ensure_browser()
    app = ResourceHubPro();
    app.mainloop()