import requests
from bs4 import BeautifulSoup
import time
import random
from langdetect import detect
import csv

import numpy as np
import re
import pandas as pd


class scraper:
    def __init__(self, max_recurse, num_articles, max_article_length, desired_lang, root_url, csv_path):
        self.recursion_depth = max_recurse
        self.num_articles = num_articles
        self.desired_lang = desired_lang
        self.max_length = max_article_length
        self.seed_url = root_url
        self.num_reads = 0
        self.sink = csv_path
        self.csv_filename = csv_path
        self.base_url = '/'.join(root_url.split('/')[:3])
        self.visited = set()

        with open(self.sink, 'w', newline= '', encoding='utf-8') as f:
            file = csv.DictWriter(f, ["url","content","word_count"])
            file.writeheader()

    def get_response(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def in_desired_lang(self, text):
        print(text)
        if(len(text)>=2): # ensuring text is not a special character
            try:
                detected_lang = detect(text)
                return detected_lang == self.desired_lang
            except Exception as e:
                print(f"Language detection error: {e}")
                return False
        else:
            print(text)
            print(f"Error while detecting the language")
            return False

    def get_title(self, page):
        if not page:
            return None
        
        title = page.find('h1', id="firstHeading")

        if not title:
            content = page.find('div', class_='mw-parser-output')
            if content:
                for p in content.find_all('p', recursive=False):
                    text = p.get_text(strip=True)
                    if text:
                        sentences = text.split('. ')
                        return sentences[0] + ('.' if sentences else ' ')
                return content.get_text(strip=True).split('. ')[0] + '.'
            
            print("found an invalid page")
            return None
        
        return title.text

    def extract_info(self, page, url):

        if not page:
            return None
        
        content = page.find('div', class_='mw-parser-output')

        if content:
            full_text = ""
            word_count = 0
            min_words_for_points = 5 # ensuring that special characters (or) single characters are not read
            for element in content.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                if word_count >= self.max_length:
                    break

                else:
                    if element.get('class') in ['mw-references', 'reflist']:
                        continue

                    if element.name == 'li':
                        text = element.get_text(strip=True)
                        words = text.split()
                        if len(words) < min_words_for_points:
                            continue
                        parent = element.find_parent(['ul', 'ol'])
                        prefix = '- ' if parent and parent.name == 'ul' else '1. '
                        text = f"{prefix}{text}"
                    else:
                        text = element.get_text(strip=True)

                    if text:
                        words = text.split()
                        remaining_words = self.max_length - word_count
                        
                        if len(words) <= remaining_words:
                            full_text += text + "\n"
                            word_count += len(words)
                        else:
                            truncated_words = words[:remaining_words]
                            full_text += " ".join(truncated_words) + "\n"
                            word_count = self.max_length
                            break

            if full_text.strip():
                return { 'url': url, 'content': full_text.strip(), 'word_count': word_count }
        
        return {'url': url, 'content': "no content found", 'word_count': word_count}

    def get_links(self, page):
        if not page:
            return []
        
        links = []
        content = page.find('div', class_='mw-parser-output')
        if content:
            for a_tag in content.find_all('a', href=True):
                href = a_tag['href']
                if (href.startswith('/wiki/') and not ':' in href and not href.startswith('/wiki/Main_Page')):
                    full_url = self.base_url + href
                    display_text = a_tag.get_text(strip=True) or full_url.split('/')[-1]
                    links.append((display_text, full_url))

        return links 
    
    def preprocess_text(self, text):
        if not isinstance(text, str) or not text.strip():
            return ""
        
        # Step 1: Split text into sentences/segments (handling newlines and points)
        segments = text.replace('\n', ' ').split(' ')
        
        # Step 2: Keep only Hindi text
        hindi_text = []
        for segment in segments:
            if segment.strip():
                try:
                    if detect(segment) == 'hi':
                        hindi_text.append(segment)
                except:
                    continue
        
        # Rejoin segments into a single string
        text = ' '.join(hindi_text)
        
        # Step 3: Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Step 4: Remove text in parentheses
        text = re.sub(r'\([^()]*\)', '', text)
        
        # Step 5: Remove double quotes
        text = text.replace('"', '')
        
        # Step 6: Remove special characters (keep Hindi characters and spaces)
        # Hindi Unicode range: \u0900-\u097F
        text = re.sub(r'[^\u0900-\u097F\s]', '', text)
        
        # Step 7: Remove extra spaces and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def write_to_csv(self, info):
        with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'content', 'word_count'])
            writer.writerow(info)

    def DFS(self, url, current_depth=0):
        if((url in self.visited) or (self.num_reads >= self.num_articles)):
            return
        
        self.visited.add(url)

        page = self.get_response(url)
        if not page:
            return
        
        title = self.get_title(page)
        if not title:
            return
        
        lang = self.in_desired_lang(title)
        if(not lang):
            print(f"Skipping the url, Language detected is different from desired.")
            return
        
        print(f"Depth {current_depth}: Scraping {title}")
        article_info = self.extract_info(page, url)

        if article_info:
            preprocessed_text = self.preprocess_text(article_info["content"])
            self.write_to_csv({"url":article_info["url"], "content":preprocessed_text, "word_count": article_info["word_count"]})
            self.num_reads += 1

        if self.num_reads >= self.num_articles:
            return
        
        links = self.get_links(page)
        
        if current_depth < self.recursion_depth:  
            for display_text, next_url in links:
                if self.num_reads < self.num_articles:
                    print(f"Scraping {display_text}")
                    self.DFS(next_url, current_depth + 1)  # Go deeper
        
    def fire(self):
        self.DFS(self.seed_url)