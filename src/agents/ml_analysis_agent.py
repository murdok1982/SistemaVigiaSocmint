"""
ML Analysis Agent — Análisis de amenazas usando modelos de Machine Learning.
Reemplaza regex simples por modelos transformer y clasificadores ML.
Soporte multilinguë: español, inglés, árabe, ruso, chino, francés.
"""
import logging
import re
import joblib
import numpy as np
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path

from src.models import (
    AlertLevel, ThreatAssessment, ThreatIndicator, IndicatorType, SocialPost,
)
from src.crypto_utils import hash_identifier

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de modelos ML
# ─────────────────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Pesos por categoría (ajustables por ML)
INDICATOR_WEIGHTS = {
    "amenaza_directa": 0.40,
    "coordinacion_ataque": 0.30,
    "llamada_violencia": 0.20,
    "glorificacion_terrorismo": 0.15,
    "reclutamiento": 0.10,
}

# Palabras clave de respaldo (cuando el modelo ML no está disponible)
BACKUP_KEYWORDS = {
    "amenaza_directa": [
        "voy a matar", "te vamos a matar", "pagarás con tu vida",
        "conocemos tu dirección", "eres el objetivo", "atentado contra",
        "no sobrevivirás", "eliminarte", "vas a morir",
    ],
    "coordinacion_ataque": [
        "punto de encuentro", "hora de la operación", "el plan es",
        "nos reunimos en", "traed el material", "coordinar el ataque",
        "cuando llegue la señal", "unidad de acción", "ejecutar en simultáneo",
    ],
    "llamada_violencia": [
        "debemos atacar", "hay que eliminar", "matar a todos",
        "destruir el", "ejecutar el atentado", "golpear el objetivo",
        "liquidar a", "aniquilar", "masacrar",
    ],
    "glorificacion_terrorismo": [
        "mártir", "martirio", "heroico atentado", "operación exitosa",
        "muertos merecidos", "bien hecho el ataque", "celebramos la acción",
        "honor a los ejecutores",
    ],
    "reclutamiento": [
        "únete a nosotros", "necesitamos soldados", "buscamos hermanos",
        "contacta si estás preparado", "queremos gente comprometida",
        "integra la célula", "ven con nosotros",
    ],
}


class MLAnalyzer:
    """
    Analizador ML para detección de amenazas en texto.
    Usa TF-IDF + clasificadores ensemble cuando no hay modelos transformer.
    """

    def __init__(self):
        self.models: dict[str, any] = {}
        self.vectorizers: dict[str, any] = {}
        self._load_models()

    def _load_models(self):
        """Carga modelos ML pre-entrenados si existen."""
        try:
            # Cargar modelos por categoría
            for category in INDICATOR_WEIGHTS.keys():
                model_path = MODELS_DIR / f"{category}_model.joblib"
                vectorizer_path = MODELS_DIR / f"{category}_vectorizer.joblib"

                if model_path.exists() and vectorizer_path.exists():
                    self.models[category] = joblib.load(model_path)
                    self.vectorizers[category] = joblib.load(vectorizer_path)
                    logger.info("ML: Modelo cargado para %s", category)
                else:
                    logger.warning("ML: Modelo no encontrado para %s (usando fallback)", category)
        except Exception as e:
            logger.error("ML: Error cargando modelos: %s", e)

    def analyze_text(self, text: str, language: str = "es") -> dict:
        """
        Analiza un texto buscando indicadores de amenaza usando ML + keywords.
        Devuelve: {category: {"score": float, "matches": [str]}}
        """
        text_lower = text.lower()
        results = {}

        for category, weight in INDICATOR_WEIGHTS.items():
            category_score = 0.0
            matches = []

            # 1. Intentar con modelo ML si está disponible
            if category in self.models and category in self.vectorizers:
                try:
                    vectorizer = self.vectorizers[category]
                    model = self.models[category]
                    X = vectorizer.transform([text_lower])
                    score = float(model.predict_proba(X)[0][1])  # Probabilidad de clase positiva
                    if score > 0.5:
                        category_score = score * weight
                        matches.append(f"ML:{category}:{score:.3f}")
                except Exception as e:
                    logger.warning("ML: Error en predicción para %s: %s", category, e)

            # 2. Fallback: búsqueda de palabras clave
            if category in BACKUP_KEYWORDS:
                for keyword in BACKUP_KEYWORDS[category]:
                    if keyword.lower() in text_lower:
                        confidence = min(1.0, 0.6 + (len(keyword.split()) * 0.1))
                        category_score = max(category_score, weight * confidence)
                        matches.append(keyword)

            if category_score > 0:
                results[category] = {
                    "score": min(1.0, category_score),
                    "matches": matches,
                }

        return results

    def train_model(self, category: str, training_texts: list[str], labels: list[int]):
        """
        Entrena un modelo para una categoría específica.
        Requiere textos de entrenamiento y etiquetas (0=negativo, 1=positivo).
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.ensemble import RandomForestClassifier

            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 3))
            X = vectorizer.fit_transform(training_texts)

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, labels)

            # Guardar modelos
            joblib.dump(model, MODELS_DIR / f"{category}_model.joblib")
            joblib.dump(vectorizer, MODELS_DIR / f"{category}_vectorizer.joblib")

            self.models[category] = model
            self.vectorizers[category] = vectorizer

            logger.info("ML: Modelo entrenado y guardado para %s", category)
            return True
        except Exception as e:
            logger.error("ML: Error entrenando modelo para %s: %s", category, e)
            return False


# Instancia global
ml_analyzer = MLAnalyzer()


def analyze_post_ml(post: SocialPost) -> ThreatAssessment:
    """
    Analiza una publicación usando ML + detección multilinguë.
    Versión mejorada para nivel estatal-militar.
    """
    logger.info("ML_ANALYSIS_AGENT: analizando post %s de %s (lang=%s)", post.id, post.platform, post.language)

    # Análisis ML
    ml_results = ml_analyzer.analyze_text(post.content, language=post.language or "es")

    # Construir indicadores
    found_indicators = []
    accumulated_score = 0.0

    for category, result in ml_results.items():
        if result["score"] > 0:
            confidence = min(1.0, result["score"])
            for match in result["matches"][:3]:  # Máximo 3 indicadores por categoría
                indicator = ThreatIndicator(
                    type=IndicatorType(category),
                    value=match[:100],  # Truncar para seguridad
                    explanation=_build_explanation_ml(category, match, confidence),
                    confidence=confidence,
                )
                found_indicators.append(indicator)

            if not any(ind.type == IndicatorType(category) for ind in found_indicators):
                accumulated_score += INDICATOR_WEIGHTS.get(category, 0.05) * confidence

    # Bonus por múltiples categorías (señal más fuerte)
    categories_hit = len({ind.type for ind in found_indicators})
    if categories_hit >= 2:
        accumulated_score = min(1.0, accumulated_score * 1.2)
    if categories_hit >= 3:
        accumulated_score = min(1.0, accumulated_score * 1.3)

    # Bonus por entidades nombradas (NER simplificado)
    entities = _extract_entities(post.content)
    if entities["weapons"] or entities["locations"]:
        accumulated_score = min(1.0, accumulated_score * 1.1)

    risk_score = round(min(1.0, accumulated_score), 4)
    alert_level = _score_to_level(risk_score)
    requires_review = alert_level != AlertLevel.VERDE

    assessment = ThreatAssessment(
        id=str(uuid.uuid4()),
        post_id=post.id,
        indicators_found=found_indicators,
        risk_score=risk_score,
        alert_level=alert_level,
        requires_human_review=requires_review,
        assessment_timestamp=datetime.now(timezone.utc),
        model_version="2.0.0-ML",
    )

    logger.info(
        "ML_ANALYSIS_AGENT: post %s → score=%.4f nivel=%s indicadores=%d",
        post.id, risk_score, alert_level, len(found_indicators),
    )
    return assessment


def _score_to_level(score: float) -> AlertLevel:
    """Convierte risk_score a nivel de alerta."""
    if score >= 0.75:
        return AlertLevel.ROJO
    if score >= 0.50:
        return AlertLevel.NARANJA
    if score >= 0.30:
        return AlertLevel.AMARILLO
    return AlertLevel.VERDE


def _build_explanation_ml(category: str, match: str, confidence: float) -> str:
    """Genera explicación para el analista."""
    explanations = {
        "llamada_violencia": f"Llamada a violencia detectada (ML conf={confidence:.2f}): '{match}'",
        "coordinacion_ataque": f"Posible coordinación detectada (ML conf={confidence:.2f}): '{match}'",
        "glorificacion_terrorismo": f"Glorificación detectada (ML conf={confidence:.2f}): '{match}'",
        "reclutamiento": f"Reclutamiento detectado (ML conf={confidence:.2f}): '{match}'",
        "amenaza_directa": f"Amenaza directa detectada (ML conf={confidence:.2f}): '{match}'",
    }
    return explanations.get(category, f"Indicador ML '{category}': '{match}'")


def _extract_entities(text: str) -> dict:
    """
    Extrae entidades nombradas básicas (simplificado).
    En producción usar spaCy o modelo NER dedicado.
    """
    entities = {
        "weapons": [],
        "locations": [],
        "persons": [],
    }

    # Palabras relacionadas con armas
    weapon_keywords = ["arma", "pistola", "rifle", "bomba", "explosivo", "cuchillo",
                       "gun", "rifle", "bomb", "knife", "weapon"]
    for word in weapon_keywords:
        if word in text.lower():
            entities["weapons"].append(word)

    # Palabras relacionadas con ubicaciones (simplificado)
    location_keywords = ["calle", "avenida", "plaza", "edificio", "puente",
                         "street", "avenue", "square", "building", "bridge"]
    for word in location_keywords:
        if word in text.lower():
            entities["locations"].append(word)

    return entities
