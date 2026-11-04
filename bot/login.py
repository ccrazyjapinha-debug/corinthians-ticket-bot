"""
login.py — Módulo de autenticação automatizada no portal Fiel Torcedor / Ingressos.
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bot.browser import esperar_clicavel, clique_humano


def fazer_login(driver, login_usuario, senha):
    """
    Preenche as credenciais de acesso (CPF/E-mail e senha) no formulário de login.
    """
    print("[INFO] Preenchendo credenciais de acesso...")

    try:
        campo_usuario = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "input[name='username'], input[name='cpf'], input[type='email'], input#login, input#c2_username"
            ))
        )
        campo_usuario.clear()
        _digitar_humano(campo_usuario, login_usuario)
        time.sleep(random.uniform(0.4, 0.8))

        campo_senha = driver.find_element(
            By.CSS_SELECTOR,
            "input[type='password'], input[name='password'], input#senha, input#c2_password"
        )
        campo_senha.clear()
        _digitar_humano(campo_senha, senha)
        time.sleep(random.uniform(0.4, 0.8))

        print("[OK] Credenciais preenchidas")
        return True

    except Exception as e:
        print(f"[ERRO] Erro ao localizar campos de login: {e}")
        return False


def clicar_botao_login(driver):
    """Submete o formulário de autenticação."""
    try:
        botao = esperar_clicavel(
            driver,
            By.XPATH,
            "//button[@type='submit' or contains(text(),'Entrar') or contains(text(),'Acessar') or contains(@class,'settings_save')]",
            timeout=15
        )
        clique_humano(driver, botao)
        print("[OK] Formulário de login enviado")
        time.sleep(3)
        return True

    except Exception as e:
        print(f"[ERRO] Erro ao submeter login: {e}")
        return False


def abrir_modal_login(driver):
    """Abre a página ou modal de autenticação caso o usuário ainda não esteja logado."""
    try:
        botao = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(text(),'Entrar') or contains(text(),'Login') or contains(@href,'login')]"
                " | //button[contains(text(),'Entrar') or contains(text(),'Login')]"
            ))
        )
        clique_humano(driver, botao)
        time.sleep(2)
        print("[OK] Tela de login aberta")
        return True
    except Exception as e:
        print(f"[AVISO] Botão de abertura de login não encontrado: {e}")
        return False


def verificar_login_ok(driver):
    """Verifica se já existe uma sessão autenticada ativa no navegador."""
    try:
        WebDriverWait(driver, 8).until(
            EC.any_of(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".user-logged, .minha-conta, .perfil-usuario, a[href*='logout'], a[href*='sair']"
                )),
                EC.url_contains("minha-conta"),
                EC.url_contains("dashboard"),
                EC.url_contains("jogos")
            )
        )
        print("[OK] Sessão autenticada confirmada!")
        return True
    except Exception:
        return False


def _digitar_humano(elemento, texto):
    """Simula digitação caractere a caractere com intervalo variável."""
    for char in texto:
        elemento.send_keys(char)
        time.sleep(random.uniform(0.04, 0.12))
