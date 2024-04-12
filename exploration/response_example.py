import gzip
from bs4 import BeautifulSoup

# Exemplo de documento crawleado pelo scrapy
cached_file_path = r'gig_finder\.scrapy\httpcache\freelancer\1b\1bf48bd5e368b3707a9139469ada52755b368b02\response_body'

with gzip.open(cached_file_path, 'rb') as compressed_file:
    soup = BeautifulSoup(compressed_file.read(), 'html.parser')

# Caso queira consultar o documento todo
# print(soup.prettify())

# Deve imprimir o título 'Web Application Development Specialist
print(soup.find('h1').text)