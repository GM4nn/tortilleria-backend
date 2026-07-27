# other libs
import json

# sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session

# app
from app.core.config import settings


MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1500

DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER",
    "CREATE", "TRUNCATE", "EXEC", "EXECUTE", ";--", "/*", "*/",
]

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

    def _client(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Falta configurar ANTHROPIC_API_KEY")
        import anthropic
        return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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
        raw = msg.content[0].text.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No se pudo generar la consulta")
        return json.loads(raw[start:end + 1])["query"]

    def _run_sql(self, query: str) -> list[dict]:
        upper = query.upper()
        if not upper.lstrip().startswith("SELECT"):
            raise ValueError("Solo se permiten consultas de lectura")
        if any(word in upper for word in DANGEROUS_KEYWORDS):
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
        return msg.content[0].text.strip()

    def ask(self, question: str) -> str:
        client = self._client()
        query = self._generate_sql(client, question)
        data = self._run_sql(query)
        return self._phrase_answer(client, question, data)
