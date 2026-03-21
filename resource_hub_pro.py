import customtkinter as ctk
import asyncio
import threading
import json
import os
import sys
import re
import csv
import webbrowser
import winsound
import multiprocessing
from datetime import datetime
from playwright.async_api import async_playwright
from tkinter import filedialog, messagebox
from urllib.parse import quote

# --- CONFIGURATION ---
VERSION = "v2.5-GreenDot"
SETTINGS_FILE = "user_settings.json"

PRIORITY_COLORS = {
    "URGENT": "#e74c3c",
    "NORMAL": "#3498db",
    "LOW": "#95a5a6"
}


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# EXPANDED SITES: Added Job Search & Local Resource Hubs
SITES = [
    {"name": "SCC Workforce",
     "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs",
     "addr": "1810 N Greene St, Spokane, WA 99217"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/",
     "addr": "130 S Arthur St, Spokane, WA 99202"},
    {"name": "Craigslist Jobs", "url": "https://spokane.craigslist.org/search/jjj", "addr": "Spokane Area"},
    {"name": "Spokane Housing", "url": "https://www.spokanehousing.org/", "addr": "25 W Nora Ave, Spokane, WA 99205"},
    {"name": "SNAP Spokane", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/",
     "addr": "3102 W Fort George Wright Dr, Spokane, WA 99224"},
    {"name": "Catholic Charities", "url": "https://www.cceasternwa.org/housing",
     "addr": "12 E 5th Ave, Spokane, WA 99202"},
    {"name": "City of Spokane", "url": "https://my.spokanecity.org/chhs/resources/",
     "addr": "808 W Spokane Falls Blvd, Spokane, WA 99201"},
    {"name": "HSSA Spokane", "url": "https://hssaspokane.org/", "addr": "120 N Stevens St, Spokane, WA 99201"},
    {"name": "Indeed - Spokane", "url": "https://www.indeed.com/jobs?l=Spokane%2C+WA", "addr": "Remote/Various"},
    {"name": "LinkedIn - Spokane", "url": "https://www.linkedin.com/jobs/search/?location=Spokane%2C%20Washington",
     "addr": "Remote/Various"}
]


class ResourceHubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Spokane Resource Hub Pro - {VERSION}")
        self.geometry("1150x850")
        ctk.set_appearance_mode("dark")

        self.results_data = []  # Store findings for CSV export
        self.results_count = 0

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Resource Board")
        self.tabview.add("Settings")

        self.setup_board_tab()
        self.setup_settings_tab()

    def setup_board_tab(self):
        tab = self.tabview.tab("Resource Board")
        head_f = ctk.CTkFrame(tab, fg_color="transparent")
        head_f.pack(fill="x", pady=10)

        self.query_entry = ctk.CTkEntry(head_f, placeholder_text="Search (e.g. Python, Grant, Housing)...", width=450)
        self.query_entry.pack(side="left", padx=10)

        ctk.CTkButton(head_f, text="Launch Deep Scan", fg_color="#2ecc71", hover_color="#27ae60",
                      command=self.run_aggregator).pack(side="left", padx=5)
        ctk.CTkButton(head_f, text="Export CSV", fg_color="#34495e", command=self.export_to_csv).pack(side="left",
                                                                                                      padx=5)

        self.count_label = ctk.CTkLabel(head_f, text="Found: 0", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.count_label.pack(side="right", padx=20)

        self.progress_bar = ctk.CTkProgressBar(tab, width=900)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.results_frame = ctk.CTkScrollableFrame(tab, width=1100, height=600, fg_color="#1a1a1a")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def add_result_row(self, site, query, phone, priority):
        self.results_count += 1
        self.count_label.configure(text=f"Found: {self.results_count}")

        # Track data for export
        self.results_data.append([priority, site['name'], query, phone, site['url']])

        p_color = PRIORITY_COLORS.get(priority, "#808080")
        row = ctk.CTkFrame(self.results_frame, fg_color="#242424", height=60)
        row.pack(fill="x", pady=3, padx=5)

        ctk.CTkLabel(row, text=priority, text_color=p_color, font=("Arial", 11, "bold"), width=100).pack(side="left")
        ctk.CTkLabel(row, text=f"{query.upper()} OPPORTUNITY\n{site['name']}", justify="left", anchor="w",
                     width=400).pack(side="left", padx=20)
        ctk.CTkLabel(row, text=phone, width=150).pack(side="left")

        btn_f = ctk.CTkFrame(row, fg_color="transparent")
        btn_f.pack(side="right", padx=10)

        maps_url = f"https://www.google.com/maps/search/?api=1&query={quote(site['addr'])}"
        ctk.CTkButton(btn_f, text="Directions", width=80, fg_color="#444",
                      command=lambda: webbrowser.open(maps_url)).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Apply", width=80, fg_color="#3498db",
                      command=lambda: webbrowser.open(site['url'])).pack(side="left", padx=2)

    async def scrape_logic(self, query):
        if not query: return

        self.results_count = 0
        self.results_data = []
        self.after(0, lambda: self.count_label.configure(text="Found: 0"))
        self.after(0, lambda: [w.destroy() for w in self.results_frame.winfo_children()])
        self.after(0, lambda: self.progress_bar.set(0))

        exec_path = None
        if getattr(sys, 'frozen', False):
            browser_dir = resource_path(os.path.join("playwright", "driver", "package", ".local-browsers"))
            if os.path.exists(browser_dir):
                for f in os.listdir(browser_dir):
                    if f.startswith("chromium-"):
                        exec_path = os.path.join(browser_dir, f, "chrome-win", "chrome.exe")
                        break

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, executable_path=exec_path)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            urgent_keywords = ["grant", "deadline", "emergency", "urgent", "immediate", "hiring now"]

            async def process_site(site):
                try:
                    page = await context.new_page()
                    await page.goto(site['url'], timeout=25000, wait_until="domcontentloaded")
                    content = await page.content()

                    if query.lower() in content.lower():
                        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
                        phone_str = phone_match.group(0) if phone_match else "See Site"
                        priority = "URGENT" if any(kw in content.lower() for kw in urgent_keywords) else "NORMAL"

                        self.after(0, lambda: self.add_result_row(site, query, phone_str, priority))
                    await page.close()
                except:
                    pass
                finally:
                    self.after(0, lambda: self.progress_bar.set(self.progress_bar.get() + (1 / len(SITES))))

            await asyncio.gather(*[process_site(s) for s in SITES])
            await browser.close()
            self.after(0, lambda: self.progress_bar.set(1.0))
            winsound.MessageBeep()

    def run_aggregator(self):
        def start_loop():
            asyncio.run(self.scrape_logic(self.query_entry.get()))

        threading.Thread(target=start_loop, daemon=True).start()

    def export_to_csv(self):
        if not self.results_data:
            messagebox.showwarning("No Data", "Perform a scan first to collect results.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                                 initialfile=f"Spokane_Resources_{datetime.now().strftime('%Y%m%d')}.csv")
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Priority", "Site Name", "Query", "Phone", "URL"])
                writer.writerows(self.results_data)
            messagebox.showinfo("Success", f"Data exported to {file_path}")

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text=f"Spokane Scraper {VERSION}", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(
            pady=20)
        ctk.CTkLabel(tab, text="SCC Software Development - AAS Program").pack()
        ctk.CTkLabel(tab, text="Target: Acer Aspire 14 AI Deployment").pack(pady=10)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if getattr(sys, 'frozen', False):
        multiprocessing.set_start_method('spawn', force=True)
    app = ResourceHubPro()
    app.mainloop()