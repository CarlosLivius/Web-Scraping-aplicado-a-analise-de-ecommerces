import pandas as pd 
from ecommerces.kabum_scraper import extrair_kabum
from ecommerces.magalu_scraper import extrair_magalu
from ecommerces.casasbahia_scraper import extrair_casasbahia

def extrair_dados(driver):
    """
    Função principal do módulo de extração.
    Define a ordem de coleta e consolida os dados.
    """

    todos_os_dados = []

    print("\n[MÓDULO DE EXTRAÇÃO] Iniciando a coleta de dados nos e-commerces...\n")

    # Extrai dados do Kabum
    print("     -> Extraindo dados do Kabum...")
    dados_kabum = extrair_kabum(driver)
    todos_os_dados.extend(dados_kabum)
    print(f"      [OK] Kabum: {len(dados_kabum)} registros coletados.")

    # Extrai dados da Magalu
    print("     -> Extraindo dados do Magalu...")
    dados_magalu = extrair_magalu(driver)
    todos_os_dados.extend(dados_magalu)
    print(f"      [OK] Magalu: {len(dados_magalu)} registros coletados.")

    # Extrai dados da Casas Bahia
    print("     -> Extraindo dados da Casas Bahia...")
    dados_casasbahia = extrair_casasbahia(driver)
    todos_os_dados.extend(dados_casasbahia)
    print(f"      [OK] Casas Bahia: {len(dados_casasbahia)} registros coletados.")

    # Chamada para consolidação e Análise
    if todos_os_dados:
        pd_final = pd.DataFrame(todos_os_dados)
        pd_final.to_csv("dados_coletados_brutos.csv", index=False)
        print("\n[SUCESSO] Dados consolidados e salvos em 'dados_coletados_brutos.csv'.")
    else:
        print("\n[ALERTA] Nenhuma informação foi coletada. Verifique os módulos de extração.")    