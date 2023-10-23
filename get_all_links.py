import requests
from bs4 import BeautifulSoup

def find_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    return links

if __name__ == '__main__':
    website_url = 'https://www.yyyyyyy.info/'  # Замените на адрес своего сайта
    links = find_links(website_url)
    for link in links:
        print(link)
