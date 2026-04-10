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
VERSION = "v3.6-OneClick-Dashboard"
PROFILE_FILE = "user_profile.json"

PRIORITY_COLORS = {"URGENT": "#e74c3c", "NORMAL": "#3498db"}

SITES = [
    {"name": "SCC Workforce Grants", "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs", "addr": "1810 N Greene St, Spokane, WA 99217"},
    {"name": "WorkSource Spokane (Jobs/Expo)", "url": "https://worksourcespokane.com/", "addr": "130 S Arthur St, Spokane, WA 99202"},
    {"name": "SNAP Energy/Housing", "url": "https://www.snapenergyassistance.org/", "addr": "3102 W Fort George Wright Dr, Spokane, WA 99224"},
    {"name": "City of Spokane CHHS (Shelter)", "url": "https://my.spokanecity.org/chhs/funding-opportunities/", "addr": "808 W Spokane Falls Blvd, Spokane, WA 99201"},
    {"name": "The Arc of Spokane (Disability)", "url": "https://www.arcspokane.org/supported-employment", "addr": "320 E 2nd Ave, Spokane, WA 99202"},
    {"name": "Second Harvest (Food)", "url": "https://2-harvest.org/get-help-spokane/", "addr": "1234 E Front Ave, Spokane, WA 99202"},
    {"name": "UGM Spokane (Shelter/Food)", "url": "https://www.uniongospelmission.org/get-help", "addr": "1224 E Trent Ave, Spokane, WA 99202"},
    {"name": "WA Dept of Vocational Rehab", "url": "https://www.dshs.wa.gov/dvr", "addr": "1313 N Atlantic St, Spokane, WA 99201"},
    {"name": "Skils'kin (Employment)", "url": "https://www.skils-kin.org/employment-services", "addr": "4004 E Boone Ave, Spokane, WA 99202"},
    {"name": "Indeed - Spokane Jobs", "url": "https://www.indeed.com/jobs?l=Spokane%2C+WA", "addr": "Remote/Various"},
    {"name": "Bold.org Scholarships", "url": "https://bold.org/scholarships/second-chance-scholarship/", "addr": "Remote/Various"}
]

class ResourceHubPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Spokane Resource Hub Pro - {VERSION}")
        self.geometry("1150x850")
        ctk.set_appearance_mode("dark")
        ctk.set_widget_scaling(1.1)

        self.results_data = []
        self.results_count = 0
        self.load_profile()

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tabview.add("Resource Board")
        self.tabview.add("My Profile")
        self.tabview.add("Settings")

        self.setup_board_tab()
        self.setup_profile_tab()
        self.setup_settings_tab()

    def load_profile(self):
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r") as f: self.user_data = json.load(f)
        else: self.user_data = {"first_name": "", "last_name": "", "email": "", "phone": "", "portfolio": ""}

    def save_profile(self):
        self.user_data = {k: getattr(self, f"ent_{k[:4]}").get() for k in ["first_name", "last_name", "email", "phone", "portfolio"]}
        with open(PROFILE_FILE, "w") as f: json.dump(self.user_data, f)
        messagebox.showinfo("Success", "Profile Saved!")

    def setup_board_tab(self):
        tab = self.tabview.tab("Resource Board")
        
        # --- QUICK ACTION DASHBOARD ---
        dash_f = ctk.CTkFrame(tab, fg_color="transparent")
        dash_f.pack(fill="x", pady=(10, 5))
        
        actions = [
            ("💰 Grants", "#2ecc71"), ("💼 Jobs", "#3498db"), 
            ("🏠 Housing", "#9b59b6"), ("🍎 Food", "#e67e22"), 
            ("♿ Disability", "#f1c40f"), ("⛺ Shelter", "#e74c3c")
        ]
        
        for text, color in actions:
            btn = ctk.CTkButton(dash_f, text=text, fg_color=color, width=120, height=35,
                                font=("Arial", 12, "bold"),
                                command=lambda t=text.split()[-1]: self.quick_search(t))
            btn.pack(side="left", padx=5)

        # --- SEARCH HEADER ---
        head_f = ctk.CTkFrame(tab, fg_color="transparent")
        head_f.pack(fill="x", pady=10)

        self.query_entry = ctk.CTkEntry(head_f, placeholder_text="Or type custom search here...", width=450)
        self.query_entry.pack(side="left", padx=10)
        self.query_entry.bind("<Return>", lambda e: self.run_aggregator())

        ctk.CTkButton(head_f, text="Launch Deep Scan", fg_color="#2ecc71", command=self.run_aggregator).pack(side="left", padx=5)
        self.count_label = ctk.CTkLabel(head_f, text="Found: 0", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.count_label.pack(side="right", padx=20)

        self.progress_bar = ctk.CTkProgressBar(tab, width=900)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.spinner = ctk.CTkProgressBar(tab, width=400, mode="indeterminate")

        self.results_frame = ctk.CTkScrollableFrame(tab, width=1100, height=600, fg_color="#1a1a1a")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def quick_search(self, term):
        self.query_entry.delete(0, 'end')
        self.query_entry.insert(0, term)
        self.run_aggregator()

    def setup_profile_tab(self):
        tab = self.tabview.tab("My Profile")
        f = ctk.CTkFrame(tab, fg_color="transparent")
        f.pack(pady=40)
        self.ent_firs = self.make_entry(f, "First Name", 1, "first_name")
        self.ent_last = self.make_entry(f, "Last Name", 2, "last_name")
        self.ent_emai = self.make_entry(f, "Email", 3, "email")
        self.ent_phon = self.make_entry(f, "Phone", 4, "phone")
        self.ent_port = self.make_entry(f, "Portfolio Link", 5, "portfolio")
        ctk.CTkButton(f, text="Update Profile", fg_color="#2ecc71", command=self.save_profile).grid(row=6, columnspan=2, pady=30)

    def make_entry(self, master, label, row, key):
        ctk.CTkLabel(master, text=label).grid(row=row, column=0, padx=20, pady=10, sticky="e")
        entry = ctk.CTkEntry(master, width=300)
        entry.insert(0, self.user_data.get(key, ""))
        entry.grid(row=row, column=1, padx=20, pady=10)
        return entry

    async def auto_apply_logic(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_context().new_page()
            await page.goto(url, wait_until="networkidle")
            field_map = {"first_name": ["fname", "first"], "last_name": ["lname", "last"], "email": ["email", "mail"], "phone": ["phone", "tel"]}
            for key, aliases in field_map.items():
                val = self.user_data.get(key)
                if val:
                    selector = ", ".join([f'input[name*="{a}" i], input[id*="{a}" i]' for a in aliases])
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        await page.fill(selector, val)
                    except: pass

    def add_result_row(self, site, priority):
        self.results_count += 1
        self.count_label.configure(text=f"Found: {self.results_count}")
        row = ctk.CTkFrame(self.results_frame, fg_color="#242424", height=70)
        row.pack(fill="x", pady=3, padx=5); row.pack_propagate(False)
        ctk.CTkLabel(row, text=priority, text_color=PRIORITY_COLORS.get(priority), font=("Arial", 11, "bold"), width=100).pack(side="left")
        ctk.CTkLabel(row, text=site['name'].upper(), anchor="w", width=400).pack(side="left", padx=20)
        btn_f = ctk.CTkFrame(row, fg_color="transparent")
        btn_f.pack(side="right", padx=10)
        ctk.CTkButton(btn_f, text="Auto-Apply", width=90, fg_color="#3498db", command=lambda u=site['url']: threading.Thread(target=lambda: asyncio.run(self.auto_apply_logic(u)), daemon=True).start()).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Map", width=70, fg_color="#444", command=lambda u=f"http://google.com/maps/search/{quote(site['addr'])}": webbrowser.open(u)).pack(side="left", padx=2)

    async def scrape_logic(self, query):
        self.after(0, lambda: [self.progress_bar.set(0), [w.destroy() for w in self.results_frame.winfo_children()]])
        self.results_count = 0
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=50)
            context = await browser.new_context(user_agent="Mozilla/5.0 Chrome/122.0.0.0")
            
            keywords = [query.lower(), "rfp", "funding", "assistance", "opportunity", "hunger", "emergency", "vocational", "dvr"]
            
            for site in SITES:
                page = await context.new_page()
                try:
                    await page.goto(site['url'], timeout=25000, wait_until="domcontentloaded")
                    content = await page.evaluate("() => document.body.innerText")
                    if any(kw in content.lower() for kw in keywords):
                        pr = "URGENT" if "deadline" in content.lower() or "closed" in content.lower() else "NORMAL"
                        self.after(0, lambda s=site, p=pr: self.add_result_row(s, p))
                except: pass
                finally:
                    await page.close()
                    self.after(0, lambda: self.progress_bar.set(self.progress_bar.get() + (1/len(SITES))))
            await browser.close()
            self.after(0, lambda: [self.spinner.stop(), self.spinner.pack_forget()])
            winsound.Beep(1000, 200)

    def run_aggregator(self):
        q = self.query_entry.get().strip()
        if q:
            self.spinner.pack(after=self.progress_bar, pady=5); self.spinner.start()
            threading.Thread(target=lambda: asyncio.run(self.scrape_logic(q)), daemon=True).start()

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text=f"Resource Hub Pro {VERSION}", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(pady=20)

if __name__ == "__main__":
    multiprocessing.freeze_support(); app = ResourceHubPro(); app.mainloop()