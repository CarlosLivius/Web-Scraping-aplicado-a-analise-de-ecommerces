# src/extracao/ecommerces/kabum_scraper.py

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# URL base da Kabum e termo de pesquisa (exemplo)
BASE_URL = "https://www.kabum.com.br/"
TERMO_PESQUISA = "celular-smartphone" # Alterado para ser mais genérico, seguindo sua URL

def extrair_kabum(driver):
    """
    Realiza a navegação e extração de dados da Kabum para uma lista de produtos.
    """
    # A URL já está parametrizada para 100 resultados na primeira página,
    # conforme o método de extração definido.
    url_busca = (
        f"{BASE_URL}{TERMO_PESQUISA}/smartphones?"
        "page_number=1&page_size=100&facet_filters=&sort=most_searched"
    )
    dados_kabum = []
    
    print(f"   [Kabum] Acessando URL: {url_busca}")
    driver.get(url_busca)

    try:
        # Espera que o elemento principal dos produtos seja carregado (garantindo o AJAX)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'main.page-content'))
        )
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # O seletor mais estável é o 'article.productCard' ou o 'div' que o contém
        # Aqui, usamos a classe que indica o CARD (productCard).
        cards_produtos = soup.find_all('article', class_=lambda x: x and 'productCard' in x)
        
        print(f"   [Kabum] Encontrados {len(cards_produtos)} cards de produto.")

        for card in cards_produtos:
            # 1. Extração do Título do Produto: Usa a classe nameCard
            titulo_tag = card.find('span', class_=lambda x: x and 'nameCard' in x)
            titulo = titulo_tag.text.strip() if titulo_tag else "N/A"
            
            # 2. Extração do Preço: Usa a classe priceCard
            preco_tag = card.find('span', class_=lambda x: x and 'priceCard' in x)
            preco_texto = preco_tag.text.strip() if preco_tag else "N/A"
            
            # 3. Limpeza do Preço para float
            preco = "N/A"
            if preco_texto != "N/A":
                # Remove R$, pontos de milhar e substitui vírgula por ponto decimal
                preco_limpo = preco_texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    preco = float(preco_limpo)
                except ValueError:
                    preco = preco_texto # Mantém o texto se a conversão falhar
            
            # Adiciona os dados coletados à lista
            dados_kabum.append({
                'e_commerce': 'Kabum',
                'produto': titulo,
                'preco_bruto': preco_texto,
                'preco_numerico': preco
            })

    except Exception as e:
        print(f"   [Kabum] Erro na extração da página: {e}")
        
    return dados_kabum