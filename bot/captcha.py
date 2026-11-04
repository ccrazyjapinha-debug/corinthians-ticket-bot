"""
captcha.py — Gerenciamento de desafios de verificação (modo interativo manual ou API).
"""

import time
import requests
from selenium.webdriver.common.by import By
from colorama import Fore
from bot.browser import _registrar_sinal_vida


def resolver_captcha_api(driver, api_key):
    """
    Resolve desafios Cloudflare Turnstile via integração de API externa (opcional).
    """
    print("[INFO] Verificando presença de desafio Turnstile...")
    sitekey = _extrair_sitekey(driver)
    if not sitekey:
        print("[INFO] Nenhum desafio bloqueante detectado")
        return True

    page_url = driver.current_url
    task_id = _enviar_requisicao_api(api_key, sitekey, page_url)
    if not task_id:
        return False

    token = _aguardar_token_api(api_key, task_id)
    if not token:
        return False

    return _injetar_token(driver, token)


def _extrair_sitekey(driver):
    """Busca o atributo sitekey caso exista um desafio ativo na página."""
    try:
        iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='challenges.cloudflare.com']")
        if iframes:
            src = iframes[0].get_attribute("src") or ""
            if "sitekey=" in src:
                return src.split("sitekey=")[1].split("&")[0]

        elementos = driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")
        if elementos:
            return elementos[0].get_attribute("data-sitekey")
        return None
    except Exception:
        return None


def _enviar_requisicao_api(api_key, sitekey, page_url):
    """Submete a tarefa de verificação para a API configurada."""
    try:
        resposta = requests.post(
            "https://2captcha.com/in.php",
            data={
                "key": api_key,
                "method": "turnstile",
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1,
            },
            timeout=25,
        )
        dados = resposta.json()
        if dados.get("status") == 1:
            return dados["request"]
        return None
    except Exception:
        return None


def _aguardar_token_api(api_key, task_id, max_tentativas=24):
    """Faz polling do resultado até obter o token ou atingir o limite de tentativas."""
    for _ in range(max_tentativas):
        time.sleep(5)
        _registrar_sinal_vida()
        try:
            resposta = requests.get(
                "https://2captcha.com/res.php",
                params={"key": api_key, "action": "get", "id": task_id, "json": 1},
                timeout=15,
            )
            dados = resposta.json()
            if dados.get("status") == 1:
                return dados["request"]
            if dados.get("request") != "CAPCHA_NOT_READY":
                return None
        except Exception:
            pass
    return None


def _injetar_token(driver, token):
    """Injeta o token retornado nos campos correspondentes do formulário."""
    try:
        driver.execute_script(
            """
            var inputs = document.querySelectorAll('[name="cf-turnstile-response"], [name="turnstile-response"]');
            inputs.forEach(function(input) {
                input.value = arguments[0];
                input.dispatchEvent(new Event('change', { bubbles: true }));
            });
            """,
            token,
        )
        time.sleep(1)
        return True
    except Exception:
        return False


def captcha_manual(driver, timeout=120):
    """
    Aguarda resolução interativa pelo usuário no navegador, mantendo o Watchdog
    atualizado e controlando o tempo real decorrido.
    """
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='challenges.cloudflare.com']")
    if not iframes:
        return True

    print("\n" + "=" * 55)
    print(Fore.YELLOW + "[AVISO] ACAO NECESSARIA: Confirme a verificação no navegador")
    print(Fore.YELLOW + f"[AVISO] Tempo limite: {timeout} segundos")
    print("=" * 55 + "\n")

    inicio = time.time()
    ultimo_log = time.time()

    while True:
        agora = time.time()
        decorrido = agora - inicio
        _registrar_sinal_vida()

        if decorrido >= timeout:
            print(Fore.RED + "[ERRO] Tempo esgotado aguardando verificação manual")
            return False

        if agora - ultimo_log >= 15:
            restante = int(timeout - decorrido)
            print(Fore.CYAN + f"[VERIFICACAO] Aguardando confirmação... {restante}s restantes")
            ultimo_log = agora

        try:
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='challenges.cloudflare.com']")
            if not iframes:
                print(Fore.GREEN + "[OK] Verificação concluída!")
                return True
        except Exception as ex:
            print(Fore.YELLOW + f"[VERIFICACAO] Aviso: {ex}")

        time.sleep(1)
