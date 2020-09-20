from urllib import robotparser
from code.util import synchronized
from collections import OrderedDict
from .domain import Domain
import urllib.robotparser
import time
from typing import List, Tuple

class Scheduler():
    #tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 20

    def __init__(self,str_usr_agent: str, int_page_limit: int,
                int_depth_limit: int, arr_urls_seeds: List):
        """
            Inicializa o escalonador. Atributos:
            :parram - `str_usr_agent`: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
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

    def has_finished_crawl(self) -> bool:
        """
            Verifica se finalizou a coleta
            :parram - None
            :return - boolean com o status da finalização crawl
        """

        if(self.int_page_count > self.int_page_limit):
            return True
        return False

    @synchronized
    def can_add_page(self, obj_url: Tuple, int_depth: int) -> bool:
        """
            Retorna verdadeiro caso  profundade for menor que a maxima,
            a url não foi descoberta ainda ou se o path não esteja entre
            o dominio da url
            :parram - obj_url : Tupla com informações referentes a url apresentada 
                                (scheme, netloc, path, query)
                    - int_depth : valor apresentando a profundidade desejada para a url
            :return - boolean com a resposta à possibilidade de adição da url 
        """
        if int_depth < self.int_depth_limit:
            # Caso a profundidade da url esteja dentro do limite

            if obj_url.netloc not in self.set_discovered_urls:
                # Caso a url inserida (sem path) nao esteja entre as urls descobertas, retore true
                return True

            else:
                # Caso a url inserida (sem path) esteja entre as urls descobertas, verifica se
                # o path inserido está contido no dominio url descoberta.

                for url_elements in self.dic_url_per_domain[obj_url.netloc]:
                    if (obj_url, int_depth) == url_elements:
                        # Caso o path inserido esteja dentro do dominio da url, retorne false 
                        return False

                else:
                    # Caso o Loop For conclua e não encontre o path no dominio, retorne true
                    return True

        return False

    @synchronized
    def add_new_page(self, obj_url: Tuple, int_depth: int) -> bool:
        """
            Adiciona uma nova página
            :parram - obj_url : Objeto da classe ParseResult com a URL a ser adicionada
                    - int_depth : valor apresentando a profundidade desejada para a url
            :return - boolean com a resposta de possibilidade de declaração de nova pagina
        """
        #https://docs.python.org/3/library/urllib.parse.html

        if self.can_add_page(obj_url,int_depth) is True:
            # Caso seja possivel adicionar a pagina, criar um dominio com a url desejada (sem path)

            new_page_requested = Domain(obj_url.netloc, self.TIME_LIMIT_BETWEEN_REQUESTS)
            if new_page_requested not in self.dic_url_per_domain.keys():
                # Caso o dominio declarado não esteja dentro da fila (dic_url_per_domain),
                # adiciona-lo na lista, coloca-lo como descoberto e retornar true

                self.dic_url_per_domain[new_page_requested] = [(obj_url, int_depth)]
                self.set_discovered_urls.add(obj_url.netloc)
                return True

            else:
                # Caso o dominio declarado esteja dentro da fila, adicionar o path
                # apresentado no dominio presente da fila e retornar true

                self.dic_url_per_domain[new_page_requested].append((obj_url, int_depth))
                return True
            
        return False


    @synchronized
    def get_next_url(self) -> Tuple:
        """
            Obtem uma nova URL path por meio da fila. Essa URL path é removida da fila.
            Logo após, caso o servidor não tenha mais URLs path, o mesmo também é removido.
            :parram - None
            :return - Tupla com as informações da url desejada com seu path
        """

        next_url = (None, None)
        checked_key = None

        for key, value in self.dic_url_per_domain.items():
            # Loop com chave e valor do dicionario
            
            if key.is_accessible():
                # Caso a chave esteja disponivel, mudando seu estado de acessibilidade,
                # armazenando a chave utilizada e verificando se a chave possui valor 

                key.accessed_now()
                checked_key = key
                if value:
                    # Caso a chave possua valor URL Path, armazenar seu primeiro valor, retira-lo dos
                    # values do dicionário e sair do look

                    next_url = value[0]
                    value.pop(0)
                    break

        else:
            # Caso o loop termine e não haja mais URLs, aguarde certo tempo para proxima interação
            time.sleep(21)

        if checked_key:
            # Caso a busca anterior tenha capturado uma chave

            if not self.dic_url_per_domain[checked_key]:
                # Caso o valor presente da chave capturada esteja vazio, deleta essa chave do dicionario
                del self.dic_url_per_domain[checked_key]

        return next_url

    def can_fetch_page(self, obj_url: Tuple) -> bool:
        """
            Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
            :parram - obj_url - Objeto da classe ParseResult com a URL a ser adicionada
            :return - boolean apresentando a possibilidade de coleta da pagina (True/False)
        """

        if obj_url.netloc in self.dic_robots_per_domain.keys():
            # Caso a URL esteja dentro da lista de URLs já verificadas para fetch,
            # Retorne seu valor na lista
            return self.dic_robots_per_domain[obj_url.netloc]

        url = "https://" + obj_url.netloc + "/robots.txt"               # URL formatada
        self.RP.set_url(url)                                            # Definindo a url para leitura
        url_response = self.RP.can_fetch(self.str_usr_agent, url)       # Capturand a resposta da possibilidade de fetch da URL
        self.RP.read()

        # Retornando a resposta apresentada pela requisição (True/False)
        # E armazenando em uma fila de histórico
        if url_response:
            self.dic_robots_per_domain[obj_url.netloc] = True
            return True
        else:
            self.dic_robots_per_domain[obj_url.netloc] = False
            return False
