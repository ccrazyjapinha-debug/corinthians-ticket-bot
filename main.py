"""
╔══════════════════════════════════════════════════════════════════╗
║   🦅  CORINTHIANS TICKET BOT — AUTOMAÇÃO DE RESERVA (RPA)    🦅  ║
║   Monitoramento de Abertura + Seleção de Setor com Fallback      ║
╚══════════════════════════════════════════════════════════════════╝

USO:
  python main.py                  → Modo completo (monitor + reserva)
  python main.py --debug          → Mantém o navegador aberto ao finalizar
  python main.py --sem-monitor    → Pula o monitor e executa a reserva direto
  python main.py --setor "Norte"  → Define o setor prioritário via CLI
  python main.py --tentativas 3   → Define o número de tentativas em caso de falha
"""

import os
import sys
import json
import time
import argparse
from colorama import init, Fore, Style

from bot.browser import criar_driver, iniciar_watchdog
from bot.login import fazer_login, clicar_botao_login, abrir_modal_login, verificar_login_ok
from bot.captcha import resolver_captcha_api, captcha_manual
from bot.ticket import fluxo_completo_reserva
from bot.notifier import notificar_sucesso, notificar_erro
from bot.monitor import aguardar_horario_abertura, monitorar_abertura, fazer_login_antecipado

init(autoreset=True)


def carregar_config(caminho="config.json"):
    """
    Carrega as configurações do arquivo JSON especificado.
    Caso config.json não exista, utiliza config.example.json como fallback.
    """
    if not os.path.exists(caminho) and os.path.exists("config.example.json"):
        print(Fore.YELLOW + f"[!] '{caminho}' não encontrado — carregando 'config.example.json'.")
        caminho = "config.example.json"

    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"[✗] Arquivo de configuração '{caminho}' não encontrado!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(Fore.RED + f"[✗] Erro de sintaxe no arquivo JSON: {e}")
        sys.exit(1)


def exibir_banner():
    print(Fore.WHITE + Style.BRIGHT + """
╔══════════════════════════════════════════════════════════════════╗
║   🦅  CORINTHIANS TICKET BOT — FIEL TORCEDOR / NEO QUÍMICA   🦅  ║
║   Automação Web Resiliente (Python + Selenium + Chrome CDP)      ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def executar_reserva(driver, config, url_override=None, modo_debug=False):
    """
    Executa o pipeline completo de seleção de setor, reserva e autenticação.
    """
    creds = config["credentials"]
    captcha_cfg = config["captcha"]

    if url_override:
        config["target"]["event_url"] = url_override

    print(Fore.YELLOW + "\n━━━ ETAPA 1: NAVEGAÇÃO E SELEÇÃO DE SETOR (NEO QUÍMICA ARENA) ━━━")
    sucesso = fluxo_completo_reserva(driver, config)

    if not sucesso:
        notificar_erro("Não foi possível concluir a seleção do ingresso")
        return False

    print(Fore.YELLOW + "\n━━━ ETAPA 2: VALIDAÇÃO DE SESSÃO ━━━")
    if not verificar_login_ok(driver):
        abrir_modal_login(driver)
        time.sleep(1.5)
        login_user = creds.get("login") or creds.get("email", "")
        fazer_login(driver, login_user, creds["password"])

        print(Fore.YELLOW + "\n━━━ ETAPA 3: VERIFICAÇÃO DE SEGURANÇA ━━━")
        captcha_ok = False
        if captcha_cfg.get("service") == "2captcha" and captcha_cfg.get("api_key"):
            captcha_ok = resolver_captcha_api(driver, captcha_cfg["api_key"])

        if not captcha_ok:
            captcha_ok = captcha_manual(driver, timeout=120)

        if not captcha_ok:
            notificar_erro("Verificação de segurança não concluída a tempo")
            return False

        clicar_botao_login(driver)
        time.sleep(3)

    notificar_sucesso(
        f"INGRESSO RESERVADO COM SUCESSO!\n"
        f"  Partida: {config['target'].get('match_name', 'Corinthians')}\n"
        f"  Setor: {config['target'].get('setor_preferido', 'Norte')}\n"
        f"  URL: {driver.current_url}"
    )

    if not modo_debug:
        print(Fore.GREEN + "\n[→] Reserva ativa! Aguardando 90s para conclusão manual do pagamento...")
        time.sleep(90)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Corinthians Ticket Bot — Automação de Reserva de Ingressos"
    )
    parser.add_argument("--debug", action="store_true", help="Mantém a sessão do navegador aberta ao finalizar")
    parser.add_argument("--config", default="config.json", help="Caminho para o arquivo de configuração JSON")
    parser.add_argument("--tentativas", type=int, default=1, help="Número máximo de tentativas em caso de falha")
    parser.add_argument("--sem-monitor", action="store_true", help="Executa a reserva imediatamente sem aguardar o monitor")
    parser.add_argument("--setor", default=None, help="Sobrescreve o setor prioritário (ex: 'Norte', 'Sul', 'Leste Inferior')")
    args = parser.parse_args()

    exibir_banner()
    config = carregar_config(args.config)

    if args.setor:
        config["target"]["setor_preferido"] = args.setor
        print(Fore.CYAN + f"[→] Setor prioritário definido via CLI: {args.setor}")

    monitor_cfg = config.get("monitor", {})
    target_cfg = config["target"]

    print(Fore.CYAN + f"⚽ Partida:    {target_cfg.get('match_name', 'Corinthians')}")
    print(Fore.CYAN + f"🏟️  Estádio:    {target_cfg.get('stadium', 'Neo Química Arena')}")
    print(Fore.CYAN + f"🎟️  Setor Alvo: {target_cfg.get('setor_preferido', 'Norte')} ({target_cfg.get('ticket_type', 'Fiel Torcedor')})")
    print(Fore.CYAN + f"🔢 Quantidade: {target_cfg.get('quantity', 1)}\n")

    driver = criar_driver(
        headless=config["settings"].get("headless", False),
        page_load_timeout=config["settings"].get("page_load_timeout", 30),
    )

    def _watchdog_reload(drv):
        """Callback de recuperação acionado caso a página pare de responder."""
        try:
            drv.refresh()
            print(Fore.YELLOW + "[WATCHDOG] Página recarregada automaticamente para recuperar sessão")
        except Exception:
            print(Fore.RED + "[WATCHDOG] Falha ao tentar recarregar a página")

    iniciar_watchdog(driver, timeout_segundos=90, callback=_watchdog_reload)
    print(Fore.CYAN + "[✓] Watchdog anti-stall ativo (timeout: 90s)")

    try:
        url_venda = None

        if not args.sem_monitor and monitor_cfg.get("ativo", False):
            horario_abertura = monitor_cfg.get("venda_abre_em")
            minutos_antes = monitor_cfg.get("iniciar_antes_minutos", 5)

            if horario_abertura:
                aguardar_horario_abertura(horario_abertura, minutos_antes)

            if monitor_cfg.get("login_antecipado", True):
                fazer_login_antecipado(driver, config)

            print(Fore.YELLOW + "\n━━━ MONITORANDO ABERTURA DAS RESERVAS ━━━")
            url_venda = monitorar_abertura(driver, config)

        for i in range(args.tentativas):
            if args.tentativas > 1:
                print(Fore.CYAN + f"\n[→] Tentativa {i + 1}/{args.tentativas}")

            sucesso = executar_reserva(
                driver, config, url_override=url_venda, modo_debug=args.debug
            )

            if sucesso:
                print(Fore.GREEN + Style.BRIGHT + "\n✅ AUTOMAÇÃO FINALIZADA COM SUCESSO!\n")
                break

            if i < args.tentativas - 1:
                delay = config["settings"].get("retry_delay", 2)
                print(Fore.YELLOW + f"[→] Nova tentativa em {delay}s...")
                time.sleep(delay)
        else:
            if args.tentativas > 1:
                print(Fore.RED + f"\n❌ Todas as {args.tentativas} tentativas falharam.\n")

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Execução interrompida pelo usuário.")

    except Exception as e:
        print(Fore.RED + f"\n[✗] Erro inesperado: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        notificar_erro(str(e))

    finally:
        if args.debug:
            print(Fore.CYAN + "\n[DEBUG] Sessão mantida para inspeção.")
            input("Pressione Enter para encerrar a conexão do driver...")


if __name__ == "__main__":
    main()
