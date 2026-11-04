"""
notifier.py — Alertas visuais no console e notificações sonoras assíncronas (Windows).
"""

import threading

try:
    import winsound
    TEM_SOM = True
except ImportError:
    TEM_SOM = False


def notificar_sucesso(mensagem="INGRESSO DO CORINTHIANS RESERVADO COM SUCESSO!"):
    """Emite alerta sonoro e visual indicando conclusão da reserva."""
    print("\n" + "=" * 60)
    print(f"  [SUCESSO] {mensagem}")
    print("=" * 60 + "\n")

    if TEM_SOM:
        def _tocar_som():
            for freq, dur in [(800, 200), (1000, 200), (1250, 450)]:
                winsound.Beep(freq, dur)

        threading.Thread(target=_tocar_som, daemon=True).start()


def notificar_erro(mensagem="FALHA NO FLUXO DE RESERVA"):
    """Emite alerta de erro visual e sonoro."""
    print(f"\n  [ERRO] {mensagem}\n")

    if TEM_SOM:
        def _tocar_erro():
            winsound.Beep(400, 500)

        threading.Thread(target=_tocar_erro, daemon=True).start()
