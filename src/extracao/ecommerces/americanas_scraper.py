# src/extracao/ecommerces/americanas_scraper.py

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import re
from bs4 import BeautifulSoup # Importando BeautifulSoup para processar o HTML bruto

# URL DE BUSCA PAGINADA: A URL será parametrizada por 'page={}'
# Usaremos 'page=1' até 'page=9' para garantir a coleta de 100 itens.
URL_BASE_SEARCH = "https://www.americanas.com.br/celulares-e-smartphones/smartphone?category-1=celulares-e-smartphones&category-2=smartphone&fuzzy=0&operator=and&facets=category-1%2Ccategory-2%2Cfuzzy%2Coperator&sort=score_desc&page={}"

# --- XPATHS DE COLETA FLEXÍVEL ---
# Buscando o card principal pela classe para o Beautiful Soup
XPATH_CARD_CLASS_PREFIX = r'ProductCard_productCard__' 


def extrair_americanas(driver):
    """
    Realiza a navegação e extração de até 108 produtos (12 por página em 9 páginas) da Americanas.
    Aplica FORÇA BRUTA (interrupção e pausa curta) para mitigar o bloqueio de carregamento.
    """
    dados_americanas = []
    
    # NOVOS LIMITES: 12 itens por página * 9 páginas = 108 itens (atinge a meta de 100)
    LIMITE_ITENS_GLOBAL = 100 
    LIMITE_ITENS_POR_PAGINA = 12 
    MAX_PAGINAS = 9 # Aumentado para 9 páginas.
    
    pagina_atual = 1

    # Loop de paginação
    while len(dados_americanas) < LIMITE_ITENS_GLOBAL and pagina_atual <= MAX_PAGINAS:
        
        # A URL agora usa o número da página diretamente
        url_atual = URL_BASE_SEARCH.format(pagina_atual)
        print(f"\n   [Americanas] Acessando URL da Página {pagina_atual}: {url_atual}")
        
        page_load_success_on_get = False
        itens_coletados_nesta_pagina = 0

        try:
            # 1. NAVEGAR (Tenta carregar a URL)
            driver.get(url_atual)
            page_load_success_on_get = True
            
        except TimeoutException:
            print(f"   [Americanas] ALERTA: Timeout de navegação (30s). Tentando coleta com DOM parcial.")
            page_load_success_on_get = True
        except Exception:
            page_load_success_on_get = True
            
        # --- INÍCIO DA COLETA FORÇADA (UMA TENTATIVA POR PÁGINA) ---
        if page_load_success_on_get:
            
            try:
                # --- TÉCNICA DE FORÇA BRUTA: SCROLL + PAUSA CURTA + INTERRUPÇÃO ---
                sleep_time = 10 
                print(f"   [PAG {pagina_atual}] Forçando DOM: Scroll, Pausa {sleep_time}s e Interrupção...")

                # 1. Scroll para forçar o lazy-load
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(sleep_time) 
                
                # 2. Interrompe o carregamento de scripts secundários
                driver.execute_script("window.stop();")
                print("   [Americanas] Carregamento INTERROMPIDO. Coletando HTML...")
                
                # 3. COLETAR HTML BRUTO E CONTAR
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Encontrar todos os cards de produto
                cards_produtos = soup.find_all('div', class_=re.compile(XPATH_CARD_CLASS_PREFIX))
                
                # Tenta fallback se a classe primária falhar (Busca por data-testid)
                if not cards_produtos:
                     cards_produtos = soup.find_all('div', attrs={'data-fs-custom-product-card': 'true'})


                current_count = len(cards_produtos)
                print(f"   [PAG {pagina_atual}] Total de cards encontrados no DOM: {current_count}.")

                # --- EXTRAÇÃO DOS PRIMEIROS 12 ITENS ---
                
                for card in cards_produtos:
                    
                    if itens_coletados_nesta_pagina >= LIMITE_ITENS_POR_PAGINA:
                        break 
                    if len(dados_americanas) >= LIMITE_ITENS_GLOBAL:
                        break 
                    
                    # --- Inicializa variáveis de coleta ---
                    titulo, preco_texto, preco_numerico, nota_media, num_comentarios = "N/A", "N/A", "N/A", "N/A", "N/A"
                    
                    try: # Novo try/except para a coleta interna de cada card
                        # 1. Título
                        titulo_tag = card.find('h3', class_=re.compile(r'ProductCard_productName'))
                        if titulo_tag:
                            titulo = titulo_tag.get('title', titulo_tag.text).strip()
                        
                        # 2. Preço à Vista
                        preco_tag = card.find('p', class_=re.compile(r'ProductCard_productPrice'))
                        if preco_tag:
                            preco_texto_raw = preco_tag.text.strip()
                            
                            match_preco = re.search(r'R\$\s*([\d\.]+,\d{2})', preco_texto_raw)
                            if match_preco:
                                preco_texto = match_preco.group(1)
                                preco_limpo = preco_texto.replace('.', '').replace(',', '.').strip()
                                try: preco_numerico = float(preco_limpo)
                                except: preco_numerico = preco_texto
                        
                        # 3. Avaliações
                        review_count_div = card.find('div', class_=re.compile(r'review-count'))
                        if review_count_div:
                            num_match = re.search(r'\((\d+)\)', review_count_div.text)
                            if num_match:
                                num_comentarios = int(num_match.group(1))
                            
                            nota_tag = card.find('div', class_=re.compile(r'avg-rating'))
                            if nota_tag:
                                nota_media = float(nota_tag.text.strip())

                        
                    except Exception:
                        # Falha na extração de atributos de um card, mas continua para o próximo.
                        pass

                    # --- CONSOLIDAÇÃO (FORA DO TRY INTERNO, MAS DENTRO DO LOOP FOR) ---
                    if titulo != "N/A" and isinstance(preco_numerico, float):
                        itens_coletados_nesta_pagina += 1
                        
                        dados_americanas.append({
                            'e_commerce': 'Americanas',
                            'produto': titulo,
                            'preco_bruto_vista': preco_texto,
                            'preco_original': "N/A", 
                            'preco_numerico': preco_numerico,
                            'nota_media': nota_media,
                            'num_comentarios': num_comentarios
                        })
                        
                        print(f"      [PAG {pagina_atual} | ITEM {itens_coletados_nesta_pagina:02d}] OK: '{titulo[:40]}...' | Preço: R$ {preco_numerico:.2f} | Total: {len(dados_americanas)}")
            
            except Exception as e:
                 # Captura erros no bloco principal de coleta, como falha no BeautifulSoup
                 print(f"   [Americanas] ERRO CRÍTICO NA COLETA na Página {pagina_atual}: {e.__class__.__name__}. Não foi possível coletar dados.")
                 
        
        # --- LÓGICA DE PAGINAÇÃO E CONTROLE ---
        
        if itens_coletados_nesta_pagina > 0:
            print(f"   [Americanas] {itens_coletados_nesta_pagina} itens adicionados da Página {pagina_atual}.")
            pagina_atual += 1
            if pagina_atual <= MAX_PAGINAS:
                time.sleep(5) # Pausa entre páginas
        else:
            print(f"   [Americanas] Coleta falhou na Página {pagina_atual} ou a listagem terminou. Interrompendo busca.")
            break
            
    print(f"\n   [Americanas] Resumo da Coleta FINAL: {len(dados_americanas)} produtos coletados no total.")
    return dados_americanas