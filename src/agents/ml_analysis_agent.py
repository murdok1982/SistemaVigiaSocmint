"""
ML Analysis Agent — Análisis de amenazas usando modelos de Machine Learning.

Pipeline en cascada:
  1. TransformerMLAnalyzer (sentence-transformers multilingüe vs anchors)
     - Si VIGIA_DISABLE_TRANSFORMERS=true o el modelo no carga -> se desactiva.
  2. KeywordMLAnalyzer (TF-IDF + keywords) -> siempre disponible como fallback
     y refuerzo (score = max(transformer, keyword)).
  3. NER:
     - spaCy multilingüe (xx_ent_wiki_sm) si está instalado.
     - Fallback: keywords + regex.

Idiomas soportados por el transformer: es, en, ar, ru, zh (5+ por anchors).
"""
from __future__ import annotations

import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from src.models import (
    AlertLevel,
    IndicatorType,
    SocialPost,
    ThreatAssessment,
    ThreatIndicator,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuración general
# ─────────────────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

DISABLE_TRANSFORMERS = os.environ.get("VIGIA_DISABLE_TRANSFORMERS", "false").lower() == "true"
TRANSFORMER_MODEL_NAME = os.environ.get(
    "VIGIA_TRANSFORMER_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2",
)
TRANSFORMER_THRESHOLD = float(os.environ.get("VIGIA_TRANSFORMER_THRESHOLD", "0.55"))
SPACY_MODEL_NAME = os.environ.get("VIGIA_SPACY_MODEL", "xx_ent_wiki_sm")

# Pesos por categoría
INDICATOR_WEIGHTS: dict[str, float] = {
    "amenaza_directa": 0.40,
    "coordinacion_ataque": 0.30,
    "llamada_violencia": 0.20,
    "glorificacion_terrorismo": 0.15,
    "reclutamiento": 0.10,
}


# ─────────────────────────────────────────────────────────────────────────────
# Anchor sentences multilingües por categoría
# (es, en, ar, ru, zh — mínimo 3 por idioma por categoría)
# ─────────────────────────────────────────────────────────────────────────────
ANCHOR_SENTENCES: dict[str, list[str]] = {
    "amenaza_directa": [
        # Español
        "Voy a matarte y conozco tu dirección",
        "Te vamos a eliminar, no escaparás",
        "Pagarás con tu vida lo que has hecho",
        # Inglés
        "I am going to kill you and your family",
        "You will not survive what is coming for you",
        "I know where you live and you will pay",
        # Árabe
        "سأقتلك أنت وعائلتك",
        "لن تنجو مما سيحدث لك",
        "أعرف عنوانك وستدفع الثمن",
        # Ruso
        "Я тебя убью, ты не уйдёшь живым",
        "Мы знаем твой адрес, тебе конец",
        "Ты заплатишь за это своей жизнью",
        # Chino
        "我会杀了你,你逃不掉",
        "我们知道你的地址,你死定了",
        "你会为此付出生命的代价",
    ],
    "coordinacion_ataque": [
        # Español
        "Punto de encuentro a las diez en la plaza, traed el material",
        "Coordinemos el ataque para el viernes a primera hora",
        "Cuando llegue la señal, todas las unidades ejecutan en simultáneo",
        # Inglés
        "Meet point at ten in the square, bring the equipment",
        "Let us coordinate the attack for Friday morning",
        "When the signal arrives all units execute simultaneously",
        # Árabe
        "نقطة الالتقاء الساعة العاشرة في الساحة، أحضروا المعدات",
        "لننسق الهجوم يوم الجمعة في الصباح الباكر",
        "عندما تصل الإشارة، تنفذ جميع الوحدات في وقت واحد",
        # Ruso
        "Точка сбора в десять на площади, принесите снаряжение",
        "Скоординируем атаку на пятницу с утра",
        "Когда поступит сигнал, все группы действуют одновременно",
        # Chino
        "十点在广场集合,带上装备",
        "我们协调周五一早发动袭击",
        "信号一到,所有小组同时行动",
    ],
    "llamada_violencia": [
        # Español
        "Hay que eliminar a todos los traidores del sistema",
        "Debemos atacar el edificio gubernamental sin piedad",
        "Liquidemos a quienes piensan distinto",
        # Inglés
        "We must eliminate all the traitors of the system",
        "We have to attack the government building without mercy",
        "Let us crush everyone who thinks differently",
        # Árabe
        "يجب أن نقضي على كل خونة النظام",
        "علينا أن نهاجم المبنى الحكومي بلا رحمة",
        "لنسحق كل من يفكر بشكل مختلف",
        # Ruso
        "Мы должны уничтожить всех предателей системы",
        "Надо без пощады атаковать здание правительства",
        "Раздавим всех, кто думает иначе",
        # Chino
        "我们必须消灭所有体制的叛徒",
        "我们要毫不留情地攻击政府大楼",
        "把所有想法不同的人都铲除",
    ],
    "glorificacion_terrorismo": [
        # Español
        "Honor a los mártires del heroico atentado",
        "Celebramos la operación exitosa contra el enemigo",
        "Los muertos merecidos son una victoria nuestra",
        # Inglés
        "Honor to the martyrs of the heroic attack",
        "We celebrate the successful operation against the enemy",
        "Those deserved dead are a victory for our cause",
        # Árabe
        "المجد لشهداء العملية البطولية",
        "نحتفل بالعملية الناجحة ضد العدو",
        "هؤلاء القتلى المستحقون انتصار لقضيتنا",
        # Ruso
        "Слава мученикам героического теракта",
        "Празднуем успешную операцию против врага",
        "Эти заслуженные жертвы — наша победа",
        # Chino
        "向英勇袭击的烈士致敬",
        "我们庆祝针对敌人的成功行动",
        "这些罪有应得的死者是我们的胜利",
    ],
    "reclutamiento": [
        # Español
        "Únete a nosotros, buscamos hermanos comprometidos",
        "Necesitamos soldados para nuestra causa, contacta si estás preparado",
        "Integra la célula y forma parte del cambio",
        # Inglés
        "Join us, we are looking for committed brothers",
        "We need soldiers for our cause, contact us if you are ready",
        "Become part of the cell and join the change",
        # Árabe
        "انضم إلينا، نبحث عن إخوة ملتزمين",
        "نحتاج جنوداً لقضيتنا، تواصل معنا إذا كنت مستعداً",
        "انضم إلى الخلية وكن جزءاً من التغيير",
        # Ruso
        "Присоединяйся к нам, ищем преданных братьев",
        "Нам нужны солдаты для нашего дела, свяжись если готов",
        "Вступай в ячейку и стань частью перемен",
        # Chino
        "加入我们,我们寻找忠诚的兄弟",
        "我们需要为事业战斗的士兵,准备好就联系我们",
        "加入小组,成为变革的一员",
    ],
}


# Palabras clave de respaldo (clasificador clásico)
BACKUP_KEYWORDS: dict[str, list[str]] = {
    "amenaza_directa": [
        "voy a matar", "te vamos a matar", "pagarás con tu vida",
        "conocemos tu dirección", "eres el objetivo", "atentado contra",
        "no sobrevivirás", "eliminarte", "vas a morir",
        "i will kill you", "you will die", "i know where you live",
    ],
    "coordinacion_ataque": [
        "punto de encuentro", "hora de la operación", "el plan es",
        "nos reunimos en", "traed el material", "coordinar el ataque",
        "cuando llegue la señal", "unidad de acción", "ejecutar en simultáneo",
        "meet point", "coordinate the attack",
    ],
    "llamada_violencia": [
        "debemos atacar", "hay que eliminar", "matar a todos",
        "destruir el", "ejecutar el atentado", "golpear el objetivo",
        "liquidar a", "aniquilar", "masacrar",
        "we must attack", "destroy the",
    ],
    "glorificacion_terrorismo": [
        "mártir", "martirio", "heroico atentado", "operación exitosa",
        "muertos merecidos", "bien hecho el ataque", "celebramos la acción",
        "honor a los ejecutores",
        "honor to the martyrs", "successful operation",
    ],
    "reclutamiento": [
        "únete a nosotros", "necesitamos soldados", "buscamos hermanos",
        "contacta si estás preparado", "queremos gente comprometida",
        "integra la célula", "ven con nosotros",
        "join us", "we need soldiers",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Singletons lazy para modelos pesados
# ─────────────────────────────────────────────────────────────────────────────
_TRANSFORMER_LOCK = threading.Lock()
_NER_LOCK = threading.Lock()

_transformer_model: Any = None
_transformer_anchor_emb: dict[str, np.ndarray] | None = None
_transformer_failed: bool = False

_ner_pipeline: Any = None
_ner_failed: bool = False


def _get_transformer():
    """Carga el modelo sentence-transformer una única vez (lazy)."""
    global _transformer_model, _transformer_anchor_emb, _transformer_failed

    if DISABLE_TRANSFORMERS:
        return None, None
    if _transformer_failed:
        return None, None
    if _transformer_model is not None and _transformer_anchor_emb is not None:
        return _transformer_model, _transformer_anchor_emb

    with _TRANSFORMER_LOCK:
        if _transformer_failed:
            return None, None
        if _transformer_model is not None and _transformer_anchor_emb is not None:
            return _transformer_model, _transformer_anchor_emb
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(
                "ML: cargando modelo transformer multilingüe '%s' (primer uso, lento)",
                TRANSFORMER_MODEL_NAME,
            )
            model = SentenceTransformer(TRANSFORMER_MODEL_NAME)
            anchor_emb: dict[str, np.ndarray] = {}
            for category, sentences in ANCHOR_SENTENCES.items():
                emb = model.encode(sentences, normalize_embeddings=True, convert_to_numpy=True)
                anchor_emb[category] = emb
            _transformer_model = model
            _transformer_anchor_emb = anchor_emb
            logger.info("ML: transformer cargado, %d categorías con anchors", len(anchor_emb))
            return _transformer_model, _transformer_anchor_emb
        except Exception as exc:
            _transformer_failed = True
            logger.warning(
                "ML: no se pudo cargar el transformer ('%s'): %s. Fallback a KeywordMLAnalyzer.",
                TRANSFORMER_MODEL_NAME, exc,
            )
            return None, None


def _get_ner_pipeline():
    """Carga el modelo spaCy NER una única vez (lazy)."""
    global _ner_pipeline, _ner_failed

    if _ner_failed:
        return None
    if _ner_pipeline is not None:
        return _ner_pipeline

    with _NER_LOCK:
        if _ner_failed:
            return None
        if _ner_pipeline is not None:
            return _ner_pipeline
        try:
            import spacy
            logger.info("ML: cargando modelo spaCy '%s' (primer uso)", SPACY_MODEL_NAME)
            nlp = spacy.load(SPACY_MODEL_NAME)
            _ner_pipeline = nlp
            logger.info("ML: spaCy cargado correctamente")
            return _ner_pipeline
        except Exception as exc:
            _ner_failed = True
            logger.warning(
                "ML: no se pudo cargar spaCy ('%s'): %s. Fallback a NER por keywords.",
                SPACY_MODEL_NAME, exc,
            )
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Analizador clásico (TF-IDF + keywords) — fallback siempre disponible
# ─────────────────────────────────────────────────────────────────────────────
class KeywordMLAnalyzer:
    """
    Analizador clásico: modelos TF-IDF entrenados (si existen en /models)
    + búsqueda de keywords de respaldo. Funciona offline, sin dependencias
    pesadas. Es el único analizador garantizado en CI sin GPU/RAM.
    """

    def __init__(self) -> None:
        self.models: dict[str, Any] = {}
        self.vectorizers: dict[str, Any] = {}
        self._load_models()

    def _load_models(self) -> None:
        try:
            for category in INDICATOR_WEIGHTS:
                model_path = MODELS_DIR / f"{category}_model.joblib"
                vectorizer_path = MODELS_DIR / f"{category}_vectorizer.joblib"
                if model_path.exists() and vectorizer_path.exists():
                    self.models[category] = joblib.load(model_path)
                    self.vectorizers[category] = joblib.load(vectorizer_path)
                    logger.info("ML[keyword]: modelo cargado para %s", category)
                else:
                    logger.debug("ML[keyword]: sin modelo entrenado para %s (usando keywords)", category)
        except Exception as exc:
            logger.error("ML[keyword]: error cargando modelos: %s", exc)

    def analyze_text(self, text: str, language: str = "es") -> dict:
        text_lower = (text or "").lower()
        results: dict[str, dict] = {}

        for category, weight in INDICATOR_WEIGHTS.items():
            category_score = 0.0
            matches: list[str] = []

            # 1. Modelo TF-IDF si existe
            if category in self.models and category in self.vectorizers:
                try:
                    vectorizer = self.vectorizers[category]
                    model = self.models[category]
                    X = vectorizer.transform([text_lower])
                    proba = model.predict_proba(X)[0]
                    score = float(proba[1]) if len(proba) > 1 else float(proba[0])
                    if score > 0.5:
                        category_score = score * weight
                        matches.append(f"ML:{category}:{score:.3f}")
                except Exception as exc:
                    logger.warning("ML[keyword]: predicción falló %s: %s", category, exc)

            # 2. Keywords
            for keyword in BACKUP_KEYWORDS.get(category, []):
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

    def train_model(self, category: str, training_texts: list[str], labels: list[int]) -> bool:
        """Entrena un modelo TF-IDF/RandomForest para una categoría."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.ensemble import RandomForestClassifier

            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 3))
            X = vectorizer.fit_transform(training_texts)
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, labels)

            joblib.dump(model, MODELS_DIR / f"{category}_model.joblib")
            joblib.dump(vectorizer, MODELS_DIR / f"{category}_vectorizer.joblib")

            self.models[category] = model
            self.vectorizers[category] = vectorizer
            logger.info("ML[keyword]: modelo entrenado y guardado para %s", category)
            return True
        except Exception as exc:
            logger.error("ML[keyword]: error entrenando %s: %s", category, exc)
            return False


# Alias retrocompatible: el código y los tests existentes usan MLAnalyzer.
MLAnalyzer = KeywordMLAnalyzer


# ─────────────────────────────────────────────────────────────────────────────
# Analizador transformer multilingüe (sentence-transformers + cosine)
# ─────────────────────────────────────────────────────────────────────────────
class TransformerMLAnalyzer:
    """
    Analizador semántico multilingüe basado en sentence-transformers.
    Compara el embedding del texto contra anchor sentences por categoría
    en es/en/ar/ru/zh y usa la similitud coseno máxima como score.
    """

    def __init__(self) -> None:
        # Trigger lazy load para detectar fallo temprano
        model, anchors = _get_transformer()
        self.available = model is not None and anchors is not None

    def analyze_text(self, text: str, language: str = "es") -> dict:
        if not text:
            return {}
        model, anchor_emb = _get_transformer()
        if model is None or anchor_emb is None:
            return {}

        try:
            emb = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
        except Exception as exc:
            logger.warning("ML[transformer]: encoding falló: %s", exc)
            return {}

        results: dict[str, dict] = {}
        for category, anchors in anchor_emb.items():
            # cosine = dot(a, b) ya que ambos vectores están normalizados
            sims = anchors @ emb
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim >= TRANSFORMER_THRESHOLD:
                weight = INDICATOR_WEIGHTS.get(category, 0.1)
                # Mapeo: similitud [threshold .. 1.0] -> score [weight*0.5 .. 1.0]
                normalized = (best_sim - TRANSFORMER_THRESHOLD) / max(1e-6, 1.0 - TRANSFORMER_THRESHOLD)
                score = min(1.0, weight + (1.0 - weight) * normalized)
                anchor_text = ANCHOR_SENTENCES[category][best_idx][:120]
                results[category] = {
                    "score": score,
                    "matches": [f"TR:{category}:{best_sim:.3f}:{anchor_text}"],
                }
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Instancias globales: keyword siempre, transformer si carga
# ─────────────────────────────────────────────────────────────────────────────
keyword_analyzer = KeywordMLAnalyzer()
transformer_analyzer = TransformerMLAnalyzer()

# Compatibilidad con código previo
ml_analyzer = keyword_analyzer


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline público
# ─────────────────────────────────────────────────────────────────────────────
def _merge_analyses(primary: dict, secondary: dict) -> dict:
    """Combina dos resultados {cat: {score, matches}} tomando max score y unión de matches."""
    merged: dict[str, dict] = {}
    for category in set(primary) | set(secondary):
        p = primary.get(category)
        s = secondary.get(category)
        if p and s:
            merged[category] = {
                "score": max(p["score"], s["score"]),
                "matches": (p["matches"] + s["matches"])[:6],
            }
        elif p:
            merged[category] = {"score": p["score"], "matches": list(p["matches"])[:6]}
        else:
            merged[category] = {"score": s["score"], "matches": list(s["matches"])[:6]}
    return merged


def analyze_post_ml(post: SocialPost) -> ThreatAssessment:
    """
    Pipeline principal: transformer (si disponible) + keywords (refuerzo).
    Devuelve un ThreatAssessment compatible con el código existente.
    """
    logger.info(
        "ML_ANALYSIS_AGENT: analizando post %s de %s (lang=%s)",
        post.id, post.platform, post.language,
    )

    text = post.content or ""
    language = post.language or "es"

    keyword_results = keyword_analyzer.analyze_text(text, language=language)

    if not DISABLE_TRANSFORMERS and transformer_analyzer.available:
        try:
            transformer_results = transformer_analyzer.analyze_text(text, language=language)
            logger.debug(
                "ML_ANALYSIS_AGENT: backend=transformer+keyword cats_tr=%d cats_kw=%d",
                len(transformer_results), len(keyword_results),
            )
            ml_results = _merge_analyses(transformer_results, keyword_results)
        except Exception as exc:
            logger.warning("ML_ANALYSIS_AGENT: transformer falló (%s), usando keywords", exc)
            ml_results = keyword_results
    else:
        if DISABLE_TRANSFORMERS:
            logger.debug("ML_ANALYSIS_AGENT: backend=keyword-only (disabled by env)")
        else:
            logger.debug("ML_ANALYSIS_AGENT: backend=keyword-only (transformer no disponible)")
        ml_results = keyword_results

    found_indicators: list[ThreatIndicator] = []
    accumulated_score = 0.0

    for category, result in ml_results.items():
        if result["score"] <= 0:
            continue
        confidence = min(1.0, float(result["score"]))
        accumulated_score = max(accumulated_score, INDICATOR_WEIGHTS.get(category, 0.05) * confidence)

        for match in result["matches"][:3]:
            try:
                indicator = ThreatIndicator(
                    type=IndicatorType(category),
                    value=match[:100],
                    explanation=_build_explanation_ml(category, match, confidence),
                    confidence=confidence,
                )
                found_indicators.append(indicator)
            except ValueError:
                logger.debug("ML_ANALYSIS_AGENT: categoría %s no es IndicatorType válido", category)

    # Bonus por múltiples categorías
    categories_hit = len({ind.type for ind in found_indicators})
    if categories_hit >= 2:
        accumulated_score = min(1.0, accumulated_score * 1.2)
    if categories_hit >= 3:
        accumulated_score = min(1.0, accumulated_score * 1.3)

    # Bonus por entidades (NER real)
    entities = _extract_entities(text)
    if entities.get("weapons") or entities.get("locations"):
        accumulated_score = min(1.0, accumulated_score * 1.1)
    if entities.get("persons"):
        accumulated_score = min(1.0, accumulated_score * 1.05)

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
        model_version="2.1.0-ML-MULTILINGUAL",
    )

    logger.info(
        "ML_ANALYSIS_AGENT: post %s → score=%.4f nivel=%s indicadores=%d entidades=%s",
        post.id, risk_score, alert_level, len(found_indicators),
        {k: len(v) for k, v in entities.items()},
    )
    return assessment


def _score_to_level(score: float) -> AlertLevel:
    if score >= 0.75:
        return AlertLevel.ROJO
    if score >= 0.50:
        return AlertLevel.NARANJA
    if score >= 0.30:
        return AlertLevel.AMARILLO
    return AlertLevel.VERDE


def _build_explanation_ml(category: str, match: str, confidence: float) -> str:
    explanations = {
        "llamada_violencia": f"Llamada a violencia detectada (conf={confidence:.2f}): '{match}'",
        "coordinacion_ataque": f"Posible coordinación detectada (conf={confidence:.2f}): '{match}'",
        "glorificacion_terrorismo": f"Glorificación detectada (conf={confidence:.2f}): '{match}'",
        "reclutamiento": f"Reclutamiento detectado (conf={confidence:.2f}): '{match}'",
        "amenaza_directa": f"Amenaza directa detectada (conf={confidence:.2f}): '{match}'",
    }
    return explanations.get(category, f"Indicador '{category}': '{match}'")


# ─────────────────────────────────────────────────────────────────────────────
# NER (spaCy multilingüe + fallback regex/keywords)
# ─────────────────────────────────────────────────────────────────────────────
WEAPON_KEYWORDS = [
    "arma", "armas", "pistola", "rifle", "fusil", "bomba", "explosivo", "explosivos",
    "cuchillo", "granada", "tnt", "ied", "c4", "munición", "balas", "detonador",
    "gun", "rifle", "bomb", "knife", "weapon", "explosive", "grenade", "ammunition",
    "оружие", "пистолет", "винтовка", "бомба", "взрывчатка", "нож", "граната",
    "سلاح", "بندقية", "قنبلة", "متفجرات", "سكين",
    "武器", "枪", "炸弹", "爆炸物", "刀",
]

DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\b\d{1,2}-\d{1,2}-\d{2,4}\b"),
]


def _extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extrae entidades nombradas usando spaCy multilingüe.
    Si spaCy no está disponible, usa fallback simple.
    Devuelve: {persons, locations, organizations, weapons, dates}
    """
    out: dict[str, list[str]] = {
        "persons": [],
        "locations": [],
        "organizations": [],
        "weapons": [],
        "dates": [],
    }
    if not text:
        return out

    text_lower = text.lower()

    # 1. Armas siempre por keywords (xx_ent_wiki_sm no las etiqueta)
    for kw in WEAPON_KEYWORDS:
        if kw in text_lower and kw not in out["weapons"]:
            out["weapons"].append(kw)

    # 2. Fechas por regex (siempre disponible)
    seen_dates: set[str] = set()
    for pattern in DATE_PATTERNS:
        for m in pattern.findall(text):
            if m not in seen_dates:
                seen_dates.add(m)
                out["dates"].append(m)

    # 3. Persons / Locations / Orgs vía spaCy (lazy load)
    nlp = _get_ner_pipeline()
    if nlp is not None:
        try:
            doc = nlp(text)
            for ent in doc.ents:
                label = ent.label_.upper()
                value = ent.text.strip()
                if not value or len(value) > 100:
                    continue
                if label == "PER" and value not in out["persons"]:
                    out["persons"].append(value)
                elif label in ("LOC", "GPE") and value not in out["locations"]:
                    out["locations"].append(value)
                elif label == "ORG" and value not in out["organizations"]:
                    out["organizations"].append(value)
        except Exception as exc:
            logger.debug("ML[ner]: spaCy falló en este texto: %s", exc)
    else:
        # Fallback de ubicaciones sin spaCy
        location_keywords = [
            "calle", "avenida", "plaza", "edificio", "puente",
            "street", "avenue", "square", "building", "bridge",
            "улица", "площадь", "здание", "мост",
            "شارع", "ساحة", "مبنى", "جسر",
            "街", "广场", "大楼", "桥",
        ]
        for kw in location_keywords:
            if kw in text_lower and kw not in out["locations"]:
                out["locations"].append(kw)

    return out
