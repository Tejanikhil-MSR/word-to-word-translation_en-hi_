import requests
from bs4 import BeautifulSoup
import time
import random
from langdetect import detect
import csv

from numba import cuda
import numpy as np
import re
import pandas as pd

@cuda.jit
def kernel_process(input_array, output_array, text_lengths):
    idx = cuda.grid(1)  # Get the thread index
    if idx < input_array.shape[0]:  # Ensure thread is within bounds
        out_idx = 0  # Output index tracker
        
        for i in range(text_lengths[idx]):
            char_code = input_array[idx, i]  # Get Unicode value of character
            
            # Keep only Hindi characters (Unicode range \u0900-\u097F) and spaces
            if (0x0900 <= char_code <= 0x097F) or char_code == 32:
                if out_idx < output_array.shape[1]:  # Ensure we don't exceed output buffer
                    output_array[idx, out_idx] = char_code
                    out_idx += 1

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
        self.visited = set()

        with open(self.sink, 'w', newline= '', encoding='utf-8') as f:
            file = csv.DictWriter(f, ["url","content","word_count"])
            file.writeheader()

    def get_response(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                        return sentences[0] + ('.' if sentences else '')
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
        text = page.find('div', class_='mw-parser-output')
        if text:
            for a_tag in text.find_all('a', href=True):
                
                href = a_tag['href']
                is_wiki_link = href.startswith('/wiki/')
                is_main_page = not href.startswith('/wiki/Main_Page')
                is_special_page = ':' in href # Since i am getting some unwanted pages of this format
                
                if (is_wiki_link and not is_special_page and not is_main_page):
                    full_url = self.seed_url + href
                    display_text = a_tag.get_text(strip=True) or full_url.split('/')[-1]
                    links.append((display_text, full_url))
                    
        return links  
    
    def preprocess_text(self, content):
        if not content:
            return []   
    
        # Filtering all the Hindi text on CPU itself (since langdetect isn't GPU-friendly)
        hindi_texts = []
        for text in content:
            if not isinstance(text, str) or not text.strip():
                hindi_texts.append("")
                continue
            segments = text.replace('\n', ' ').split(' ')
            hindi_segments = [
                                seg for seg in segments 
                                if seg.strip() and len(seg) > 2 and detect(seg) == 'hi'
                             ]

            hindi_texts.append(' '.join(hindi_segments))
        
        # Offloading the regular-expression preprocessing to gpu
        max_len = max(len(t) for t in hindi_texts)
        text_array = np.zeros((len(hindi_texts), max_len), dtype=np.uint8)
        text_lengths = np.zeros(len(hindi_texts), dtype=np.int32)

        for i, text in enumerate(hindi_texts):
            encoded = np.array([ord(c) for c in text], dtype=np.int32)
            text_array[i, :len(encoded)] = encoded
            text_lengths[i] = len(encoded)
        
        output_array = np.zeros_like(text_array)
        # d_text_array = cuda.to_device(text_array)
        # d_out_array = cuda.device_array((len(hindi_texts), max_len), dtype=np.uint8)
        # text_lengths = np.array([len(t) for t in hindi_texts], dtype=np.int32)
        # d_text_lengths = cuda.to_device(text_lengths)
        
        # Configure CUDA grid and blocks
        threads_per_block = 256
        blocks_per_grid = (text_array.shape[0] + threads_per_block - 1) // threads_per_block 
        
        kernel_process[blocks_per_grid, threads_per_block](text_array, output_array, text_lengths)
        cuda.synchronize()
        print(cuda.current_context().get_memory_info())  # Prints GPU memory stats
        print("Kernel execution completed successfully!") 

        # Copy results back to CPU
        out_array = output_array

        result = ["".join(chr(c) for c in row if c > 0) for row in out_array]
        print(result)
        return result

    def write_to_csv(self, info):
        with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['url', 'content', 'word_count'])
            writer.writerow(info)

    def DFS(self, url, current_depth=0):
        if((url in self.visited) or (self.num_reads >= self.num_articles)):
            print("i am here")
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
            print(f"Skipping the url : {url} Language detected is different from desired.")
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
                    time.sleep(random.uniform(1, 3))
                    print(f"Scraping {display_text}")
                    self.dfs_scrape(next_url, current_depth + 1)  # Go deeper

    def fire(self, seed_url):
        self.DFS(seed_url)