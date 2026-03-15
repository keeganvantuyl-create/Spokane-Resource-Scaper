import customtkinter as ctk
import asyncio
import threading
import json
import os
import sys
import subprocess
import webbrowser
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
    {"name": "Next Generation Zone", "url": "https://nextgenzone.org/"}
]

FIELD_MAP = {
    "first_name": ["first", "fname", "given-name", "name"],
    "email": ["email", "mail", "user_email"],
    "resume": ["resume", "cv", "upload", "attachment", "file"]
}


def ensure_browser():
    """Ensures Chromium is installed for Playwright on the Acer Aspire."""
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except:
        pass


class ResourceHubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spokane Resource Hub Pro - Keegan Van Tuyl")
        self.geometry("950x800")
        ctk.set_appearance_mode("dark")

        # Layout Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Search & Aggregate")
        self.tabview.add("Auto-Fill Tool")
        self.tabview.add("Settings")

        self.setup_search_tab()
        self.setup_autofill_tab()
        self.setup_settings_tab()
        self.load_settings()

    # --- UI SETUP ---
    def setup_search_tab(self):
        tab = self.tabview.tab("Search & Aggregate")

        self.query_entry = ctk.CTkEntry(tab, placeholder_text="Search for grants, jobs, or housing...", width=450)
        self.query_entry.pack(pady=10)

        self.web_search_var = ctk.BooleanVar(value=False)
        self.web_switch = ctk.CTkSwitch(tab, text="Include Live Web Search (DuckDuckGo)", variable=self.web_search_var)
        self.web_switch.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(tab, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

        self.search_btn = ctk.CTkButton(tab, text="Launch Deep Scan", fg_color="#2ecc71", command=self.run_aggregator)
        self.search_btn.pack(pady=10)

        self.results_frame = ctk.CTkScrollableFrame(tab, width=850, height=450, label_text="Live Results")
        self.results_frame.pack(pady=10, fill="both", expand=True)

    def setup_autofill_tab(self):
        tab = self.tabview.tab("Auto-Fill Tool")
        self.url_entry = ctk.CTkEntry(tab, placeholder_text="Application URL will appear here", width=600)
        self.url_entry.pack(pady=20)

        self.fill_btn = ctk.CTkButton(tab, text="Apply Now (Auto-Fill)", command=self.start_autofill,
                                      fg_color="#3498db")
        self.fill_btn.pack(pady=10)

        self.log_box = ctk.CTkTextbox(tab, width=800, height=400, fg_color="#1a1a1a")
        self.log_box.pack(pady=10)

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text="Your Profile Info (Saved Locally)", font=("Arial", 16, "bold")).pack(pady=20)

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

    # --- LOGIC: AGGREGATOR ---
    def add_result_card(self, site, title, url):
        card = ctk.CTkFrame(self.results_frame)
        card.pack(pady=5, padx=10, fill="x")

        info = f"SOURCE: {site}\nTITLE: {title[:60]}..."
        ctk.CTkLabel(card, text=info, justify="left", font=("Arial", 11)).pack(side="left", padx=15, pady=10)

        ctk.CTkButton(card, text="Apply", width=100, command=lambda u=url: self.transfer_url(u)).pack(side="right",
                                                                                                      padx=15)

    def transfer_url(self, url):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)
        self.tabview.set("Auto-Fill Tool")
        self.log("URL received. Ready for Auto-Fill.")

    async def scrape_logic(self, query):
        all_results = []
        for widget in self.results_frame.winfo_children(): widget.destroy()

        self.progress_bar.set(0)
        total_steps = len(SITES) + (1 if self.web_search_var.get() else 0)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Step 1: Trusted Local Sites
            for i, site in enumerate(SITES):
                try:
                    await page.goto(site['url'], timeout=12000)
                    if query.lower() in (await page.content()).lower():
                        res = {"n": "Resource Found", "s": site['name'], "l": site['url']}
                        all_results.append(res)
                        self.after(0, lambda r=res: self.add_result_card(r['s'], r['n'], r['l']))
                except:
                    pass
                self.after(0, lambda v=(i + 1) / total_steps: self.progress_bar.set(v))

            # Step 2: DuckDuckGo Web Search
            if self.web_search_var.get():
                try:
                    with DDGS() as ddgs:
                        web_res = ddgs.text(f"{query} Spokane Washington", max_results=10)
                        for r in web_res:
                            res = {"n": r['title'], "s": "Live Web Search", "l": r['href']}
                            all_results.append(res)
                            self.after(0, lambda r=res: self.add_result_card(r['s'], r['n'], r['l']))
                except:
                    pass
                self.after(0, lambda: self.progress_bar.set(1.0))

            await browser.close()
            self.generate_html_dashboard(all_results)
            webbrowser.open(HTML_FILE)

    def generate_html_dashboard(self, results):
        cards_html = ""
        for r in results:
            cards_html += f"""
            <div class='card'>
                <h3>{r['n']}</h3>
                <p>Source: {r['s']}</p>
                <a href='{r['l']}' class='btn' target='_blank'>View Live Site</a>
            </div>"""

        template = f"""
        <html><head><style>
            body {{ background: #121212; color: #e0e0e0; font-family: sans-serif; padding: 40px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: #1e1e1e; padding: 20px; border-radius: 12px; border-left: 5px solid #3498db; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            h1 {{ color: #3498db; }}
            .btn {{ display: inline-block; margin-top: 10px; color: #3498db; text-decoration: none; font-weight: bold; }}
        </style></head><body>
            <h1>Spokane Resource Search Results</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <div class='grid'>{cards_html}</div>
        </body></html>"""

        with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(template)

    # --- LOGIC: AUTO-FILL ---
    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    async def autofill_logic(self, url):
        if not os.path.exists(SETTINGS_FILE):
            self.log("Error: Please save your settings first!")
            return

        with open(SETTINGS_FILE, "r") as f:
            user = json.load(f)

        self.log(f"Launching Auto-Fill for: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for review
            page = await browser.new_page()
            await page.goto(url)

            self.log("Scanning for form fields...")
            inputs = await page.query_selector_all('input')
            for btn in inputs:
                n = (await btn.get_attribute('name') or "").lower()
                i = (await btn.get_attribute('id') or "").lower()

                # Fill Text Fields
                if any(k in n or k in i for k in FIELD_MAP["first_name"]):
                    await btn.fill(user["name"])
                    self.log(f"Filled Name: {user['name']}")

                # Handle File Upload
                t = await btn.get_attribute('type')
                if t == "file" and any(k in n or k in i for k in FIELD_MAP["resume"]):
                    await btn.set_input_files(user["resume"])
                    self.log("Uploaded Resume!")

            self.log("Auto-fill complete. Please review and submit manually.")
            await asyncio.sleep(60)
            await browser.close()

    # --- THREADING HELPERS ---
    def run_aggregator(self):
        q = self.query_entry.get()
        if q: threading.Thread(target=lambda: asyncio.run(self.scrape_logic(q)), daemon=True).start()

    def start_autofill(self):
        u = self.url_entry.get()
        if u: threading.Thread(target=lambda: asyncio.run(self.autofill_logic(u)), daemon=True).start()

    def browse_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.res_path.delete(0, "end")
            self.res_path.insert(0, p)

    def save_settings(self):
        data = {"name": self.name_entry.get(), "email": self.email_entry.get(), "resume": self.res_path.get()}
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f)
        self.log("Profile settings saved locally.")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                d = json.load(f)
                self.name_entry.insert(0, d.get("name", ""))
                self.email_entry.insert(0, d.get("email", ""))
                self.res_path.insert(0, d.get("resume", ""))


if __name__ == "__main__":
    ensure_browser()
    app = ResourceHubPro()
    app.mainloop()