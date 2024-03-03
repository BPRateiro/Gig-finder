import gzip
from bs4 import BeautifulSoup

# Exemplo de documento crawleado pelo scrapy
cached_file_path = 'gig_finder/.scrapy/httpcache/freelancer/0b/0b225578623802c0f03ecc1fdf4a342a7d9b2ddc/response_body'

with gzip.open(cached_file_path, 'rb') as compressed_file:
    soup = BeautifulSoup(compressed_file.read(), 'html.parser')

# print(soup.prettify())
print(soup.find('h1').text)