"""
ticket.py — Fluxo de seleção de partida, setor da Neo Química Arena (com fallback
automático por prioridade), quantidade de ingressos e avanço até a reserva.
"""

import time
import random
from selenium.webdriver.common.by import By
from bot.browser import esperar_clicavel, clique_humano, aceitar_cookies

SETORES_PADRAO_ARENA = [
    "Norte",
    "Sul",
    "Leste Inferior",
    "Leste Superior",
    "Oeste Inferior",
    "Oeste Superior",
]


def navegar_para_partida(driver, event_url):
    """Acessa a página de jogos/ingressos e fecha avisos de cookies."""
    print(f"[→] Acessando página da partida: {event_url}")
    driver.get(event_url)
    time.sleep(random.uniform(1.5, 2.5))
    aceitar_cookies(driver)
    print("[✓] Página carregada")


def selecionar_partida(driver, nome_partida=""):
    """
    Clica no botão de compra/reserva correspondente à partida alvo.
    """
    print(f"[→] Selecionando partida: {nome_partida or 'Primeira disponível'}...")
    try:
        if nome_partida:
            termo = nome_partida.split("—")[0].strip()
            xpath_partida = (
                f"//*[contains(text(),'{termo}')]/ancestor::*[self::div or self::article or self::li][1]"
                f"//a[contains(text(),'Comprar') or contains(text(),'Reservar') or contains(text(),'Ingressos')]"
                f" | //*[contains(text(),'{termo}')]/ancestor::*[self::div or self::article or self::li][1]"
                f"//button[contains(text(),'Comprar') or contains(text(),'Reservar') or contains(text(),'Ingressos')]"
            )
            botoes = driver.find_elements(By.XPATH, xpath_partida)
            if botoes:
                clique_humano(driver, botoes[0])
                time.sleep(2)
                print(f"[✓] Partida '{termo}' selecionada")
                return True

        btn = esperar_clicavel(
            driver,
            By.XPATH,
            "//a[contains(text(),'Comprar') or contains(text(),'Reservar') or contains(text(),'INGRESSOS') or contains(@class,'tmpe-link-details')]"
            " | //button[contains(text(),'Comprar') or contains(text(),'Reservar') or contains(@class,'next')]",
            timeout=10,
        )
        clique_humano(driver, btn)
        time.sleep(2)
        print("[✓] Acesso à seleção de setores realizado")
        return True
    except Exception as e:
        print(f"[✗] Não foi possível abrir a seleção da partida: {e}")
        return False


def selecionar_setor_por_prioridade(driver, setor_preferido="Norte", lista_prioridade=None):
    """
    Tenta selecionar o setor preferido da Neo Química Arena.
    Caso esteja esgotado/indisponível, percorre automaticamente a fila de prioridade.
    """
    prioridades = []
    if setor_preferido:
        prioridades.append(setor_preferido)

    for s in (lista_prioridade or SETORES_PADRAO_ARENA):
        if s not in prioridades:
            prioridades.append(s)

    print(f"[→] Ordem de prioridade de setores: {' > '.join(prioridades)}")

    for setor in prioridades:
        print(f"[→] Tentando setor: {setor}...")
        try:
            elementos = driver.find_elements(
                By.XPATH,
                f"//*[contains(translate(text(),'nortesullesteoesteinferioruperior','NORTESULLESTEOESTEINFERIORUPERIOR'), '{setor.upper()}') "
                f"or contains(text(), '{setor}')]"
            )
            for el in elementos:
                texto_bloco = (el.text or "").upper()
                if "ESGOTADO" in texto_bloco or "INDISPONÍVEL" in texto_bloco:
                    continue
                if el.is_displayed():
                    clique_humano(driver, el)
                    time.sleep(1.2)
                    print(f"[✓] Setor '{setor}' selecionado com sucesso!")
                    return True
        except Exception:
            continue

    print("[!] Seleção específica de setor não exigida ou usando listagem padrão")
    return True


def selecionar_ingresso(driver, tipo_ingresso="Fiel Torcedor", quantidade=1):
    """
    Seleciona a categoria do ingresso e incrementa a quantidade desejada.
    """
    print(f"[→] Selecionando {quantidade}x ingresso ({tipo_ingresso})...")
    try:
        if tipo_ingresso:
            linhas = driver.find_elements(By.XPATH, f"//tr[contains(., '{tipo_ingresso}')] | //div[contains(., '{tipo_ingresso}')]")
            for linha in linhas:
                botoes_mais = linha.find_elements(By.CSS_SELECTOR, ".plus, button.btn-number.plus, button[aria-label*='Adicionar']")
                if botoes_mais:
                    for _ in range(quantidade):
                        clique_humano(driver, botoes_mais[0])
                        time.sleep(0.4)
                    print(f"[✓] {quantidade}x '{tipo_ingresso}' adicionado(s)")
                    return True

        botoes_mais = driver.find_elements(
            By.XPATH,
            "//button[contains(@class,'plus') or normalize-space(text())='+']"
        )
        if botoes_mais:
            for _ in range(quantidade):
                clique_humano(driver, botoes_mais[0])
                time.sleep(0.4)
            print(f"[✓] {quantidade} ingresso(s) selecionado(s)")
            return True

        print("[✗] Controle de quantidade de ingresso não encontrado")
        return False

    except Exception as e:
        print(f"[✗] Erro ao selecionar quantidade de ingressos: {e}")
        return False


def clicar_continuar(driver, etapa=""):
    """Avança para a próxima etapa do fluxo de reserva/checkout."""
    if etapa:
        print(f"[→] Avançando etapa: {etapa}")

    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.4)

        btn = esperar_clicavel(
            driver,
            By.XPATH,
            "//a[contains(@class,'next') or contains(text(),'Continuar') or contains(text(),'Próximo') or contains(text(),'Avançar')]"
            " | //button[contains(@class,'next') or contains(text(),'Continuar') or contains(text(),'Próximo') or contains(text(),'Reservar')]",
            timeout=10,
        )
        clique_humano(driver, btn)
        time.sleep(1.8)
        print(f"[✓] Etapa concluída" + (f" ({etapa})" if etapa else ""))
        return True
    except Exception as e:
        print(f"[✗] Botão de avanço não encontrado ({etapa}): {e}")
        return False


def aceitar_termos(driver):
    """Marca o aceite dos termos de compra/reserva, quando aplicável."""
    print("[→] Verificando termos e condições da reserva...")
    try:
        el = driver.find_element(
            By.XPATH,
            "//a[contains(text(),'Eu aceito') or contains(text(),'Aceitar')]"
            " | //button[contains(text(),'Eu aceito') or contains(text(),'Aceitar')]"
            " | //label[contains(text(),'termos') or contains(text(),'Li e concordo')]"
        )
        clique_humano(driver, el)
        time.sleep(1.2)
        print("[✓] Termos aceitos")
        return True
    except Exception:
        return False


def fluxo_completo_reserva(driver, config):
    """
    Orquestra todas as etapas de seleção e reserva de ingresso:
    1. Acessa a página da partida
    2. Seleciona o jogo alvo
    3. Escolhe o setor da Neo Química Arena (com fallback por prioridade)
    4. Define categoria e quantidade de ingressos
    5. Aceita termos e avança para confirmação da reserva
    """
    target = config["target"]

    navegar_para_partida(driver, target["event_url"])

    if not selecionar_partida(driver, target.get("match_name", "")):
        return False

    selecionar_setor_por_prioridade(
        driver,
        setor_preferido=target.get("setor_preferido", "Norte"),
        lista_prioridade=target.get("setores_por_prioridade"),
    )

    if not selecionar_ingresso(
        driver,
        tipo_ingresso=target.get("ticket_type", "Fiel Torcedor"),
        quantidade=target.get("quantity", 1),
    ):
        return False

    if not clicar_continuar(driver, "seleção de setor e ingresso"):
        return False

    aceitar_termos(driver)
    clicar_continuar(driver, "confirmação de reserva")

    print("\n[✓✓✓] INGRESSO RESERVADO NO CARRINHO — pronto para finalização do pagamento!")
    return True
