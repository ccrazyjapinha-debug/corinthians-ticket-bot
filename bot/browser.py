"""
browser.py — Gerenciamento de sessão do Chrome via Chrome DevTools Protocol (CDP)
e thread de Watchdog anti-stall.

Estratégia arquitetural:
- Conecta via CDP (porta 9222) a uma instância real do Google Chrome.
- Mantém uma thread daemon de Watchdog sincronizada com Lock para detectar
  eventuais travamentos de rede/DOM e acionar recuperação automática.
"""

import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from colorama import Fore

DEBUG_PORT = 9222
_watchdog_lock = threading.Lock()
_ultimo_sinal_vida = time.time()


def criar_driver(headless=False, page_load_timeout=30):
    """
    Conecta ao Google Chrome via Remote Debugging Protocol (CDP) na porta 9222.
    """
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(page_load_timeout)
        print(Fore.GREEN + f"[OK] Conectado ao Chrome via CDP (aba ativa: {driver.title[:50]})")
        _registrar_sinal_vida()
        return driver

    except Exception as e:
        print(Fore.RED + f"""
==============================================================
  [ERRO] CHROME NAO ENCONTRADO NA PORTA {DEBUG_PORT}
--------------------------------------------------------------
  Execute primeiro o script: start_chrome.bat
==============================================================
""")
        raise RuntimeError(f"Chrome não está rodando na porta {DEBUG_PORT}") from e


def _registrar_sinal_vida():
    """Atualiza o timestamp de última atividade para o controle do Watchdog."""
    global _ultimo_sinal_vida
    with _watchdog_lock:
        _ultimo_sinal_vida = time.time()


def connection_alive(driver):
    """Verifica se a conexão com o WebDriver permanece responsiva."""
    try:
        _ = driver.title
        _registrar_sinal_vida()
        return True
    except Exception:
        return False


def iniciar_watchdog(driver, timeout_segundos=60, callback=None):
    """
    Inicia uma thread daemon de monitoramento (Watchdog) que verifica
    periodicamente se o fluxo principal ficou bloqueado além do limite.
    """
    def _watch():
        global _ultimo_sinal_vida
        while True:
            time.sleep(10)
            with _watchdog_lock:
                inativo_ha = time.time() - _ultimo_sinal_vida

            if inativo_ha > timeout_segundos:
                print(Fore.YELLOW + f"\n[WATCHDOG] Fluxo sem resposta há {int(inativo_ha)}s — executando recuperação!")
                if callback:
                    try:
                        callback(driver)
                    except Exception as e:
                        print(Fore.RED + f"[WATCHDOG] Erro no callback de recuperação: {e}")
                _registrar_sinal_vida()

    t = threading.Thread(target=_watch, daemon=True)
    t.start()
    return t


def esperar_elemento(driver, by, seletor, timeout=15):
    """Aguarda presença do elemento no DOM com wait explícito."""
    _registrar_sinal_vida()
    resultado = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, seletor))
    )
    _registrar_sinal_vida()
    return resultado


def esperar_clicavel(driver, by, seletor, timeout=15):
    """Aguarda até que o elemento esteja visível e habilitado para clique."""
    _registrar_sinal_vida()
    resultado = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, seletor))
    )
    _registrar_sinal_vida()
    return resultado


def scroll_ate_elemento(driver, elemento):
    """Centraliza o elemento na viewport antes da interação."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    time.sleep(0.4)


def clique_humano(driver, elemento):
    """
    Realiza movimentação de cursor e clique com cadência humanizada.
    """
    _registrar_sinal_vida()
    scroll_ate_elemento(driver, elemento)
    time.sleep(random.uniform(0.25, 0.65))
    ActionChains(driver).move_to_element(elemento).pause(
        random.uniform(0.1, 0.25)
    ).click().perform()
    time.sleep(random.uniform(0.2, 0.45))
    _registrar_sinal_vida()


def aceitar_cookies(driver):
    """Fecha o banner de consentimento de cookies caso esteja visível."""
    try:
        botao = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(translate(text(),'ACEITAR','aceitar'),'aceitar') "
                "or contains(translate(text(),'CONCORDO','concordo'),'concordo')]"
            ))
        )
        botao.click()
        print("[OK] Banner de cookies fechado")
        time.sleep(0.8)
    except Exception:
        pass
