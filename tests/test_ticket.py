import unittest
from unittest.mock import Mock, patch

from bot import ticket


class FakeElement:
    def __init__(self, text="", displayed=True):
        self.text = text
        self.displayed = displayed

    def is_displayed(self):
        return self.displayed


class SelecionarSetorTests(unittest.TestCase):
    @patch("bot.ticket.time.sleep")
    @patch("bot.ticket.clique_humano")
    def test_retorna_true_quando_setor_e_selecionado(self, clique, sleep):
        driver = Mock()
        driver.find_elements.return_value = [FakeElement("Setor Norte")]

        resultado = ticket.selecionar_setor_por_prioridade(
            driver, setor_preferido="Norte", lista_prioridade=["Sul"]
        )

        self.assertTrue(resultado)
        clique.assert_called_once()

    @patch("bot.ticket.time.sleep")
    @patch("bot.ticket.clique_humano")
    def test_retorna_false_quando_todos_os_setores_estao_indisponiveis(
        self, clique, sleep
    ):
        driver = Mock()
        driver.find_elements.return_value = [FakeElement("ESGOTADO")]

        resultado = ticket.selecionar_setor_por_prioridade(
            driver, setor_preferido="Norte", lista_prioridade=["Sul"]
        )

        self.assertFalse(resultado)
        clique.assert_not_called()

    @patch("bot.ticket.time.sleep")
    @patch("bot.ticket.clique_humano")
    def test_retorna_false_quando_nao_encontra_setores(self, clique, sleep):
        driver = Mock()
        driver.find_elements.return_value = []

        resultado = ticket.selecionar_setor_por_prioridade(
            driver, setor_preferido="Norte", lista_prioridade=["Sul"]
        )

        self.assertFalse(resultado)
        clique.assert_not_called()


class FluxoReservaTests(unittest.TestCase):
    @patch("bot.ticket.selecionar_ingresso")
    @patch("bot.ticket.selecionar_setor_por_prioridade", return_value=False)
    @patch("bot.ticket.selecionar_partida", return_value=True)
    @patch("bot.ticket.navegar_para_partida")
    def test_interrompe_fluxo_quando_setor_nao_e_selecionado(
        self, navegar, partida, setor, ingresso
    ):
        driver = Mock()
        config = {
            "target": {
                "event_url": "https://example.test/event",
                "setor_preferido": "Norte",
                "setores_por_prioridade": ["Sul"],
            }
        }

        resultado = ticket.fluxo_completo_reserva(driver, config)

        self.assertFalse(resultado)
        ingresso.assert_not_called()


if __name__ == "__main__":
    unittest.main()
