# ---------------------------------------------------------------------------------------------------------------

# Escopo de lib e API

import requests                               # Para fazer as requisições do HTML
from bs4 import BeautifulSoup
from pprint import pprint
from datetime import datetime
import pytz                                   # Python timezone
import pandas as pd                          # Tratar e viabilizar armazenamento dos dados 
import re                                     # Regular Expressions para a validação de cada uma das notícias
from keywords import KEYWORDS
from keywords import VALIDATION_KEYWORDS
from unidecode import unidecode               # Para formatar cada texto de cada notícia para tornar mais preciso o uso de RE
import os                                     # Para verificar existência de arquivo

# ---------------------------------------------------------------------------------------------------------------

# Método que carrega as URLs salvas em accepted_news.csv e unaccepted_news.csv
def get_all_urls():
    urls = []
    for arquivo in ["accepted_news.csv", "unaccepted_news.csv"]:
        if os.path.exists(arquivo):
            df = pd.read_csv(arquivo)
            
            columns = df['url'].tolist()
            urls.extend(columns)

    return set(urls)


# Classe do crawler (não há parâmetros a serem passados porque não estou usando herança)
class EstadaoSpider:

    def __init__(self, keyword, list):
        self.keyword = keyword
        self.noticias_aceitas = []
        self.noticias_recusadas = []
        self.noticias_salvas = []
        self.lista_urls = list
        self.noticias_salvas = get_all_urls()
        self.start_requests(self.lista_urls)

    # Método que faz a requisição para obter o HTML da página
    def start_requests(self, list):
        for url in list:
            response = requests.get(url)

            if response.status_code == 200:
                if url not in self.noticias_salvas:
                    print(f"Extraindo notícia da url: {url}")

                    self._parser(response.text, url)
                
                else:
                    print(f"[URL] {url} já foi processada. Pulando...")
                    continue
            else:
                print(f"Não foi possível acessar a url: {url}")
                
        self.load_news(self.noticias_aceitas)
        self.load_news(self.noticias_recusadas)
        self.print_news(self.noticias_aceitas + self.noticias_recusadas)

    # Método que só deve extrair o conteúdo desejado do HTML da notícia: OK
    # Método protected: não deve ser usado fora da classe
    def _parser (self, html, url):
        html_bs4 = BeautifulSoup(html, "html.parser")

        item = {}

        acquisition_date = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
        last_update = acquisition_date
        raw_publication_date = html_bs4.select_one("time").text
        date = raw_publication_date.strip()[:10] # Strip remove espaços ou quebras de linha invisíveis e slicing para pegar somente uma parte da data.
        title = html_bs4.select_one("h1").text

        raw_article = html_bs4.select_one("#content")
        paragrafos = ""
        paragrafo = raw_article.select_one("p")

        # Concantenação dos parágrafos das notícias
        while paragrafo:
            paragrafos = paragrafos + paragrafo.text

            # paragrafo = paragrafo.find_next("p") -> estava buscando qualquer parágrafo por todo o HTML a partir do elemento atual
            paragrafo = paragrafo.find_next_sibling("p") # Procura entre os irmãos do mesmo nível

        print("A URL foi totalmente extraída.")

        if self.validation_article(paragrafos):
            item["acquisition_date"] = acquisition_date
            item["publication_date"] = self.date_format(date)
            item["newspaper"] = "Estadao"
            item["accepted_by"] = self.validation_article(paragrafos)
            item["article"] = paragrafos
            item["keyword"] = self.keyword
            item["last_update"] = last_update
            item["title"] = title
            item["url"] = url
            item["tags"] = self.search_tags(paragrafos)
            item["manual_relevance_class"] = None
            item["gangs"] = self.search_gangs(paragrafos)

            self.noticias_aceitas.append(item)
        else:
            item["url"] = url
            self.noticias_recusadas.append(item)

        return f"Notícia cuja URL é {url} foi verificada."
    
    # Método para salvar notícia
    def load_news(self, noticias):
        data_frame = pd.DataFrame(noticias) # transforma a lista de notícias em um dataframe 

        if noticias == self.noticias_aceitas:
            if os.path.exists("accepted_news.csv"):
                db = pd.read_csv("accepted_news.csv")
                concatenar = pd.concat([data_frame, db])
                concatenar.to_csv("data/accepted_news.csv", index=False)

                # print("Banco já existe! Notícias aceitas adicionadas.")
            else:
                data_frame.to_csv("data/accepted_news.csv", index=False)
                # print(f"Banco não estava criado ainda. Notícias aceitas foram inseridas.")

        if noticias == self.noticias_recusadas:
            if os.path.exists("unaccepted_news.csv"):
                # print("Banco já existe! Notícias recusadas adicionadas.")
                db = pd.read_csv("unaccepted_news.csv")
                concatenar= pd.concat([data_frame, db])
                concatenar.to_csv("data/unaccepted_news.csv", index=False)
            else:
                data_frame.to_csv("data/unaccepted_news.csv", index=False)
                # print("Banco não estava criado ainda. Notícias não aceitas foram inseridas.")

    # Método que exibe cada uma das notícias de qualquer lista de notícias
    def print_news(self, list_news):
        for i in range (0, len(list_news)):
            pprint(list_news[i], sort_dicts=False)

    # Método que valida as palavras-chave: OK
    def validation_article(self, article):
        if not article: return False
        # Lógica de validação de primeira e segunda tabelas
        GANGS_NAMES = VALIDATION_KEYWORDS["GANGS"] + VALIDATION_KEYWORDS["ORGANIZED CRIME"]
        gang = False 
        for p in GANGS_NAMES:
            if re.findall(p, unidecode(article.lower()), re.I):
                gang = p; break
        
        activity = False
        GANGS_ACTIONS = VALIDATION_KEYWORDS["DRUGS"] + VALIDATION_KEYWORDS["ARMED INTERACTIONS"]
        for p in GANGS_ACTIONS:
            if re.findall(p, unidecode(article.lower()), re.I):
                activity = p; break
            
        return f"{gang} - {activity}" if (gang and activity) else False

    # Método que percorre o corpo da notícia buscando pelas gangues: OK
    def search_gangs(self, article):
        GANGS = KEYWORDS["GANGS"] + KEYWORDS["ORGANIZED CRIME"]
        gangs = []
        for p in GANGS:
            if re.findall(p, unidecode(article.lower()), flags=re.I):
                gangs.append(p); continue

        return gangs if gangs else []
    
    # Método que percorre o corpo da notícia buscando pelas tags (palavras características encontradas): OK
    def search_tags(self, article):
        TAGS = KEYWORDS["DRUGS"] + KEYWORDS["ARMED INTERACTIONS"]
        tags = []

        for p in TAGS:
            if re.findall(fr'{p}', unidecode(article.lower()), flags=re.I):
                tags.append(p); continue
        
        return tags if tags else []

    # Método que formata data dd/mm/aa para dd-mm-aa usando Regex: OK
    def date_format(self, date):
        date = re.sub(r'/', '-', date)
        
        return date
