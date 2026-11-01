"""
monitor.py — Monitor de abertura de vendas de ingressos na Neo Química Arena (Fiel Torcedor).
Gerencia a contagem regressiva pré-abertura, login antecipado e polling em tempo real.
"""

import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from colorama import init, Fore, Style
from bot.browser import _registrar_sinal_vida

init(autoreset=True)

SELETORES_BLOQUEADO = [
    "//button[contains(text(),'EM BREVE')]",
    "//button[contains(text(),'ESGOTADO')]",
    "//span[contains(text(),'Em Breve')]",
    "//span[contains(text(),'Indisponível')]",
]

SELETORES_DISPONIVEL = [
    "//a[contains(text(),'COMPRAR') or contains(text(),'Comprar') or contains(text(),'INGRESSOS')]",
    "//button[contains(text(),'COMPRAR') or contains(text(),'Comprar') or contains(text(),'Reservar')]",
    "a.btn-comprar",
    "button.btn-primary.next",
]


def aguardar_horario_abertura(horario_str, minutos_antes=5):
    """
    Aguarda até N minutos antes do horário oficial de abertura de vendas.
    Formato esperado de horario_str: ISO 8601 ("2026-11-05T11:00:00").
    """
    abertura = datetime.fromisoformat(horario_str)
    inicio_bot = abertura - timedelta(minutes=minutos_antes)
    agora = datetime.now()

    if agora >= inicio_bot:
        print(Fore.YELLOW + "[!] Horário de preparação atingido — iniciando execução imediatamente...")
        return

    espera_total = (inicio_bot - agora).total_seconds()
    print(Fore.CYAN + f"\n⏰ Abertura das vendas: {abertura.strftime('%d/%m às %H:%M')}")
    print(Fore.CYAN + f"🤖 Ativação do monitor: {inicio_bot.strftime('%d/%m às %H:%M')} ({minutos_antes} min antes)")
    print(Fore.CYAN + f"⏳ Tempo de espera: {int(espera_total // 60)} min e {int(espera_total % 60)}s\n")

    while True:
        _registrar_sinal_vida()
        agora = datetime.now()
        restante = (inicio_bot - agora).total_seconds()

        if restante <= 0:
            print(Fore.GREEN + Style.BRIGHT + "\n✅ Janela de preparação aberta! Iniciando monitor...\n")
            break

        if restante <= 60:
            print(Fore.YELLOW + f"\r⏳ {int(restante)}s para iniciar...", end="", flush=True)
            time.sleep(1)
        elif restante <= 300:
            print(Fore.CYAN + f"\r⏳ {int(restante // 60)}min {int(restante % 60)}s para iniciar...", end="", flush=True)
            time.sleep(10)
        else:
            horas = int(restante // 3600)
            minutos = int((restante % 3600) // 60)
            print(Fore.CYAN + f"\r⏳ {horas}h {minutos}min para iniciar...", end="", flush=True)
            time.sleep(30)


def venda_esta_aberta(driver, url_evento):
    """
    Verifica na página da partida se o botão de compra/reserva já foi liberado.
    """
    try:
        _registrar_sinal_vida()
        driver.get(url_evento)
        time.sleep(1.8)

        for seletor in SELETORES_DISPONIVEL:
            try:
                if seletor.startswith("//"):
                    elementos = driver.find_elements(By.XPATH, seletor)
                else:
                    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)

                if elementos and any(el.is_displayed() for el in elementos):
                    return True
            except Exception:
                pass

        for seletor in SELETORES_BLOQUEADO:
            try:
                elementos = driver.find_elements(By.XPATH, seletor)
                if elementos and any(el.is_displayed() for el in elementos):
                    return False
            except Exception:
                pass

        return False

    except Exception as e:
        print(Fore.RED + f"[!] Erro ao consultar disponibilidade da partida: {e}")
        return False


def monitorar_abertura(driver, config):
    """
    Executa polling contínuo até detectar a liberação das reservas para a partida.
    """
    monitor = config.get("monitor", {})
    target = config["target"]
    intervalo = monitor.get("intervalo_checagem_segundos", 3)
    url_alvo = target["event_url"]

    print(Fore.CYAN + f"[🔍] Monitorando partida em: {url_alvo}")
    print(Fore.CYAN + f"[🔍] Intervalo de verificação: {intervalo}s\n")

    tentativa = 0
    while True:
        tentativa += 1
        agora = datetime.now().strftime("%H:%M:%S")

        if venda_esta_aberta(driver, url_alvo):
            print(Fore.GREEN + Style.BRIGHT + f"\n\n🚨 [{agora}] RESERVAS LIBERADAS! Iniciando seleção de setor!\n")
            return url_alvo

        print(Fore.YELLOW + f"[{agora}] #{tentativa} Venda ainda não liberada... nova checagem em {intervalo}s")
        time.sleep(intervalo)


def fazer_login_antecipado(driver, config):
    """
    Autentica o torcedor antes da abertura oficial para reduzir o tempo de checkout.
    """
    from bot.login import fazer_login, abrir_modal_login, verificar_login_ok, clicar_botao_login
    from bot.captcha import resolver_captcha_api, captcha_manual

    creds = config["credentials"]
    captcha_cfg = config["captcha"]

    print(Fore.CYAN + "\n[→] Verificando sessão / login antecipado no Fiel Torcedor...")
    driver.get(config["target"]["event_url"])
    time.sleep(2)

    if verificar_login_ok(driver):
        return True

    abrir_modal_login(driver)
    time.sleep(1.5)

    login_user = creds.get("login") or creds.get("email", "")
    if not fazer_login(driver, login_user, creds["password"]):
        print(Fore.RED + "[✗] Não foi possível preencher o login antecipado")
        return False

    captcha_ok = False
    if captcha_cfg.get("service") == "2captcha" and captcha_cfg.get("api_key"):
        captcha_ok = resolver_captcha_api(driver, captcha_cfg["api_key"])

    if not captcha_ok:
        captcha_ok = captcha_manual(driver, timeout=120)

    if captcha_ok:
        clicar_botao_login(driver)
        time.sleep(2.5)
        if verificar_login_ok(driver):
            print(Fore.GREEN + "[✓] Login antecipado concluído com sucesso!")
            return True

    print(Fore.YELLOW + "[!] Login antecipado pendente — será validado na etapa final")
    return False
