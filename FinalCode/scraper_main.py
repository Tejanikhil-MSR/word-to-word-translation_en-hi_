import argparse
import web_scraper_cpu as ws

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Wikipedia Scraper")
    
    parser.add_argument("--max_recurse", type=int, default=10, help="Max recursion depth for crawling")
    parser.add_argument("--num_articles", type=int, default=4, help="Number of articles to scrape")
    parser.add_argument("--max_length", type=int, default=500, help="Max words per article")
    parser.add_argument("--desired_lang", type=str, default="hi", help="Desired language (e.g., 'hi' for Hindi)")
    parser.add_argument("--root_url", type=str, default="https://en.wikipedia.org", help="Root URL to start scraping")
    parser.add_argument("--csv_path", type=str, default="scraped_data.csv", help="Path to save the scraped data")

    args = parser.parse_args()

    
    my_scraper = ws.scraper(
        max_recurse=args.max_recurse,
        num_articles=args.num_articles,
        max_article_length=args.max_length,
        desired_lang=args.desired_lang,
        root_url=args.root_url,
        csv_path=args.csv_path
    )

    my_scraper.fire()