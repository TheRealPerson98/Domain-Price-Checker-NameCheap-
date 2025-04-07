from bs4 import BeautifulSoup
import time
import json
import csv
import os
import sys
import subprocess
import signal
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from colorama import init, Fore, Style
import threading
import concurrent.futures
import datetime
from utils.tohtml import generate_html_output

init()

import logging
logging.getLogger('selenium').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
os.environ['CHROME_DRIVER_SILENT_OUTPUT'] = "1"

class SilentChromeDriver(webdriver.Chrome):
    def __init__(self, options=None, service=None):
        if service is None:
            service = Service(log_path=os.devnull)
        
        if options is None:
            options = Options()
        
        startupinfo = None
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            service.creation_flags = subprocess.CREATE_NO_WINDOW
        
        service._handle_process = lambda *args, **kwargs: subprocess.Popen(
            *args, 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            startupinfo=startupinfo,
            **kwargs
        )
        
        super().__init__(options=options, service=service)

def ensure_directories():
    directories = [
        "data",
        "data/images",
        "data/temp"
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            log_info(f"Created directory: {directory}")

def log_info(message):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def log_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def log_warning(message):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def log_error(message):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

print_lock = threading.Lock()

def progress_bar(seconds, domain):
    with print_lock:
        print(f"{Fore.YELLOW}Starting check for {domain}...{Style.RESET_ALL}")
    
    time.sleep(seconds)
    
    with print_lock:
        print(f"{Fore.YELLOW}Completed loading {domain} after {seconds}s{Style.RESET_ALL}")

stop_execution = False
save_screenshots = False
generate_html_report = False

def signal_handler(sig, frame):
    global stop_execution
    print(f"\n{Fore.RED}Stopping execution... (please wait for current operations to complete){Style.RESET_ALL}")
    stop_execution = True

def check_namecheap_price(domain):
    global stop_execution, save_screenshots
    
    if stop_execution:
        return "Stopped"
        
    driver = None
    try:
        with print_lock:
            log_info(f"Checking domain: {domain}")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = SilentChromeDriver(options=chrome_options)
        
        driver.get(f"https://www.namecheap.com/domains/registration/results/?domain={domain}")
        
        wait_time = 15
        progress_bar(wait_time, domain)
        
        if stop_execution:
            return "Stopped"
            
        if save_screenshots:
            screenshot_path = os.path.join("data/images", f"{domain.replace('.', '_')}.png")
            driver.save_screenshot(screenshot_path)
        
        page_source = driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        exact_domain_name = domain.lower()
        exact_domain_selector = f"article[class*='{exact_domain_name.split('.')[-1]}']"
        
        articles = soup.select(exact_domain_selector)
        exact_match_found = False
        
        for article in articles:
            domain_h2 = article.find("h2")
            if domain_h2 and domain_h2.text.strip().lower() == exact_domain_name:
                exact_match_found = True
                
                if 'unavailable' in article.get('class', []):
                    unavailable_text = "Unavailable"
                    span_label = article.select_one('span.label')
                    if span_label:
                        unavailable_text = span_label.text.strip()
                    
                    with print_lock:
                        log_warning(f"Exact domain {domain} is unavailable: {unavailable_text}")
                    
                    alternatives = []
                    alternative_articles = soup.find_all("article", class_=lambda c: c and "available" in c)
                    
                    for alt_article in alternative_articles:
                        alt_h2 = alt_article.find("h2")
                        if alt_h2:
                            alt_domain = alt_h2.text.strip()
                            alt_price_div = alt_article.find("div", class_="price")
                            if alt_price_div and alt_price_div.find("strong"):
                                alt_price = alt_price_div.find("strong").text.strip()
                                alternatives.append((alt_domain, alt_price))
                    
                    if alternatives:
                        with print_lock:
                            log_info(f"Found alternatives available for purchase")
                        
                        alt_domain, alt_price = alternatives[0]
                        return f"Unavailable ({unavailable_text}). Alternative: {alt_domain} - {alt_price}"
                    
                    return f"Unavailable ({unavailable_text})"
                
                price_div = article.find("div", class_="price")
                if price_div and price_div.find("strong"):
                    price = price_div.find("strong").text.strip()
                    with print_lock:
                        log_success(f"Found available domain: {domain_h2.text} - {price}")
                    return price
        
        if not exact_match_found:
            available_articles = soup.find_all("article", class_=lambda c: c and "available" in c)
            
            if available_articles:
                alt_results = []
                for article in available_articles:
                    domain_h2 = article.find("h2")
                    if domain_h2:
                        alt_domain = domain_h2.text.strip()
                        price_div = article.find("div", class_="price")
                        if price_div and price_div.find("strong"):
                            price = price_div.find("strong").text.strip()
                            alt_results.append((alt_domain, price))
                
                if alt_results:
                    with print_lock:
                        log_warning(f"Exact domain {domain} not found, but found alternatives")
                    
                    alt_domain, price = alt_results[0]
                    return f"Exact domain not found. Alternative: {alt_domain} - {price}"
            
            unavailable_articles = soup.find_all("article", class_=lambda c: c and "unavailable" in c)
            for article in unavailable_articles:
                domain_h2 = article.find("h2")
                if domain_h2 and domain_h2.text.strip().lower() == exact_domain_name:
                    span_label = article.select_one('span.label')
                    unavailable_text = "Unavailable"
                    if span_label:
                        unavailable_text = span_label.text.strip()
                    
                    with print_lock:
                        log_warning(f"Domain {domain} is unavailable: {unavailable_text}")
                    return f"Unavailable ({unavailable_text})"
        
        with print_lock:
            log_warning(f"No information found for domain {domain}")        
        return "No information found"
        
    except Exception as e:
        with print_lock:
            log_error(f"Error checking {domain}: {str(e)}")
        return f"Error: {str(e)}"
    finally:
        if driver:
            driver.quit()

def bulk_check(domains, batch_size=5):
    global stop_execution
    results = {}
    
    for i in range(0, len(domains), batch_size):
        if stop_execution:
            log_warning("Stopping domain checks as requested...")
            break
            
        batch = domains[i:i + batch_size]
        log_info(f"\n{Fore.MAGENTA}===== Processing batch {i//batch_size + 1}/{(len(domains) + batch_size - 1)//batch_size} ====={Style.RESET_ALL}")
        
        batch_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_domain = {executor.submit(check_namecheap_price, domain): domain for domain in batch}
            
            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    price = future.result()
                    
                    if price == "Stopped":
                        continue
                        
                    batch_results[domain] = price
                    
                    status_color = Fore.GREEN if price != "Unavailable" and not price.startswith("Error") else Fore.YELLOW
                    with print_lock:
                        log_info(f"{status_color}Result: {domain}: {price}{Style.RESET_ALL}")
                except Exception as exc:
                    with print_lock:
                        log_error(f"Domain {domain} generated an exception: {exc}")
                    batch_results[domain] = f"Error: {exc}"
                
                if stop_execution:
                    break
        
        results.update(batch_results)
        
        save_to_csv(results, os.path.join("data/temp", "domain_prices_partial.csv"))
        
        if not stop_execution:
            log_info(f"Completed batch {i//batch_size + 1}. Pausing before next batch...")
            time.sleep(2)
            
    return results

def save_to_csv(results, filename="domain_prices.csv"):
    if "/" not in filename and "\\" not in filename:
        filename = os.path.join("data", filename)
        
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Domain', 'Price'])
        for domain, price in results.items():
            writer.writerow([domain, price])
    log_info(f"Results saved to {filename}")

def cleanup_temp_files():
    temp_dir = os.path.join("data", "temp")
    if os.path.exists(temp_dir):
        log_info(f"Cleaning up temporary files in {temp_dir}...")
        count = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    count += 1
            except Exception as e:
                log_error(f"Error deleting {file_path}: {e}")
        log_success(f"Cleaned up {count} temporary files")
    else:
        log_warning(f"Temp directory {temp_dir} not found, nothing to clean up")

try:
    with open('domains.json', 'r') as file:
        domains_to_check = json.load(file)
        if not isinstance(domains_to_check, list):
            log_error("Error: domains.json should contain a list of domain names")
            exit(1)
except FileNotFoundError:
    log_error("Error: domains.json file not found")
    exit(1)
except json.JSONDecodeError:
    log_error("Error: domains.json contains invalid JSON")
    exit(1)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    ensure_directories()
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.CYAN}  DOMAIN PRICE CHECKER - Namecheap")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    while True:
        screenshot_choice = input(f"{Fore.CYAN}Do you want to save domain screenshots? (y/n): {Style.RESET_ALL}").lower().strip()
        if screenshot_choice in ['y', 'yes']:
            save_screenshots = True
            log_info("Screenshots will be saved to data/images directory")
            break
        elif screenshot_choice in ['n', 'no']:
            save_screenshots = False
            log_info("Screenshots will not be saved")
            break
        else:
            log_error("Please enter 'y' or 'n'")
    
    while True:
        html_choice = input(f"{Fore.CYAN}Do you want to generate an HTML report? (y/n): {Style.RESET_ALL}").lower().strip()
        if html_choice in ['y', 'yes']:
            generate_html_report = True
            log_info("HTML report will be generated")
            break
        elif html_choice in ['n', 'no']:
            generate_html_report = False
            log_info("HTML report will not be generated")
            break
        else:
            log_error("Please enter 'y' or 'n'")
    
    log_info(f"Loaded {len(domains_to_check)} domains from domains.json")
    log_info("Starting domain checks with Selenium (this may take time to load each page)...")
    log_info(f"{Fore.YELLOW}Press Ctrl+C to stop the process at any time{Style.RESET_ALL}")
    
    try:
        results = bulk_check(domains_to_check)
        if stop_execution:
            log_warning("Process was stopped by user")
        else:
            log_success("All domains processed successfully!")
        
        save_to_csv(results)
        
        if generate_html_report and results:
            html_path = generate_html_output(results, save_screenshots)
            log_success(f"HTML report generated: {html_path}")
    finally:
        cleanup_temp_files() 