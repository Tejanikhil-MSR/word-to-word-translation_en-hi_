import sys
sys.setrecursionlimit(5000) 


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

        if(len(text)>=2): # ensuring text is not a special character
            try:
                detected_lang = detect(text)
                print(detected_lang)
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
        
        full_text = []
        word_count = 0
        min_words_for_points = 5  # Ignore very short list items

        content_containers = page.find_all('div', class_=re.compile(r'mw-parser-output'))

        coordinate_keywords = ['coordinates', 'geo', 'geo-dec', 'latitude', 'longitude']
        
        # I dont want the coordinates to be extracted
        def is_coordinate_related(tag):
            if not tag:
                return False
            cls = tag.get('class') or []
            tag_id = tag.get('id') or ''
            return any(kw in cls for kw in coordinate_keywords) or any(kw in tag_id for kw in coordinate_keywords)


        # Iterate over all content containers and extract content
        for content in content_containers:
            for element in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span'], recursive=True):
                
                if word_count >= self.max_length:
                    break
                
                # Skip coordinates explicitly
                if is_coordinate_related(element):
                    continue

                if element.find_parent(['table', 'div'], class_=lambda c: c and ('infobox' in c or 'navbox' in c or 'coordinates' in c or 'mw-indicator' in c)):
                    continue

                if element.get('class') and ('mw-references' in element.get('class') or 'reflist' in element.get('class')):
                    continue

                text = element.get_text()

                # Handling list items separately
                if element.name == 'li':
                    words = text.split()
                    if len(words) < min_words_for_points:
                        continue
                    parent = element.find_parent(['ul', 'ol'])
                    prefix = '- ' if parent and parent.name == 'ul' else '1. '
                    text = f"{prefix}{text}"
                
                if text:
                    words = text.split()
                    remaining_words = self.max_length - word_count
                    if len(words) <= remaining_words:
                        full_text.append(text)
                        word_count += len(words)
                    else:
                        full_text.append(" ".join(words[:remaining_words]))
                        word_count = self.max_length
                        break  # Stop when limit is reached

        return {'url': url, 'content': "\n".join(full_text).strip(), 'word_count': word_count }

    def get_links(self, page):
        if not page:
            return []
        
        links = []
        for link in page.find_all('a', href=True):
            href = link['href']
            # Filter out help or wikipedia account related links
            if (href.startswith('/wiki/') and not ':' in href and not href.startswith('/wiki/Main_Page')):
                full_link = f"https://{self.desired_lang}.wikipedia.org{href}"
                display_text = link.get_text(strip=True) or full_link.split('/')[-1]
                links.append((display_text, full_link))
                   

        return links 
    
    def preprocess_text(self, text):
        if not isinstance(text, str) or not text.strip():
            return ""
        
        segments = text.replace('\n', ' ').split(' ')
        
        desired_text = []
        for segment in segments:
            desired_text.append(segment)
                
        text = ' '.join(desired_text)
        
        text = re.sub(r'\d+', '', text)
        
        text = re.sub(r'\([^()]*\)', '', text)
        
        text = text.replace('"', '')
        
        if(self.desired_lang=="hi"):
            text = re.sub(r'[^\u0900-\u097F\s]', '', text)
        elif(self.desired_lang=="en"):
            text = re.sub(r'[^A-Za-z\s]', '', text)

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
        
        # if(self.desired_lang=="hi"): # Check only if the desired_language is hindi
        #     lang = self.in_desired_lang(title)
        #     print(title, lang)
        #     if(not lang):
        #         print(f"Skipping the url, {title} Language detected is different from desired {lang}.")
        #         return
        
        print(f"Depth {current_depth}: Scraping {title}")
        article_info = self.extract_info(page, url)

        if article_info:
            print(url)
            preprocessed_text = self.preprocess_text(article_info["content"])
            self.write_to_csv({"url":article_info["url"], "content":preprocessed_text, "word_count": article_info["word_count"]})
            self.num_reads += 1

        if self.num_reads >= self.num_articles:
            return
        
        links = self.get_links(page)
        random.shuffle(links)
        
        if current_depth < self.recursion_depth:  
            for display_text, next_url in links:
                if self.num_reads < self.num_articles:
                    self.DFS(next_url, current_depth + 1)  # Go deeper
        
    def fire(self):
        self.DFS(self.seed_url)