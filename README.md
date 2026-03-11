# 🌲 Spokane Resource Scraper

A Python-based web scraper designed to help students and community members in Spokane, WA, find local grants, housing, and career resources in real-time.

## 🚀 Overview
I built this tool to automate the search for critical community resources. It currently targets high-impact local organizations and provides a "Priority" alert system for urgent deadlines.

**Targeted Resources:**
* **SCC Workforce Transitions** (Opportunity Grants, FAFSA/WASFA)
* **WorkSource Spokane** (Job opportunities & training)
* **SNAP Spokane** (Housing & rental assistance)
* **Pioneer Human Services** (Career reentry)

## ✨ Key Features
* **Live Web Scraping:** Uses `BeautifulSoup` to pull direct links from official Spokane agency websites.
* **Priority Alerts:** Automatically flags resources with upcoming deadlines as **[URGENT]**.
* **CSV Export:** Saves all findings to a `spokane_resources.csv` file for easy tracking in Excel.
* **Polite Scraping:** Implements `time.sleep` to ensure respectful interaction with local servers.

## 🛠️ Tech Stack
* **Language:** Python 3.12+
* **Libraries:** `requests`, `beautifulsoup4`, `csv`
* **Environment:** PyCharm Professional

## 📥 Installation & Usage
To run this project locally on your machine:

1. **Clone the repo:**
   ```bash
   git clone [https://github.com/KeeganVT/Spokane-Resource-Scraper.git](https://github.com/KeeganVT/Spokane-Resource-Scraper.git)
