import customtkinter as ctk
import asyncio
import threading
import json
import os
import sys
import re
import webbrowser
import winsound
import multiprocessing
from datetime import datetime
from playwright.async_api import async_playwright
from tkinter import filedialog, messagebox
from urllib.parse import quote

# --- CONFIGURATION ---
VERSION = "v2.4-GreenDot"
SETTINGS_FILE = "user_settings.json"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


SITES = [
    {"name": "SCC Workforce",
     "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs",
     "addr": "1810 N Greene St, Spokane, WA 99217"},
    {"name": "Spokane Housing", "url": "https://www.spokanehousing.org/", "addr": "25 W Nora Ave, Spokane, WA 99205"},
    {"name": "SNAP Spokane", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/",
     "addr": "3102 W Fort George Wright Dr, Spokane, WA 99224"},
    {"name": "WorkSource", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/",
     "addr": "130 S Arthur St, Spokane, WA 99202"},
    {"name": "Catholic Charities", "url": "https://www.cceasternwa.org/housing",
     "addr": "12 E 5th Ave, Spokane, WA 99202"},
    {"name": "City of Spokane", "url": "https://my.spokanecity.org/chhs/resources/",
     "addr": "808 W Spokane Falls Blvd, Spokane, WA 99201"},
    {"name": "HSSA Spokane", "url": "https://hssaspokane.org/", "addr": "120 N Stevens St, Spokane, WA 99201"}
]


class ResourceHubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Spokane Resource Hub Pro - {VERSION}")
        self.geometry("1150x850")
        ctk.set_appearance_mode("dark")
        self.results_count = 0

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Resource Board");
        self.tabview.add("Settings")

        self.setup_board_tab()
        self.setup_settings_tab()

    def setup_board_tab(self):
        tab = self.tabview.tab("Resource Board")
        head_f = ctk.CTkFrame(tab, fg_color="transparent")
        head_f.pack(fill="x", pady=10)

        self.query_entry = ctk.CTkEntry(head_f, placeholder_text="Search (e.g. Grant, Housing, Job)...", width=450)
        self.query_entry.pack(side="left", padx=10)

        ctk.CTkButton(head_f, text="Launch Deep Scan", fg_color="#2ecc71", command=self.run_aggregator).pack(
            side="left", padx=5)

        # Found Count Label
        self.count_label = ctk.CTkLabel(head_f, text="Found: 0", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.count_label.pack(side="right", padx=20)

        self.progress_bar = ctk.CTkProgressBar(tab, width=900);
        self.progress_bar.set(0);
        self.progress_bar.pack(pady=5)
        self.results_frame = ctk.CTkScrollableFrame(tab, width=1100, height=600, fg_color="#1a1a1a")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def add_result_row(self, site, query, phone, priority):
        self.results_count += 1
        self.count_label.configure(text=f"Found: {self.results_count}")

        p_color = "#e74c3c" if priority == "URGENT" else "#3498db"
        row = ctk.CTkFrame(self.results_frame, fg_color="#242424", height=60)
        row.pack(fill="x", pady=3, padx=5)

        ctk.CTkLabel(row, text=priority, text_color=p_color, font=("Arial", 11, "bold"), width=100).pack(side="left")
        ctk.CTkLabel(row, text=f"{query.upper()} OPPORTUNITY\n{site['name']}", justify="left", anchor="w",
                     width=400).pack(side="left", padx=20)
        ctk.CTkLabel(row, text=phone, width=150).pack(side="left")

        btn_f = ctk.CTkFrame(row, fg_color="transparent")
        btn_f.pack(side="right", padx=10)
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={quote(site['addr'])}"
        ctk.CTkButton(btn_f, text="Directions", width=80, fg_color="#444",
                      command=lambda: webbrowser.open(maps_url)).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Apply", width=80, fg_color="#3498db",
                      command=lambda: webbrowser.open(site['url'])).pack(side="left", padx=2)

    async def scrape_logic(self, query):
        if not query: return
        self.results_count = 0
        self.count_label.configure(text="Found: 0")
        for w in self.results_frame.winfo_children(): w.destroy()

        exec_path = None
        if getattr(sys, 'frozen', False):
            base = resource_path(os.path.join("playwright", "driver", "package", ".local-browsers"))
            if os.path.exists(base):
                for f in os.listdir(base):
                    if f.startswith("chromium-"):
                        exec_path = os.path.join(base, f, "chrome-win", "chrome.exe")
                        break

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, executable_path=exec_path)
            context = await browser.new_context()

            async def process_site(site):
                try:
                    page = await context.new_page()
                    await page.goto(site['url'], timeout=30000, wait_until="networkidle")
                    content = await page.content()
                    if query.lower() in content.lower():
                        phone = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', content)
                        phone_str = phone.group(0) if phone else "See Site"
                        priority = "URGENT" if any(
                            x in content.lower() for x in ["grant", "deadline", "emergency"]) else "NORMAL"
                        self.after(0, lambda: self.add_result_row(site, query, phone_str, priority))
                    await page.close()
                except:
                    pass

            await asyncio.gather(*[process_site(s) for s in SITES])
            await browser.close()
            self.after(0, lambda: self.progress_bar.set(1.0))
            winsound.MessageBeep()

    def run_aggregator(self):
        threading.Thread(target=lambda: asyncio.run(self.scrape_logic(self.query_entry.get())), daemon=True).start()

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text=f"Spokane Scraper {VERSION}").pack(pady=20)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if getattr(sys, 'frozen', False): multiprocessing.set_start_method('spawn', force=True)
    app = ResourceHubPro();
    app.mainloop()