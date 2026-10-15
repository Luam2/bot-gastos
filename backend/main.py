import sqlite3
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB = "gastos.db"

CATEGORIAS = {
    "comida": ["almuerzo", "cena", "desayuno", "cafe", "café", "menu", "menú", "pizza", "snack", "comida"],
    "transporte": ["pasaje", "taxi", "uber", "bus", "metro", "gasolina", "combi"],
    "ocio": ["cine", "juego", "salida", "netflix", "spotify", "fiesta"],
    "estudios": ["libro", "copias", "curso", "impresion", "impresión"],
    "salud": ["farmacia", "medicina", "doctor"],
}


def categorizar(descripcion):
    texto = descripcion.lower()
    for categoria, palabras in CATEGORIAS.items():
        for palabra in palabras:
            if palabra in texto:
                return categoria
    return "otros"


def get_con():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


con = get_con()
con.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    monto REAL NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT
)
""")
con.commit()
con.close()


class GastoIn(BaseModel):
    monto: float = Field(gt=0)
    descripcion: str = Field(min_length=1)


app = FastAPI(title="API de gastos")


@app.post("/gastos", status_code=201)
def crear_gasto(gasto: GastoIn):
    fecha = date.today().isoformat()
    descripcion = gasto.descripcion.strip()
    categoria = categorizar(descripcion)

    con = get_con()
    cur = con.execute(
        "INSERT INTO gastos (fecha, monto, descripcion, categoria) VALUES (?, ?, ?, ?)",
        (fecha, gasto.monto, descripcion, categoria),
    )
    con.commit()
    nuevo_id = cur.lastrowid
    con.close()

    return {
        "id": nuevo_id,
        "fecha": fecha,
        "monto": gasto.monto,
        "descripcion": descripcion,
        "categoria": categoria,
    }


@app.get("/gastos")
def listar_gastos():
    con = get_con()
    filas = con.execute(
        "SELECT * FROM gastos ORDER BY fecha DESC, id DESC"
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


@app.delete("/gastos/{gasto_id}")
def borrar_gasto(gasto_id: int):
    con = get_con()
    cur = con.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    con.commit()
    borrados = cur.rowcount
    con.close()

    if borrados == 0:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return {"mensaje": f"Gasto {gasto_id} eliminado"}