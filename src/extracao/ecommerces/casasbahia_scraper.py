# src/extracao/ecommerces/casasbahia_scraper.py

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import re

# URL DE BUSCA PAGINADA: A URL aceita o número da página no formato ?page=X
URL_PAGINADA = "https://www.casasbahia.com.br/smartphone/b?page={}"

# --- XPATHS DE COLETA ---
# XPATH GERAL PARA DETECTAR O CARD DE PRODUTO (o elemento que contém todos os dados)
# Usando data-testid para estabilidade (div[@data-testid="product-card-item"])
XPATH_CARD_GERAL = '//div[@data-testid="product-card-item"]'

# --- XPATHS RELATIVOS AOS ATRIBUTOS (DENTRO DA TAG DIV DO CARD) ---
# TÍTULO: O título está no atributo 'title' do link dentro do h3
XPATH_TITULO_RELATIVO = './/h3[@class="product-card__title"]/a'
# PREÇO: XPATH que busca o preço mais visível (geralmente o preço Pix ou à vista)
XPATH_PRECO_AVISTA_RELATIVO = './/div[@class="product-card__highlight-price"]'
# AVALIAÇÕES: XPATH que busca o span com o número de avaliações (X)
XPATH_AVALIACAO_RELATIVO = './/span[@data-testid="product-card-reviews-count"]'


def extrair_casasbahia(driver):
    """
    Realiza a navegação e extração de 100 produtos da Casas Bahia (50 por página).
    """
    dados_casasbahia = []
    
    pagina_atual = 1
    LIMITE_ITENS_GLOBAL = 100
    LIMITE_ITENS_POR_PAGINA = 25
    MAX_PAGINAS = 4

    while len(dados_casasbahia) < LIMITE_ITENS_GLOBAL and pagina_atual <= MAX_PAGINAS:
        url_atual = URL_PAGINADA.format(pagina_atual)
        print(f"\n   [Casas Bahia] Acessando URL da Página {pagina_atual}: {url_atual}")
        
        page_load_success_on_get = False
        itens_coletados_nesta_pagina = 0

        try:
            # 1. NAVEGAR (Tenta carregar a URL)
            driver.get(url_atual)
            page_load_success_on_get = True 
            
        except TimeoutException:
            # Captura o Timeout de navegação (30s) e força a coleta
            print(f"   [Casas Bahia] ALERTA: Timeout de navegação (30s). Tentando coleta com DOM parcial.")
            page_load_success_on_get = True 
        except Exception:
            page_load_success_on_get = True 
            
        # --- BLOCO DE COLETA (EXECUTADO MESMO APÓS TIMEOUT) ---
        if page_load_success_on_get:
            
            try:
                # --- TÉCNICA DE PAUSA FIXA (COLETA FORÇADA) ---
                sleep_time = 15 # 15s fixos para estabilização (Casas Bahia é notoriamente pesada)
                print(f"   [Casas Bahia] Aguardando {sleep_time} segundos para estabilização do DOM (Coleta Forçada)...")
                
                # Rola a página e pausa para carregar todos os lazy-load assets
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(sleep_time) 
                
                # 1. COLETAR TODOS OS CARDS DE PRODUTO EM LOTE (FORÇADA)
                cards_produtos_elements = driver.find_elements(By.XPATH, XPATH_CARD_GERAL)
                
                print(f"   [Casas Bahia] Total de cards encontrados: {len(cards_produtos_elements)}.")

                # 2. ITERAR E EXTRAIR
                for card_element in cards_produtos_elements:
                    
                    if itens_coletados_nesta_pagina >= LIMITE_ITENS_POR_PAGINA:
                        break
                    if len(dados_casasbahia) >= LIMITE_ITENS_GLOBAL:
                        break 
                    
                    # --- Inicializa variáveis de coleta ---
                    titulo, preco_texto, preco_numerico, nota_media, num_comentarios = "N/A", "N/A", "N/A", "N/A", "N/A"
                    preco_original_texto = "N/A"
                    
                    try:
                        
                        # 1. Título
                        try:
                            # O título está no atributo 'title' do elemento <a>
                            titulo_tag = card_element.find_element(By.XPATH, XPATH_TITULO_RELATIVO)
                            titulo = titulo_tag.get_attribute('title').strip()
                        except: pass
                        
                        # 2. Preço à Vista (Preço Principal)
                        try:
                            preco_tag = card_element.find_element(By.XPATH, XPATH_PRECO_AVISTA_RELATIVO)
                            preco_texto_raw = preco_tag.text.strip()
                            
                            # Limpa o preço (apenas dígitos e vírgulas)
                            match_preco = re.search(r'R\$\s*([\d\.]+,\d{2})', preco_texto_raw)
                            if match_preco:
                                preco_texto = match_preco.group(1)
                                preco_limpo = preco_texto.replace('.', '').replace(',', '.').strip()
                                try: preco_numerico = float(preco_limpo)
                                except: preco_numerico = preco_texto
                            else:
                                preco_texto = preco_texto_raw
                        except: pass

                        # 3. Avaliações (Número de Comentários)
                        try:
                            num_comentarios_tag = card_element.find_element(By.XPATH, XPATH_AVALIACAO_RELATIVO)
                            num_comentarios_texto = num_comentarios_tag.text.strip()
                            num_match = re.search(r'\((\d+)\)', num_comentarios_texto)
                            if num_match:
                                num_comentarios = int(num_match.group(1))
                            # Nota Média: A Casas Bahia não expõe a nota média de forma simples no card, deixando N/A.
                            nota_media = "N/A"
                            
                        except: pass
                        
                        
                        # --- CONSOLIDAÇÃO ---
                        if titulo != "N/A" and isinstance(preco_numerico, float):
                            itens_coletados_nesta_pagina += 1
                            
                            dados_casasbahia.append({
                                'e_commerce': 'Casas Bahia',
                                'produto': titulo,
                                'preco_bruto_vista': preco_texto,
                                'preco_original': "N/A", # Não coletado com essa extração
                                'preco_numerico': preco_numerico,
                                'nota_media': nota_media,
                                'num_comentarios': num_comentarios
                            })
                            
                            print(f"      [PAG {pagina_atual} | ITEM {itens_coletados_nesta_pagina:02d}] OK: '{titulo[:40]}...' | Preço: R$ {preco_numerico:.2f} | Total: {len(dados_casasbahia)}")
                        
                    except Exception:
                        pass
            
                page_load_success_on_get = True 

            except Exception as e:
                # Captura todos os erros que podem ocorrer
                print(f"   [Casas Bahia] ERRO CRÍTICO NA COLETA: {e.__class__.__name__}. Não foi possível coletar dados.")

        
        # --- LÓGICA DE PAGINAÇÃO E CONTROLE ---
        
        if itens_coletados_nesta_pagina > 0:
            print(f"   [Casas Bahia] {itens_coletados_nesta_pagina} itens adicionados da Página {pagina_atual}.")
            pagina_atual += 1
            if pagina_atual <= MAX_PAGINAS:
                time.sleep(5) 
        else:
            print("   [Casas Bahia] Coleta falhou nesta página ou a listagem terminou. Interrompendo busca.")
            break
            
    print(f"\n   [Casas Bahia] Resumo da Coleta FINAL: {len(dados_casasbahia)} produtos coletados no total.")
    return dados_casasbahia