import unittest
from unittest.mock import patch

from selenium.common.exceptions import NoSuchElementException, TimeoutException

from bot import login


class ImmediateWait:
    """Substitui a espera temporizada por uma avaliação imediata no teste."""

    def __init__(self, driver, timeout):
        self.driver = driver

    def until(self, condition):
        result = condition(self.driver)
        if not result:
            raise TimeoutException("Indicador de sessão não encontrado")
        return result


class FakeDriver:
    def __init__(self, current_url, authenticated=False):
        self.current_url = current_url
        self.authenticated = authenticated

    def find_element(self, by, selector):
        if self.authenticated:
            return object()
        raise NoSuchElementException("Nenhum indicador de autenticação")


class VerificarLoginTests(unittest.TestCase):
    @patch("bot.login.WebDriverWait", ImmediateWait)
    def test_retorna_true_quando_encontra_indicador_de_sessao(self):
        driver = FakeDriver(
            "https://www.fieltorcedor.com.br/jogos",
            authenticated=True,
        )

        self.assertTrue(login.verificar_login_ok(driver))

    @patch("bot.login.WebDriverWait", ImmediateWait)
    def test_nao_confunde_pagina_publica_de_jogos_com_login(self):
        driver = FakeDriver(
            "https://www.fieltorcedor.com.br/jogos",
            authenticated=False,
        )

        self.assertFalse(login.verificar_login_ok(driver))

    @patch("bot.login.WebDriverWait", ImmediateWait)
    def test_nao_considera_url_dashboard_prova_suficiente(self):
        driver = FakeDriver(
            "https://www.fieltorcedor.com.br/dashboard",
            authenticated=False,
        )

        self.assertFalse(login.verificar_login_ok(driver))


if __name__ == "__main__":
    unittest.main()
