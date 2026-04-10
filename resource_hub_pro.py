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
VERSION = "v3.1-Production-Ready"
SETTINGS_FILE = "user_settings.json"
PROFILE_FILE = "user_profile.json"

PRIORITY_COLORS = {
    "URGENT": "#e74c3c",
    "NORMAL": "#3498db",
    "LOW": "#95a5a6"
}

SITES = [
    {"name": "SCC Workforce", "url": "https://scc.spokane.edu/For-Our-Students/Student-Resources/Specially-Funded-Programs", "addr": "1810 N Greene St, Spokane, WA 99217"},
    {"name": "WorkSource Spokane", "url": "https://worksourcespokane.com/job-seekers/job-opportunities/", "addr": "130 S Arthur St, Spokane, WA 99202"},
    {"name": "SNAP Spokane", "url": "https://www.snapwa.org/rental-housing-information-resources-and-support/", "addr": "3102 W Fort George Wright Dr, Spokane, WA 99224"},
    {"name": "Spokane County HCD", "url": "https://www.spokanecounty.gov/5944/2026-HCD-RFPs", "addr": "1101 W College Ave, Spokane, WA 99260"},
    {"name": "Indeed - Spokane", "url": "https://www.indeed.com/jobs?l=Spokane%2C+WA", "addr": "Remote/Various"},
    {"name": "Bold Second Chance Grant", "url": "https://bold.org/scholarships/second-chance-scholarship/", "addr": "Remote/Various"}
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

    # --- PROFILE MANAGEMENT ---
    def load_profile(self):
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r") as f:
                self.user_data = json.load(f)
        else:
            self.user_data = {"first_name": "", "last_name": "", "email": "", "phone": "", "portfolio": ""}

    def save_profile(self):
        self.user_data = {
            "first_name": self.ent_fname.get(),
            "last_name": self.ent_lname.get(),
            "email": self.ent_email.get(),
            "phone": self.ent_phone.get(),
            "portfolio": self.ent_port.get()
        }
        with open(PROFILE_FILE, "w") as f:
            json.dump(self.user_data, f)
        messagebox.showinfo("Success", "Profile saved! Auto-Apply is now ready.")

    # --- UI TABS ---
    def setup_board_tab(self):
        tab = self.tabview.tab("Resource Board")
        head_f = ctk.CTkFrame(tab, fg_color="transparent")
        head_f.pack(fill="x", pady=10)

        self.query_entry = ctk.CTkEntry(head_f, placeholder_text="Search (Grant, CRP, Workforce)...", width=450)
        self.query_entry.pack(side="left", padx=10)
        self.query_entry.bind("<Return>", lambda e: self.run_aggregator())

        ctk.CTkButton(head_f, text="Launch Deep Scan", fg_color="#2ecc71", command=self.run_aggregator).pack(side="left", padx=5)
        ctk.CTkButton(head_f, text="Export CSV", fg_color="#34495e", command=self.export_to_csv).pack(side="left", padx=5)

        self.count_label = ctk.CTkLabel(head_f, text="Found: 0", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.count_label.pack(side="right", padx=20)

        self.progress_bar = ctk.CTkProgressBar(tab, width=900)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.results_frame = ctk.CTkScrollableFrame(tab, width=1100, height=600, fg_color="#1a1a1a")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_profile_tab(self):
        tab = self.tabview.tab("My Profile")
        f = ctk.CTkFrame(tab, fg_color="transparent")
        f.pack(pady=40)

        ctk.CTkLabel(f, text="Auto-Fill Identity", font=("Arial", 24, "bold"), text_color="#2ecc71").grid(row=0, columnspan=2, pady=20)
        
        self.ent_fname = self.make_entry(f, "First Name", 1)
        self.ent_lname = self.make_entry(f, "Last Name", 2)
        self.ent_email = self.make_entry(f, "Email", 3)
        self.ent_phone = self.make_entry(f, "Phone", 4)
        self.ent_port = self.make_entry(f, "Portfolio/GitHub", 5)

        # Pre-fill from loaded data
        self.ent_fname.insert(0, self.user_data.get("first_name", ""))
        self.ent_lname.insert(0, self.user_data.get("last_name", ""))
        self.ent_email.insert(0, self.user_data.get("email", ""))
        self.ent_phone.insert(0, self.user_data.get("phone", ""))
        self.ent_port.insert(0, self.user_data.get("portfolio", ""))

        ctk.CTkButton(f, text="Update Profile", fg_color="#2ecc71", command=self.save_profile).grid(row=6, columnspan=2, pady=30)

    def make_entry(self, master, label, row):
        ctk.CTkLabel(master, text=label).grid(row=row, column=0, padx=20, pady=10, sticky="e")
        entry = ctk.CTkEntry(master, width=300)
        entry.grid(row=row, column=1, padx=20, pady=10)
        return entry

    # --- LOGIC & AUTOMATION ---
    async def auto_apply_logic(self, url):
        field_map = {
            "first_name": ["fname", "firstname", "first_name", "given-name"],
            "last_name": ["lname", "lastname", "last_name", "family-name"],
            "email": ["email", "user_email", "mail"],
            "phone": ["phone", "tel", "mobile", "contact"]
        }
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False) 
            page = await browser.new_context().new_page()
            await page.goto(url)
            for key, aliases in field_map.items():
                val = self.user_data.get(key)
                if not val: continue
                selector = ", ".join([f'input[name*="{a}" i], input[id*="{a}" i]' for a in aliases])
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.fill(selector, val)
                except: pass

    def trigger_auto_apply(self, url):
        threading.Thread(target=lambda: asyncio.run(self.auto_apply_logic(url)), daemon=True).start()

    def add_result_row(self, site, query, phone, priority):
        self.results_count += 1
        self.count_label.configure(text=f"Found: {self.results_count}")
        self.results_data.append([priority, site['name'], query, phone, site['url']])

        p_color = PRIORITY_COLORS.get(priority, "#808080")
        row = ctk.CTkFrame(self.results_frame, fg_color="#242424", height=70)
        row.pack(fill="x", pady=3, padx=5)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text=priority, text_color=p_color, font=("Arial", 11, "bold"), width=100).pack(side="left")
        ctk.CTkLabel(row, text=f"{site['name'].upper()}", justify="left", anchor="w", width=350).pack(side="left", padx=20)
        
        btn_f = ctk.CTkFrame(row, fg_color="transparent")
        btn_f.pack(side="right", padx=10)

        ctk.CTkButton(btn_f, text="Auto-Apply", width=90, fg_color="#3498db", command=lambda u=site['url']: self.trigger_auto_apply(u)).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="Map", width=70, fg_color="#444", command=lambda u=f"https://www.google.com/maps/search/{quote(site['addr'])}": webbrowser.open(u)).pack(side="left", padx=2)

    async def scrape_logic(self, query):
        if not query: return
        self.after(0, lambda: [self.count_label.configure(text="Found: 0"), self.progress_bar.set(0), [w.destroy() for w in self.results_frame.winfo_children()]])
        self.results_count = 0
        self.results_data = []
        sem = asyncio.Semaphore(5)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            async def process_site(site):
                async with sem:
                    page = await context.new_page()
                    try:
                        await page.goto(site['url'], timeout=12000, wait_until="domcontentloaded")
                        content = await page.evaluate("() => document.body.innerText")
                        if query.lower() in content.lower():
                            priority = "URGENT" if "deadline" in content.lower() else "NORMAL"
                            self.after(0, lambda s=site, q=query, pr=priority: self.add_result_row(s, q, "N/A", pr))
                    except: pass
                    finally:
                        await page.close()
                        self.after(0, lambda: self.progress_bar.set(self.progress_bar.get() + (1 / len(SITES))))
            
            await asyncio.gather(*[process_site(s) for s in SITES])
            await browser.close()
            winsound.Beep(1000, 200)

    def run_aggregator(self):
        query = self.query_entry.get().strip()
        if not query: return
        threading.Thread(target=lambda: asyncio.run(self.scrape_logic(query)), daemon=True).start()

    def export_to_csv(self):
        if not self.results_data: return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Priority", "Site Name", "Query", "Phone", "URL"])
                writer.writerows(self.results_data)

    def setup_settings_tab(self):
        tab = self.tabview.tab("Settings")
        ctk.CTkLabel(tab, text=f"Resource Hub Pro {VERSION}", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(pady=20)
        ctk.CTkLabel(tab, text="Optimized for Acer Aspire 14 AI Hardware").pack()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = ResourceHubPro()
    app.mainloop()