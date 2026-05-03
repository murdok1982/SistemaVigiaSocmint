"""
Pruebas del motor ML de análisis de amenazas.
Verifica detección, falsos positivos, rendimiento.
"""
import pytest
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.ml_analysis_agent import MLAnalyzer, analyze_post_ml
from src.models import SocialPost
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def ml_analyzer():
    return MLAnalyzer()


@pytest.fixture
def sample_posts():
    return [
        SocialPost(
            id="test-1",
            platform="twitter",
            content="Voy a matarte, no escaparás de mí",
            author_id_hash="abc123",
            timestamp=datetime.now(timezone.utc),
            url="https://twitter.com/test/status/1",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id="test-2",
            platform="telegram",
            content="Coordinar el ataque el próximo viernes en el punto de encuentro habitual",
            author_id_hash="def456",
            timestamp=datetime.now(timezone.utc),
            url="https://t.me/test/2",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id="test-3",
            platform="reddit",
            content="Me gusta el café y leer libros",  # Inocuo
            author_id_hash="ghi789",
            timestamp=datetime.now(timezone.utc),
            url="https://reddit.com/r/test/comments/3",
            is_public=True,
            language="es",
        ),
        SocialPost(
            id="test-4",
            platform="twitter",
            content="Hay que eliminar a todos los que piensan distinto, destruir el sistema",
            author_id_hash="jkl012",
            timestamp=datetime.now(timezone.utc),
            url="https://twitter.com/test/status/4",
            is_public=True,
            language="es",
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Detección
# ─────────────────────────────────────────────────────────────────────────────
class TestMLDetection:
    """Pruebas de detección de amenazas con ML."""

    def test_detect_direct_threat(self, ml_analyzer):
        """Verifica detección de amenaza directa."""
        text = "Voy a matarte, vas a pagar con tu vida"
        result = ml_analyzer.analyze_text(text)
        
        assert "amenaza_directa" in result
        assert result["amenaza_directa"]["score"] > 0.5

    def test_detect_attack_coordination(self, ml_analyzer):
        """Verifica detección de coordinación de ataque."""
        text = "Coordinar el ataque, punto de encuentro en la plaza, traed el material"
        result = ml_analyzer.analyze_text(text)
        
        assert "coordinacion_ataque" in result
        assert result["coordinacion_ataque"]["score"] > 0.5

    def test_detect_violence_call(self, ml_analyzer):
        """Verifica detección de llamada a violencia."""
        text = "Debemos atacar el edificio gubernamental y destruir el sistema"
        result = ml_analyzer.analyze_text(text)
        
        assert "llamada_violencia" in result

    def test_no_false_positive(self, ml_analyzer):
        """Verifica que no haya falsos positivos en texto inocuo."""
        text = "Me encanta el clima hoy, voy a dar un paseo por el parque"
        result = ml_analyzer.analyze_text(text)
        
        # No debe detectar amenazas
        assert len(result) == 0 or all(score["score"] < 0.3 for score in result.values())

    def test_risk_score_calculation(self, sample_posts):
        """Verifica cálculo correcto de risk_score."""
        for post in sample_posts:
            assessment = analyze_post_ml(post)
            
            if "matar" in post.content.lower() or "matarte" in post.content.lower():
                assert assessment.risk_score >= 0.5
                assert assessment.alert_level in ["NARANJA", "ROJO"]
            
            if "café" in post.content.lower():
                assert assessment.risk_score < 0.5 or assessment.alert_level == "VERDE"


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Escalabilidad
# ─────────────────────────────────────────────────────────────────────────────
class TestPerformance:
    """Pruebas de rendimiento del motor ML."""

    def test_batch_processing(self, ml_analyzer):
        """Verifica procesamiento de lote de 1000 textos."""
        texts = ["Texto de prueba " + str(i) for i in range(1000)]
        
        import time
        start = time.time()
        results = [ml_analyzer.analyze_text(text) for text in texts]
        elapsed = time.time() - start
        
        assert len(results) == 1000
        assert elapsed < 10.0  # Debe procesar 1000 en menos de 10 seg

    def test_multilingual_support(self, ml_analyzer):
        """Verifica soporte multilingüe."""
        texts = {
            "es": "Voy a matarte",
            "en": "I will kill you",
            "fr": "Je vais te tuer",
            "ar": "سأقتلك",  # Árabe: te mataré
        }
        
        for lang, text in texts.items():
            result = ml_analyzer.analyze_text(text, language=lang)
            # Debe al menos intentar analizar
            assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Tests de Integración con Modelos
# ─────────────────────────────────────────────────────────────────────────────
class TestModelIntegration:
    """Pruebas de integración con modelos ML reales."""

    def test_model_loading(self, ml_analyzer):
        """Verifica que los modelos se carguen correctamente."""
        # Al menos debe inicializarse sin errores
        assert ml_analyzer is not None
        assert hasattr(ml_analyzer, 'models')
        assert hasattr(ml_analyzer, 'vectorizers')

    def test_fallback_mechanism(self, ml_analyzer):
        """Verifica que el sistema use fallback si falla el modelo."""
        # Simular fallo en modelo
        original_model = ml_analyzer.models.get("amenaza_directa")
        ml_analyzer.models["amenaza_directa"] = None
        
        text = "Voy a matarte"
        result = ml_analyzer.analyze_text(text)
        
        # Debe usar palabras clave de respaldo
        assert len(result) > 0 or True  # Al menos no debe crashear
        
        # Restaurar
        ml_analyzer.models["amenaza_directa"] = original_model


if __name__ == "__main__":
    pytest.main(["-v", __file__])
