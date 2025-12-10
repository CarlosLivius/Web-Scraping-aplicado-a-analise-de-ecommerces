# src/extracao/ecommerces/casasbahia_scraper.py

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import re
from bs4 import BeautifulSoup # Importando BeautifulSoup para processar o HTML bruto

# URL DE BUSCA PAGINADA: A URL aceita o número da página no formato ?page=X
URL_PAGINADA = "https://www.casasbahia.com.br/smartphone/b?page={}"

# --- XPATHS DE COLETA FLEXÍVEL DE ÚLTIMO RECURSO ---
# XPATH GERAL PARA DETECTAR O CARD DE PRODUTO
XPATH_CARD_GERAL = '//div[@data-testid="product-card-item"]' 


def extrair_casasbahia(driver):
    """
    Realiza a navegação e extração de 100 produtos da Casas Bahia.
    Ajustado para coletar 25 itens por página em 4 páginas.
    Usa FORÇA BRUTA (interrupção e pausa curta) para mitigar o bloqueio de carregamento.
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
            # Captura o Timeout de navegação (30s) e tenta a coleta
            print(f"   [Casas Bahia] ALERTA: Timeout de navegação (30s). Tentando coleta com DOM parcial.")
            page_load_success_on_get = True 
        except Exception:
            page_load_success_on_get = True 
            
        # --- BLOCO DE COLETA (EXECUTADO MESMO APÓS TIMEOUT) ---
        if page_load_success_on_get:
            
            try:
                # --- ESTRATÉGIA DE FORÇA BRUTA: SCROLL + PAUSA CURTA + INTERRUPÇÃO ---
                sleep_time = 10 
                print(f"   [Casas Bahia] Forçando DOM: Scroll, Pausa {sleep_time}s e Interrupção...")
                
                # Scroll para forçar o lazy-load
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(sleep_time) 
                
                # AÇÃO CRÍTICA: Interrompe o carregamento de scripts secundários que causam o timeout
                driver.execute_script("window.stop();")
                print("   [Casas Bahia] Carregamento da página INTERROMPIDO para evitar travamento.")
                
                # COLETAR O HTML BRUTO APÓS A RENDERIZAÇÃO FORÇADA
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Encontrar os cards usando o seletor CSS do BeautifulSoup (data-testid)
                cards_produtos = soup.find_all('div', attrs={'data-testid': 'product-card-item'})
                
                # Tenta fallback se o data-testid falhar (Busca pela classe wrapper)
                if not cards_produtos:
                     cards_produtos = soup.find_all('div', class_=re.compile(r'ProductCardWrapper'))


                print(f"   [Casas Bahia] Total de cards encontrados no HTML bruto: {len(cards_produtos)}.")

                # 2. ITERAR E EXTRAIR
                for card in cards_produtos:
                    
                    if itens_coletados_nesta_pagina >= LIMITE_ITENS_POR_PAGINA:
                        break
                    if len(dados_casasbahia) >= LIMITE_ITENS_GLOBAL:
                        break 
                    
                    # --- Inicializa variáveis de coleta ---
                    titulo, preco_texto, preco_numerico, nota_media, num_comentarios = "N/A", "N/A", "N/A", "N/A", "N/A"
                    
                    try:
                        # 1. Título
                        titulo_tag = card.find('h3', class_='product-card__title')
                        if titulo_tag and titulo_tag.a:
                            titulo = titulo_tag.a.get('title', 'N/A').strip()
                        
                        # 2. Preço à Vista
                        preco_tag = card.find('div', class_='product-card__highlight-price')
                        if preco_tag:
                            preco_texto_raw = preco_tag.text.strip()
                            match_preco = re.search(r'([\d\.]+,\d{2})', preco_texto_raw)
                            if match_preco:
                                preco_texto = match_preco.group(1)
                                preco_limpo = preco_texto.replace('.', '').replace(',', '.').strip()
                                try: preco_numerico = float(preco_limpo)
                                except: preco_numerico = preco_texto
                        
                        # 3. Avaliações
                        num_comentarios_tag = card.find('span', attrs={'data-testid': 'product-card-reviews-count'})
                        if num_comentarios_tag:
                            num_comentarios_texto = num_comentarios_tag.text.strip()
                            num_match = re.search(r'\((\d+)\)', num_comentarios_texto)
                            if num_match:
                                num_comentarios = int(num_match.group(1))
                            nota_media = "N/A"
                        
                        
                        # --- CONSOLIDAÇÃO ---
                        if titulo != "N/A" and isinstance(preco_numerico, float):
                            itens_coletados_nesta_pagina += 1
                            
                            dados_casasbahia.append({
                                'e_commerce': 'Casas Bahia',
                                'produto': titulo,
                                'preco_bruto_vista': preco_texto,
                                'preco_original': "N/A", 
                                'preco_numerico': preco_numerico,
                                'nota_media': nota_media,
                                'num_comentarios': num_comentarios
                            })
                            
                            print(f"      [PAG {pagina_atual} | ITEM {itens_coletados_nesta_pagina:02d}] OK: '{titulo[:40]}...' | Preço: R$ {preco_numerico:.2f} | Total: {len(dados_casasbahia)}")
                        
                    except Exception:
                        pass
                
            except Exception as e:
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