from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse,urljoin
from io import BytesIO

class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        self.obj_scheduler = obj_scheduler




    def request_url(self,obj_url):
        """
            Faz a requisição e retorna o conteúdo em binário da URL passada como parametro

            obj_url: Instancia da classe ParseResult com a URL a ser requisitada.
        """
        user_agent = {'user-agent': 'coletor-grupo-4'} 
        response = requests.get(obj_url,headers = user_agent)
        if response.status_code == 200 and "text/html" in response.headers["content-type"]:
            return BytesIO(response.content)
        else: 
            response = None

        return response.content

    def discover_links(self,obj_url,int_depth,bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content,features="lxml")
        for link in soup.select(None):
            obj_new_url = None
            int_new_depth = None

            yield obj_new_url,int_new_depth


    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        pass

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        pass
