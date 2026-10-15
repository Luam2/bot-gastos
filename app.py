import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

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


st.title("💸 Bot de gastos")

with st.form("nuevo_gasto", clear_on_submit=True):
    monto = st.number_input("Monto (S/)", min_value=0.0, step=0.5)
    descripcion = st.text_input("Descripción (ej: almuerzo)")
    enviado = st.form_submit_button("Guardar")

if enviado:
    if monto > 0 and descripcion.strip():
        categoria = categorizar(descripcion)
        con = sqlite3.connect("gastos.db")
        con.execute(
            "INSERT INTO gastos (fecha, monto, descripcion, categoria) VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), monto, descripcion.strip(), categoria),
        )
        con.commit()
        con.close()
        st.success(f"Guardado: S/ {monto:.2f} - {descripcion} [{categoria}]")
    else:
        st.warning("Escribe un monto mayor a 0 y una descripción.")

con = sqlite3.connect("gastos.db")
df = pd.read_sql("SELECT * FROM gastos ORDER BY fecha DESC, id DESC", con)
con.close()

inicio_mes = date.today().replace(day=1).isoformat()
df_mes = df[df["fecha"] >= inicio_mes]

st.metric("Total del mes", f"S/ {df_mes['monto'].sum():.2f}")

if df_mes.empty:
    st.info("Aún no hay gastos este mes.")
else:
    st.subheader("Gasto por categoría (mes)")
    st.bar_chart(df_mes.groupby("categoria")["monto"].sum())

st.subheader("Todos los gastos")
st.dataframe(df, use_container_width=True)