import urllib

from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import os
import requests
import shutil


def remove_thumbnail_suffix(url):
    new_url = re.sub(r'/thumb', '', url)
    new_url = re.sub(r'/[0-9]+px-.+\.(jpg|png|gif)$', '', new_url)
    return new_url


def download_image(url, folder, image_number, highres):
    if highres:
        modified_url = remove_thumbnail_suffix(url)
        try:
            response = requests.get(modified_url, stream=True, headers={'User-agent': 'bot 0.1'})
        except urllib.error.HTTPError:
            response = requests.get(url, stream=True, headers={'User-agent': 'bot 0.1'})
    else:
        response = requests.get(url, headers={'User-agent': 'bot 0.1'}, stream=True)

    filename = os.path.join(folder, f"image{image_number:03}.jpg")
    with open(filename, 'wb') as f:
        shutil.copyfileobj(response.raw, f)


def get_english_label(row, label_col):
    try:
        cells = row.find_elements(By.TAG_NAME, f'td')
        label = ''.join(c for c in cells[label_col].text if c.isalpha() or c == " ").replace("  ",
                                                                                             " ")
        return label.lower()
    except Exception as e:
        return "not an image"


def get_caption_from_img_element(img_element):
    try:
        parent_element = img_element.find_element(By.XPATH, '..')
        while parent_element.tag_name.lower() != 'figure':
            parent_element = parent_element.find_element(By.XPATH, '..')
            if parent_element.tag_name.lower() == 'html':
                raw = img_element.get_attribute("alt")
                label = ''.join(c for c in raw if c.isalpha() or c == " ").replace("  ", " ")
                return label.lower()

        caption_element = parent_element.find_element(By.TAG_NAME, 'figcaption')
        raw = caption_element.text
        label = ''.join(c for c in raw if c.isalpha() or c == " ").replace("  ", " ")
        return label.lower()

    except Exception as e:
        return ""


def is_data(label, img_url):
    stopwords = ['wiki', "not an image", "encyclopedia", "icon"]
    return all(x not in label for x in stopwords) and label and img_url


def get_rows(table):
    headers = table.find_element(By.TAG_NAME, 'tr').find_elements(By.TAG_NAME, 'th')
    name_cols = ("English", "Name", "English name")
    try:
        label_col = next(i for i, header in enumerate(headers) if header.text in name_cols)
    except StopIteration:
        label_col = 0

    rows = table.find_elements(By.TAG_NAME, 'tr')
    return label_col, rows


def scrape_wikipedia(url, name, folder, highres):
    data_dir = os.path.join(folder, name)
    os.makedirs(data_dir, exist_ok=True)
    driver = webdriver.Chrome()
    driver.get(url)
    tables = driver.find_elements(By.CLASS_NAME, 'wikitable')
    labels = []
    image_number = 1
    urls = set()
    n_tot = 0
    for table in tables:
        label_col, rows = get_rows(table)
        n = len(rows)
        n_tot += n

    every_tot = 0
    every = n_tot / 100.0
    num_prints = 1
    if 0 < every < 1:
        num_prints = int(1.0 / every)
    i = -1
    for table in tables:
        label_col, rows = get_rows(table)
        for row in rows:
            i += 1
            if i > every_tot:
                print("|" * num_prints, end="")
                every_tot += every
            images = row.find_elements(By.TAG_NAME, 'img')
            for img in images:
                label = get_english_label(row, label_col)
                img_url = img.get_attribute('src')
                if is_data(label, img_url):
                    labels.append(label)
                    download_image(img_url, data_dir, image_number, highres=highres)
                    image_number += 1
                    urls.add(img_url)
    else:
        print("|" * 100, end="")

    with open(os.path.join(data_dir, "labels.txt"), 'w') as f:
        for label in labels:
            f.write(label + "\n")

    driver.quit()


def scrape_wikipedia_sites(sites_list_filename, folder, highres=False):
    for site in open(sites_list_filename).readlines():
        name = site.split("/")[-1].strip()
        print("\nName:", name)
        scrape_wikipedia(site, name, folder, highres=highres)
