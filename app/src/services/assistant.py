# other libs
import json
import re

# sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session

# app
from app.core.config import settings
from app.src.models import IAConfig


MODEL = "claude-sonnet-5"
MAX_TOKENS = 1500

# Palabras que modifican datos; se buscan como palabra completa para no chocar
# con columnas como "created_at" (que contiene "CREATE").
WRITE_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE",
    "EXEC", "EXECUTE", "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM",
    "GRANT", "REINDEX",
]
WRITE_KEYWORDS_RE = re.compile(r"\b(" + "|".join(WRITE_KEYWORDS) + r")\b")

SCHEMA_HINT = """
Base de datos SQLite de una tortillería. Tablas y columnas:
- products(id, icon, name, price, active)
- customers(id, customer_name, customer_category, customer_phone, created_at, active)
- sales(id, date, total, customer_id)
- sales_detail(id, sale_id, product_id, quantity, unit_price, subtotal)
- orders(id, date, total, customer_id, status, completed_at, amount_paid, default_dealer)
  status: 'pendiente' | 'completado' | 'cancelado'
- order_details(id, order_id, product_id, quantity, unit_price, subtotal)
- order_refunds(id, order_id, product_id, quantity, comments, created_at)
- dealers(id, username, pin, name, active)  -> repartidores; orders.default_dealer = dealers.username
- suppliers(id, supplier_name, product_type, city, active)
- supplies(id, supply_name, supplier_id, unit)
- supply_purchases(id, supply_id, supplier_id, purchase_date, quantity, unit_price, total_price, remaining)
- cash_cuts(id, closed_at, expected_total, declared_total, difference)

Reglas: SOLO genera SQL SELECT. Usa JOINs cuando necesites datos de otra tabla.
Fechas SQLite: strftime('%Y-%m', date) = strftime('%Y-%m','now') para el mes actual.
""".strip()


class AssistantService:

    def __init__(self, db_session: Session) -> None:
        self._db_session: Session = db_session

    def _api_key(self) -> str | None:
        # Prioriza la key guardada en la DB (ia_config); si no, la del entorno
        row = self._db_session.query(IAConfig).order_by(IAConfig.id.desc()).first()
        if row and row.api_key:
            return row.api_key
        return settings.ANTHROPIC_API_KEY

    def _client(self):
        api_key = self._api_key()
        if not api_key:
            raise ValueError("Falta configurar la API key de Anthropic")
        import anthropic
        return anthropic.Anthropic(api_key=api_key)

    @staticmethod
    def _extract_text(msg) -> str:
        # La respuesta puede traer bloques de "thinking" antes del texto; tomamos
        # solo los bloques de texto (no asumimos que content[0] sea el texto).
        texts = [
            block.text
            for block in msg.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        if not texts:  # respaldo: cualquier bloque con texto
            texts = [getattr(b, "text", "") or "" for b in msg.content]
        return "".join(texts).strip()

    def _generate_sql(self, client, question: str) -> str:
        prompt = (
            f"{SCHEMA_HINT}\n\n"
            f"Pregunta del usuario: {question}\n\n"
            "Responde SOLO con un JSON: {\"query\": \"SELECT ...\"}"
        )
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = self._extract_text(msg)
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No se pudo generar la consulta")
        return json.loads(raw[start:end + 1])["query"]

    def _run_sql(self, query: str) -> list[dict]:
        stripped = query.strip()
        upper = stripped.upper()
        # Solo lectura: SELECT o CTE (WITH ... SELECT)
        if not (upper.startswith("SELECT") or upper.startswith("WITH")):
            raise ValueError("Solo se permiten consultas de lectura")
        if WRITE_KEYWORDS_RE.search(upper):
            raise ValueError("Consulta no permitida")
        if any(token in stripped for token in (";--", "/*", "*/")):
            raise ValueError("Consulta no permitida")

        rows = self._db_session.execute(text(query)).mappings().all()
        return [dict(r) for r in rows]

    def _phrase_answer(self, client, question: str, data: list[dict]) -> str:
        prompt = (
            "Eres un asistente de negocios de una tortillería. Responde en español, "
            "breve y directo, con formato de moneda MXN cuando aplique. "
            "Si los datos están vacíos, dilo claramente.\n\n"
            f"Pregunta: {question}\n"
            f"Datos: {json.dumps(data, default=str, ensure_ascii=False)}"
        )
        msg = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._extract_text(msg)

    def ask(self, question: str) -> str:
        client = self._client()
        query = self._generate_sql(client, question)
        data = self._run_sql(query)
        return self._phrase_answer(client, question, data)
