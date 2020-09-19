from urllib import robotparser
from code.util import synchronized
from collections import OrderedDict
from .domain import Domain
import urllib.robotparser
import time

class Scheduler():
    #tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 20

    def __init__(self,str_usr_agent,int_page_limit,int_depth_limit,arr_urls_seeds):
        """
            Inicializa o escalonador. Atributos:
                - `str_usr_agent`: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
                - `int_page_limit`: Número de páginas a serem coletadas
                - `int_depth_limit`: Profundidade máxima a ser coletada
                - `int_page_count`: Quantidade de página já coletada
                - `dic_url_per_domain`: Fila de URLs por domínio (explicado anteriormente)
                - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
                - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas no `robots.txt`
        """
        self.str_usr_agent = str_usr_agent
        self.int_page_limit = int_page_limit    # Limite de Paginas
        self.int_depth_limit = int_depth_limit  # Profundidade da busca
        self.int_page_count = 0
        self.TIME_LIMIT_BETWEEN_REQUESTS = 20

        self.dic_url_per_domain = OrderedDict() # Dicionário com as URLs
        self.set_discovered_urls = set()        # URLs Descobertas
        self.dic_robots_per_domain = {}
        self.RP = urllib.robotparser.RobotFileParser()

        for element in arr_urls_seeds:
            self.dic_url_per_domain[Domain(element, self.TIME_LIMIT_BETWEEN_REQUESTS)] = []
        
    @synchronized
    def count_fetched_page(self):
        """
            Contabiliza o número de paginas já coletadas
        """
        self.int_page_count += 1

    def has_finished_crawl(self):
        """
            Verifica se finalizou a coleta
        """
        if(self.int_page_count > self.int_page_limit):
            return True
        return False


    @synchronized
    def can_add_page(self,obj_url,int_depth):
        """
            Retorna verdadeiro caso  profundade for menor que a maxima
            e a url não foi descoberta ainda
        """
        if int_depth < self.int_depth_limit:
            if obj_url.netloc not in self.set_discovered_urls:
                return True
            else:
                # Verificar se a url está presente na parte descoberta do dominio

                for url_elements in self.dic_url_per_domain[obj_url.netloc]:
                    if (obj_url, int_depth) == url_elements:
                        # Caso a URL com a preferencia estejam presentes no dominio, retorne falso
                        return False
                else:
                    # Caso o Loop For conclua e nao ache, retorne verdadeiro
                    return True

        return False

    @synchronized
    def add_new_page(self,obj_url,int_depth):
        """
            Adiciona uma nova página
            obj_url: Objeto da classe ParseResult com a URL a ser adicionada
            int_depth: Profundidade na qual foi coletada essa URL
        """
        #https://docs.python.org/3/library/urllib.parse.html

        if self.can_add_page(obj_url,int_depth) is True:
            # If True, getting creating a new Domain object and checking dic_url_per_domain.keys

            new_page_requested = Domain(obj_url.netloc, self.TIME_LIMIT_BETWEEN_REQUESTS)
            if new_page_requested not in self.dic_url_per_domain.keys():
                # Adding new page in url queue and dicovering this url

                self.dic_url_per_domain[new_page_requested] = [(obj_url, int_depth)]
                self.set_discovered_urls.add(obj_url.netloc)
                return True
            else:
                # Adicione mais uma url ao dominio desejado

                self.dic_url_per_domain[new_page_requested].append((obj_url, int_depth))
                return True
            
        return False


    @synchronized
    def get_next_url(self):
        """
        Obtem uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """

        next_url = (None, None)
        checked_key = None

        for key, value in self.dic_url_per_domain.items():
            
            if key.is_accessible():
                key.accessed_now()
                checked_key = key
                if value:
                    next_url = value[0]
                    value.pop(0)
                    break
            else:
               continue
        else:
            time.sleep(21)

        if checked_key:
            if not self.dic_url_per_domain[checked_key]:
                del self.dic_url_per_domain[checked_key]

        return next_url

    def can_fetch_page(self,obj_url):
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        """

        if obj_url.netloc in self.dic_robots_per_domain.keys():
            return self.dic_robots_per_domain[obj_url.netloc]

        url = "https://" + obj_url.netloc + "/robots.txt"
        self.RP.set_url(url)
        url_response = self.RP.can_fetch(self.str_usr_agent, url)
        self.RP.read()

        if url_response:
            self.dic_robots_per_domain[obj_url.netloc] = True
            return True
        else:
            self.dic_robots_per_domain[obj_url.netloc] = False
            return False
