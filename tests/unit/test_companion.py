import sys
from types import SimpleNamespace

sys.path.insert(0, ".")

from cloud.agents import companion


def test_idioma_e_historico_da_conversa_sao_preservados():
    assert companion.detectar_idioma("hello") == "en"
    assert companion.detectar_idioma("Oi, tudo bem?") == "pt-BR"

    messages = companion._provider_messages(
        "What was my dog's name?",
        {
            "nome": "Maria",
            "historico": [
                {"role": "user", "content": "My dog was named Lucky."},
                {"role": "assistant", "content": "Lucky sounds special."},
            ],
        },
        companion.SYSTEM_PROMPT_EN,
    )
    assert messages[-3]["content"] == "My dog was named Lucky."
    assert messages[-1]["content"] == "What was my dog's name?"


def test_gpt_oss_tem_tokens_de_saida_e_tenta_novamente_resposta_vazia(monkeypatch):
    chamadas = []
    respostas = iter(("", "Estou aqui com você. Vamos conversar."))

    class CompletionsFake:
        def create(self, **kwargs):
            chamadas.append(kwargs)
            texto = next(respostas)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=texto))]
            )

    cliente = SimpleNamespace(
        chat=SimpleNamespace(completions=CompletionsFake())
    )
    monkeypatch.setattr(companion, "_groq", cliente)
    monkeypatch.setattr(companion, "GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setattr(companion, "_bedrock", False)

    resposta = companion.conversar("Estou com saudade.", {"nome": "Dona Maria"})

    assert resposta == "Estou aqui com você. Vamos conversar."
    assert len(chamadas) == 2
    assert all(chamada["max_tokens"] == 200 for chamada in chamadas)
    assert all(chamada["reasoning_effort"] == "low" for chamada in chamadas)
    assert chamadas[1]["temperature"] < chamadas[0]["temperature"]
