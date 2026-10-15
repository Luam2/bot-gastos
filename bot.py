import sqlite3
from datetime import date, timedelta

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


conexion = sqlite3.connect("gastos.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    monto REAL NOT NULL,
    descripcion TEXT NOT NULL
)
""")

try:
    cursor.execute("ALTER TABLE gastos ADD COLUMN categoria TEXT")
except sqlite3.OperationalError:
    pass  # la columna ya existe

cursor.execute("SELECT id, descripcion FROM gastos WHERE categoria IS NULL")
for id_gasto, desc in cursor.fetchall():
    cursor.execute(
        "UPDATE gastos SET categoria = ? WHERE id = ?",
        (categorizar(desc), id_gasto),
    )
conexion.commit()


def resumen(desde, titulo):
    cursor.execute(
        "SELECT fecha, monto, descripcion, categoria FROM gastos WHERE fecha >= ? ORDER BY fecha",
        (desde,),
    )
    filas = cursor.fetchall()

    if not filas:
        print(f"{titulo}: sin gastos.")
        return

    total = 0
    print(f"--- {titulo} ---")
    for fecha, monto, descripcion, categoria in filas:
        print(f"{fecha}  S/ {monto:.2f}  {descripcion}  [{categoria}]")
        total += monto
    print(f"TOTAL: S/ {total:.2f}")


def por_categoria(desde, titulo):
    cursor.execute(
        "SELECT categoria, SUM(monto) FROM gastos WHERE fecha >= ? GROUP BY categoria ORDER BY SUM(monto) DESC",
        (desde,),
    )
    filas = cursor.fetchall()

    if not filas:
        print(f"{titulo}: sin gastos.")
        return

    print(f"--- {titulo} ---")
    for categoria, subtotal in filas:
        print(f"{categoria}: S/ {subtotal:.2f}")


print("Bot de gastos. Escribe un gasto así: 18 almuerzo")
print("Comandos: hoy, semana, mes, categorias, salir")

while True:
    texto = input("> ").strip()

    if texto == "salir":
        print("Chau")
        break

    if texto == "hoy":
        resumen(date.today().isoformat(), "Gastos de hoy")
        continue

    if texto == "semana":
        desde = (date.today() - timedelta(days=6)).isoformat()
        resumen(desde, "Últimos 7 días")
        continue

    if texto == "mes":
        desde = date.today().replace(day=1).isoformat()
        resumen(desde, "Gastos del mes")
        continue

    if texto == "categorias":
        desde = date.today().replace(day=1).isoformat()
        por_categoria(desde, "Gasto por categoría (mes)")
        continue

    partes = texto.split(" ", 1)

    if len(partes) < 2:
        print("Formato: monto descripcion (ejemplo: 18 almuerzo)")
        continue

    try:
        monto = float(partes[0])
    except ValueError:
        print("El monto debe ser un número (ejemplo: 18 almuerzo)")
        continue

    descripcion = partes[1]
    fecha = date.today().isoformat()
    categoria = categorizar(descripcion)

    cursor.execute(
        "INSERT INTO gastos (fecha, monto, descripcion, categoria) VALUES (?, ?, ?, ?)",
        (fecha, monto, descripcion, categoria),
    )
    conexion.commit()
    print(f"Guardado: S/ {monto:.2f} - {descripcion} [{categoria}]")

conexion.close()