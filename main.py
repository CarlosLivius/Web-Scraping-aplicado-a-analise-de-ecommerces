import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__), 'src'))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from extracao.extracao_master import iniciar_extracao

def configurar_servico_driver():
    """Configura e retorna uma instância do driver do Chrome (Selenium) no modo headless."""
    # O modo headless é recomendado para scraping em servidores, mas pode ser desativado
    # se você quiser visualizar a navegação durante o desenvolvimento/teste.

    opcoes = webDriver.ChromeOptions()
    opcoes.add_argument('--headless') # Executa o Chrome em modo headless (sem interface gráfica)
    opcoes.add_argument('--no-sandbox') # Necessário para rodar como root em alguns ambientes
    opcoes.add_argument('--disable-dev-shm-usage') # Evita problemas de memória em ambientes limitados

    # Instala o Driver mais recente e inicia o serviço
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opcoes)
        return driver
    except Exception as e:
        print(f"Erro ao configurar o driver do Chrome: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando Aplicação de Web Scraping para Análise de E-commerces...")

    driver = configurar_servico_driver()

    if driver:
        try:
            # Função principal de extração de dados
            iniciar_extracao(driver)
            print("✅ Extração concluída com sucesso!")
        except Exception as e:
            print(f"Erro durante a extração: {e}")
        finally:
            # Encerra o driver após a extração
            driver.quit()
    else:
        print("❌ Falha ao iniciar o driver do Chrome. Encerrando a aplicação.")

