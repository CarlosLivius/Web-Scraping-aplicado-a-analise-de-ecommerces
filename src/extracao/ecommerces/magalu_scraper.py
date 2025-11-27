# src/extracao/ecommerces/magalu_scraper.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException 
import time
import re

# URL DE CATEGORIA: Usando a URL de categoria solicitada (Lembre-se: ela é mais instável!)
URL_PAGINADA = "https://www.magazineluiza.com.br/celulares-e-smartphones/l/te/?page={}&sortOrientation=desc&sortType=score"

# --- XPATH FLEXÍVEL (COLETA DO CONTÊINER) ---
# XPATH que busca TODOS os elementos LI que são filhos do UL[data-testid="list"]
XPATH_LISTA_PRODUTOS = '//ul[@data-testid="list"]/li'


# --- XPATHS RELATIVOS AOS ATRIBUTOS (DENTRO DA TAG <li> DO PRODUTO) ---
XPATH_TITULO_RELATIVO = './/h2[@data-testid="product-title"]'
XPATH_PRECO_AVISTA_RELATIVO = './/p[@data-testid="price-value"]'
XPATH_PRECO_ORIGINAL_RELATIVO = './/p[@data-testid="price-original"]'
XPATH_AVALIACAO_RELATIVO = './/span[@format="score-count"]' 


def extrair_magalu(driver):
    """
    Realiza a navegação e extração dos atributos completos de 100 produtos da Magazine Luiza,
    usando XPATH flexível para o lote de produtos e a URL de categoria.
    """
    dados_magalu = []
    
    # ATENÇÃO: driver.set_page_load_timeout(30) DEVE SER REMOVIDO DO main.py.
    
    pagina_atual = 1
    LIMITE_ITENS_GLOBAL = 100
    LIMITE_ITENS_POR_PAGINA = 50
    MAX_PAGINAS = 2

    while len(dados_magalu) < LIMITE_ITENS_GLOBAL and pagina_atual <= MAX_PAGINAS:
        url_atual = URL_PAGINADA.format(pagina_atual)
        print(f"\n   [Magalu] Acessando URL da Página {pagina_atual}: {url_atual}")
        
        page_load_success_on_get = False
        itens_coletados_nesta_pagina = 0

        try:
            # 1. NAVEGAR (Irá esperar o máximo possível, pois o timeout foi removido no main.py)
            driver.get(url_atual)
            page_load_success_on_get = True 
            
        except Exception:
            # Captura qualquer falha de navegação (Timeout ou WebDriver) e tenta prosseguir
            print(f"   [Magalu] ALERTA: Falha no carregamento completo da página. Tentando coleta com DOM parcial.")
            page_load_success_on_get = True 

        
        # --- BLOCO DE COLETA (EXECUTADO MESMO APÓS ERRO DE NAVEGAÇÃO) ---
        if page_load_success_on_get:
            
            try:
                # --- TÉCNICA DE PAUSA FIXA (COLETA FORÇADA) ---
                sleep_time = 10 # 10s fixos para estabilização
                print(f"   [Magalu] Aguardando {sleep_time} segundos para estabilização do DOM (Coleta Forçada)...")
                
                # Rola a página e pausa
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(sleep_time) 
                
                # 1. COLETAR TODOS OS CARDS DE PRODUTO EM LOTE 
                cards_produtos_elements = driver.find_elements(By.XPATH, XPATH_LISTA_PRODUTOS)
                
                print(f"   [Magalu] Total de cards encontrados na página {pagina_atual}: {len(cards_produtos_elements)}.")

                # 2. ITERAR SOBRE O LOTE COLETADO E EXTRAIR ATRIBUTOS
                for card_element in cards_produtos_elements:
                    
                    # Se a coleta nesta página atingiu o limite, paramos a iteração do FOR
                    if itens_coletados_nesta_pagina >= LIMITE_ITENS_POR_PAGINA:
                        break
                    
                    # Verifica se o limite global foi atingido
                    if len(dados_magalu) >= LIMITE_ITENS_GLOBAL:
                        break 
                    
                    # --- Inicializa variáveis de coleta ---
                    titulo, preco_texto, preco_numerico, nota_media, num_comentarios = "N/A", "N/A", "N/A", "N/A", "N/A"
                    preco_original_texto = "N/A"
                    
                    try:
                        # FILTRO: Devemos garantir que o elemento é um link de produto válido
                        is_product_link = card_element.find_elements(By.XPATH, './/a[@data-testid="product-card-container"]')
                        if not is_product_link:
                             continue # Pula cards de categoria/filtro

                        # 1. Título
                        try:
                            titulo = card_element.find_element(By.XPATH, XPATH_TITULO_RELATIVO).text.strip()
                        except: pass
                        
                        # 2. Preço à Vista (Preço Principal)
                        try:
                            preco_avs_tag = card_element.find_element(By.XPATH, XPATH_PRECO_AVISTA_RELATIVO)
                            preco_texto_raw = preco_avs_tag.text.strip()
                            
                            match_preco = re.search(r'R\$\s*([\d\.]+,\d{2})', preco_texto_raw)
                            if match_preco:
                                preco_texto = match_preco.group(1)
                                preco_limpo = preco_texto.replace('.', '').replace(',', '.').strip()
                                try: preco_numerico = float(preco_limpo)
                                except: preco_numerico = preco_texto
                            else:
                                preco_texto = preco_texto_raw
                        except: pass

                        # 3. Preço Original
                        try:
                            preco_original_tag = card_element.find_element(By.XPATH, XPATH_PRECO_ORIGINAL_RELATIVO)
                            preco_original_texto = preco_original_tag.text.strip()
                        except: pass

                        # 4. Avaliações
                        try:
                            avaliacao_texto = card_element.find_element(By.XPATH, XPATH_AVALIACAO_RELATIVO).text.strip()
                            match = re.search(r'(\d+\.?\d*)\s*\((\d+)\)', avaliacao_texto)
                            if match:
                                nota_media = float(match.group(1))
                                num_comentarios = int(match.group(2))
                        except: pass
                        
                        
                        # --- CONSOLIDAÇÃO ---
                        if titulo != "N/A" and isinstance(preco_numerico, float):
                            itens_coletados_nesta_pagina += 1
                            
                            dados_magalu.append({
                                'e_commerce': 'Magalu',
                                'produto': titulo,
                                'preco_bruto_vista': preco_texto,
                                'preco_original': preco_original_texto,
                                'preco_numerico': preco_numerico,
                                'nota_media': nota_media,
                                'num_comentarios': num_comentarios
                            })
                            
                    except Exception:
                        # Captura erros de processamento e continua
                        pass
                
            except Exception as e:
                 print(f"   [Magalu] ERRO CRÍTICO NA COLETA: {e.__class__.__name__}. Não foi possível iniciar a coleta na página.")

        
        # --- LÓGICA DE PAGINAÇÃO E CONTROLE ---
        
        # O script só avança de página se a coleta na página atual foi bem-sucedida (itens coletados > 0)
        if itens_coletados_nesta_pagina > 0:
            print(f"   [Magalu] {itens_coletados_nesta_pagina} itens adicionados da Página {pagina_atual}.")
            pagina_atual += 1
            
            # Adiciona uma pausa entre as páginas
            if pagina_atual <= MAX_PAGINAS:
                time.sleep(5) 
        else:
            # Se não coletamos nada (mesmo com coleta forçada), consideramos que a listagem acabou ou o bloqueio é total.
            print("   [Magalu] Coleta falhou nesta página ou a listagem terminou. Interrompendo busca.")
            break
            


    # --- FINALIZAÇÃO ---
    print(f"\n   [Magalu] Resumo da Coleta FINAL: {len(dados_magalu)} produtos coletados no total.")
    return dados_magalu