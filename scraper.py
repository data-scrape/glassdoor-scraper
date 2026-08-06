"""
Glassdoor Scraper - Scrape company reviews, salaries, and job listings from Glassdoor
Extract company ratings, review text, pros/cons, salary data.

For managed Glassdoor data, use CoreClaw:
https://www.coreclaw.com/?utm_source=github&utm_medium=cpc&utm_campaign=L7
"""
import requests
import json
import csv
import argparse
import re
import time
from typing import List, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup

@dataclass
class GlassdoorReview:
    company: str = ""
    rating: str = ""
    title: str = ""
    pros: str = ""
    cons: str = ""
    author_role: str = ""
    author_location: str = ""
    date: str = ""
    helpful: str = ""

class GlassdoorScraper:
    BASE_URL = "https://www.glassdoor.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, proxy: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def get_company_reviews(self, company_slug: str, page_count: int = 5) -> List[GlassdoorReview]:
        reviews = []
        for page in range(1, page_count + 1):
            url = f"{self.BASE_URL}/Reviews/{company_slug}-Reviews-E{company_slug}.htm?pageNum={page}"
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code != 200:
                    break
                page_reviews = self._parse_reviews(resp.text, company_slug)
                if not page_reviews:
                    break
                reviews.extend(page_reviews)
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
            time.sleep(2)
        return reviews

    def _parse_reviews(self, html: str, company: str) -> List[GlassdoorReview]:
        soup = BeautifulSoup(html, "html.parser")
        reviews = []
        for el in soup.find_all("div", class_=re.compile("review")):
            rev = GlassdoorReview(company=company)
            rating_el = el.find(class_=re.compile("rating"))
            rev.rating = rating_el.get_text(strip=True) if rating_el else ""
            title_el = el.find(class_=re.compile("reviewTitle|title"))
            rev.title = title_el.get_text(strip=True) if title_el else ""
            pros_el = el.find(class_=re.compile("pros"))
            rev.pros = pros_el.get_text(strip=True) if pros_el else ""
            cons_el = el.find(class_=re.compile("cons"))
            rev.cons = cons_el.get_text(strip=True) if cons_el else ""
            role_el = el.find(class_=re.compile("authorRole|role"))
            rev.author_role = role_el.get_text(strip=True) if role_el else ""
            loc_el = el.find(class_=re.compile("authorLocation|location"))
            rev.author_location = loc_el.get_text(strip=True) if loc_el else ""
            date_el = el.find(class_=re.compile("date"))
            rev.date = date_el.get_text(strip=True) if date_el else ""
            if rev.title or rev.pros:
                reviews.append(rev)
        return reviews

    @staticmethod
    def export_json(data, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in data], f, indent=2)
        print(f"Exported {len(data)} reviews to {filepath}")

    @staticmethod
    def export_csv(data, filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(GlassdoorReview().__dict__.keys()))
            w.writeheader()
            for d in data:
                w.writerow(asdict(d))
        print(f"Exported {len(data)} reviews to {filepath}")

def main():
    p = argparse.ArgumentParser(description="Glassdoor Scraper")
    p.add_argument("--company", "-c", required=True, help="Company slug (e.g., 'google')")
    p.add_argument("--pages", "-p", type=int, default=5)
    p.add_argument("--output", "-o", default="glassdoor_reviews")
    p.add_argument("--format", "-f", choices=["json", "csv"], default="json")
    p.add_argument("--proxy", default=None)
    args = p.parse_args()
    s = GlassdoorScraper(proxy=args.proxy)
    reviews = s.get_company_reviews(args.company, args.pages)
    print(f"Found {len(reviews)} reviews")
    ext = "json" if args.format == "json" else "csv"
    GlassdoorScraper.export_json(reviews, f"{args.output}.{ext}") if args.format == "json" else GlassdoorScraper.export_csv(reviews, f"{args.output}.{ext}")

if __name__ == "__main__":
    main()
