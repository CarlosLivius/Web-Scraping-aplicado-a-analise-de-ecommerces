# src/extracao/ecommerces/kabum_scraper.py

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException 
import time

# ----------------------------------------
# TODO: Realizar filtragem por termos no título, conseguir extrair RAM, armazenamento, câmera, etc.   
# ----------------------------------------

# URL base da Kabum e termo de pesquisa (exemplo)
BASE_URL = "https://www.kabum.com.br/"
TERMO_PESQUISA = "celular-smartphone" 

# XPATH para o container principal da listagem de produtos (Contém todos os cards)
XPATH_CONTAINER_LISTAGEM = '//*[@id="listing"]/div[3]/div/div/div[2]/div/main'
# XPATH RELATIVO para cada card de produto dentro do container
XPATH_CARD_PRODUTO_RELATIVO = './div' # Alterado para div[] para pegar todos os filhos diretos do container

def extrair_kabum(driver):
    """
    Realiza a navegação e extração de dados da Kabum usando XPATH.
    O 'driver' (Selenium) é passado pelo módulo principal.
    """
    url_busca = (
        f"{BASE_URL}{TERMO_PESQUISA}/smartphones?"
        "page_number=1&page_size=100&facet_filters=&sort=most_searched"
    )
    dados_kabum = []
    
    print(f"   [Kabum] Acessando URL: {url_busca}")
    
    try:
        driver.get(url_busca)
        
        # 1. Espera o carregamento do container principal usando o XPATH
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, XPATH_CONTAINER_LISTAGEM))
        )
        time.sleep(2) # Pequeno delay para estabilizar o DOM
        
        # 2. Encontra o container mestre
        container_listagem = driver.find_element(By.XPATH, XPATH_CONTAINER_LISTAGEM)
        
        # 3. Encontra todos os CARDS de produto DENTRO do container
        # Usamos './div' para capturar todos os <div> filhos diretos (div[1] a div[100])
        cards_produtos_elements = container_listagem.find_elements(By.XPATH, XPATH_CARD_PRODUTO_RELATIVO)
        
        print(f"   [Kabum] Encontrados {len(cards_produtos_elements)} cards de produto.")

        for card_element in cards_produtos_elements:

            # Parte relativa ao título
            XPATH_TITULO_RELATIVO = './article/a/div/button/div/h3'
            
            # Parte relativa ao preço
            XPATH_PRECO_RELATIVO = './article/a/div/div[2]/div[2]/span'
            
            # 1. Extração do Título do Produto
            try:
                # Usa find_element para buscar dentro do 'card_element'
                titulo_tag = card_element.find_element(By.XPATH, XPATH_TITULO_RELATIVO)
                titulo = titulo_tag.text.strip()
            except:
                titulo = "N/A - XPATH Falhou (Título)"
            
            # 2. Extração do Preço
            try:
                preco_tag = card_element.find_element(By.XPATH, XPATH_PRECO_RELATIVO)
                preco_texto = preco_tag.text.strip()
            except:
                preco_texto = "N/A - XPATH Falhou (Preço)"
            
            # 3. Limpeza do Preço para float
            preco = "N/A"
            if preco_texto not in ["N/A - XPATH Falhou (Preço)", "N/A"]:
                # Remove R$, pontos de milhar e substitui vírgula por ponto decimal
                preco_limpo = preco_texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    preco = float(preco_limpo)
                except ValueError:
                    preco = preco_texto
            
            # Adiciona os dados coletados à lista
            dados_kabum.append({
                'e_commerce': 'Kabum',
                'produto': titulo,
                'preco_bruto': preco_texto,
                'preco_numerico': preco
            })

    except TimeoutException:
        print("   [Kabum] ALERTA: Tempo limite de carregamento da página excedido (30s).")
    except WebDriverException as wde:
        print(f"   [Kabum] ERRO DE DRIVER/COMUNICAÇÃO: Falha ao navegar ou se comunicar com o driver. Erro: {wde}")
    except Exception as e:
        print(f"   [Kabum] Erro genérico na extração da página: {e}")
        
    return dados_kabum