from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import string

# Personagem [x]
# Nome [x]
# Raça [x]
# Técnicas [x]
# Saga []

class Bot():
    def __init__(self):
        # Extrair os Nomes e Links por página
        # self.extrair_personagens()
        # Extrair Todas as Técnicas
        # self.extrair_tecnicas()
        # Extrair Todas as Raças
        # self.extrair_sagas()
        pass

    def extrair_personagens(self):
        characters_url = "wiki/Category:Characters?from="
        for letra in string.ascii_uppercase:
            with sync_playwright() as p:
                navegador = p.chromium.launch(headless=False)
                pagina = navegador.new_page()
                pagina.goto(self.url(characters_url, letra))
                soup = BeautifulSoup(pagina.content(), "html.parser")
                nomes = soup.find_all("a", class_="category-page__member-link")
                
                for nome in nomes: 
                    # Tratamento dos Nomes
                    if "Category" not in nome.text[0:9]:
                        # Nomes
                        print(nome.text)
                        # Links 
                        link_character = nome.get("href")
                        pagina.goto(self.url(link_character, ""))
                        soup = BeautifulSoup(pagina.content(), "html.parser")
                        # Raça
                        raça = soup.find_all("div", {"data-source": "Race"})
                        for i in raça:
                            raça = i.find("div", class_="pi-data-value pi-font").text
                        
                        # Técnicas
                        # É necessário fazer uma comparação com as técnicas da database para validar a técnica
                        tecnicas = soup.find_all()
                        
                    else:
                        pass
    
    def extrair_sagas(self):
        sagas_url = "wiki/List_of_Sagas"
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=False)
            pagina = navegador.new_page()
            pagina.goto(self.url(sagas_url, ""))
            soup = BeautifulSoup(pagina.content(), "html.parser")
            sagas = soup.find_all("th", {"style": "background:#EE6C17; color:#ffffff"})
            for saga in sagas:
                saga = saga.text.strip()
                if saga not in ["Manga", "Anime"]:
                    print(saga)
                else:
                    pass

    def extrair_tecnicas(self):
        tecnicas_url = "wiki/Category:Techniques?from="
        for letra in string.ascii_uppercase:
            with sync_playwright() as p:
                navegador = p.chromium.launch(headless=False)
                pagina = navegador.new_page()
                pagina.goto(self.url(tecnicas_url, letra))
                soup = BeautifulSoup(pagina.content(), "html.parser")
                nomes = soup.find_all("a", class_="category-page__member-link")
                for nome in nomes:
                    print(nome.text)


    def url(self, context, letter):
        base = f"https://dragonball.fandom.com/{context}{letter}"
        return base

iniciar = Bot() 