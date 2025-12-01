import sys
import os

# Adiciona o diretório 'src' ao PATH para permitir imports de módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from extracao.orchestrator_extract import extrair_dados

def configurar_servico_driver():
    """Configura e retorna uma instância do driver do Chrome (Selenium)."""
    
    opcoes = webdriver.ChromeOptions()
    
    # ----------------------------------------------------------------------
    # ARGUMENTOS ESSENCIAIS DE ESTABILIDADE E ANTI-BLOQUEIO
    # ----------------------------------------------------------------------
    opcoes.add_argument('--headless') 
    opcoes.add_argument('--no-sandbox')
    opcoes.add_argument('--disable-dev-shm-usage')
    opcoes.add_argument('--disable-gpu')
    opcoes.add_argument('--ignore-certificate-errors')
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36")
    
    # --- ARGUMENTOS CRÍTICOS DE STEALTH ---
    opcoes.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation']) 
    opcoes.add_experimental_option('useAutomationExtension', False)
    # ----------------------------------------------------------------------

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opcoes)
        
        # REMOVIDO: driver.set_page_load_timeout(30)
        # O timeout agora é o default (o que é necessário para a coleta forçada).
        
        return driver
    except Exception as e:
        print(f"Erro ao configurar o driver do Chrome. Verifique se o Google Chrome está instalado. Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando Aplicação de Web Scraping para Análise de E-commerces...")
    
    import sys 
    
    driver = configurar_servico_driver()
    
    if driver:
        try:
            extrair_dados(driver)
            print("✅ Extração concluída com sucesso!")
        except Exception as e:
            print(f"❌ Erro Crítico durante a extração: {e}")
        finally:
            if 'driver' in locals() and driver:
                driver.quit()
    else:
        print("❌ Falha ao iniciar o driver do Chrome. Encerrando a aplicação.")