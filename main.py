# main.py

import sys
import os

# Adiciona o diretório 'src' ao PATH para permitir imports de módulos internos
# Linha de correção: O caminho correto para a pasta raiz do projeto.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# CORREÇÃO: Importa a função 'extrair_dados' do módulo 'orchestrator_extract'
# O módulo está dentro da pasta 'extracao'.
from extracao.orchestrator_extract import extrair_dados

def configurar_servico_driver():
    """Configura e retorna uma instância do driver do Chrome (Selenium) no modo headless."""
    
    opcoes = webdriver.ChromeOptions()
    
    # ----------------------------------------------------------------------
    # ARGUMENTOS ESSENCIAIS DE ESTABILIDADE E ANTI-BLOQUEIO
    # ----------------------------------------------------------------------
    # opcoes.add_argument('--headless')
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--disable-gpu')
    
    # CORREÇÃO: Adicionando argumento para ignorar erros de certificado (SSL/HTTPS)
    opcoes.add_argument('--ignore-certificate-errors')
    
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
    
    # Desabilita logs de erro excessivos do Chrome que poluem o console
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging'])
    # ----------------------------------------------------------------------

    # Instala o driver mais recente e inicia o serviço
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opcoes)
        
        # AÇÃO CRÍTICA: Removida a linha driver.set_page_load_timeout(30)
        # O timeout agora é o default (geralmente 300s ou infinito).
        # O controle de tempo será feito pelo time.sleep e window.stop() no scraper.
        
        return driver
    except Exception as e:
        print(f"Erro ao configurar o driver do Chrome. Verifique se o Google Chrome está instalado. Erro: {e}")
        # Encerra o programa com erro
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando Aplicação de Web Scraping para Análise de E-commerces...")
    
    import sys 
    
    driver = configurar_servico_driver()
    
    if driver:
        try:
            # CORREÇÃO: Chama a função principal do módulo de extração com o novo nome
            extrair_dados(driver)
            print("✅ Extração concluída com sucesso!")
        except Exception as e:
            # Captura exceções mais amplas que podem ocorrer após o driver iniciar
            print(f"❌ Erro Crítico durante a extração: {e}")
        finally:
            # Garante que o navegador seja fechado após a conclusão ou erro
            if 'driver' in locals() and driver:
                driver.quit()
    else:
        # Esta linha não deve ser atingida, pois a falha do driver causa sys.exit(1)
        print("❌ Falha ao iniciar o driver do Chrome. Encerrando a aplicação.")