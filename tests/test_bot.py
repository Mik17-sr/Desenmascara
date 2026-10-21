from app.bot.client import format_analysis
from app.schemas.contract import AnalysisResult

# MarkdownV2 reserved characters, except "*" and "_", which format_analysis uses as markup.
RESERVED = set("[]()~`>#+-=|{}.!")


def unescaped_reserved(message: str) -> list[str]:
    found = []
    i = 0
    while i < len(message):
        if message[i] == "\\":
            i += 2
            continue
        if message[i] in RESERVED:
            found.append(message[i])
        i += 1
    return found


def test_fallback_texts_are_escaped():
    # The engine returns no recommendations when Ollama is unavailable, so the fixed texts are used.
    result = AnalysisResult(
        risk_level="inconclusive",
        risk_score=0,
        summary="El motor de IA local no está disponible temporalmente.",
    )
    message = format_analysis(result)

    assert unescaped_reserved(message) == []
    assert "• Verifica por otro canal antes de compartir datos o realizar pagos\\." in message
    assert "• El análisis automático puede equivocarse; revisa el contexto por tu cuenta\\." in message
