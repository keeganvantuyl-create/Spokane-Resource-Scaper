# Spokane Reentry Resource Aggregator
**Empowering formerly incarcerated individuals through automated resource discovery.**

## 🎯 The Mission
The first 72 hours after release are critical. This tool is designed to bridge the gap between incarceration and stability by aggregating real-time resources in Spokane, WA, specifically targeting:
* **Housing:** Low-barrier and transitional housing.
* **Employment:** Reentry-friendly employers and workforce training (Pioneer, WorkSource).
* **Recovery:** Instant access to local support groups (NA/AA) with fallback logic for high-reliability.
* **Transportation:** Accessible bus pass programs.

## 🛠️ How it Works
This Python-based tool uses **BeautifulSoup** and **Requests** to scrape local government and non-profit websites. It features:
* **Graceful Degradation:** Hardcoded fallback resources for essential services when external sites are unreachable.
* **Priority Logic:** Automatically flags resources with upcoming deadlines as "URGENT."
* **CSV Export:** Generates a portable list that case managers and individuals can use offline.

## 🚀 Future Roadmap
* **API Integration:** Transitioning from scraping to official APIs (CareerOneStop) for deeper job data.
* **SMS Alerts:** Notifying users of new grant or housing openings.
* **Mapping:** Visualizing resources near Spokane transit centers.

*Built by Keegan Van Tuyl - Software Development Student at SCC.*
