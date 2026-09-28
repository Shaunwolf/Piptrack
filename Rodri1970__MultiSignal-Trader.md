# Rodri1970/MultiSignal-Trader (space)

```json
{
  "kind": "space",
  "id": "Rodri1970/MultiSignal-Trader",
  "url": "https://huggingface.co/spaces/Rodri1970/MultiSignal-Trader",
  "meta": {
    "tags": [
      "gradio",
      "region:us"
    ],
    "likes": 0,
    "sdk": "gradio",
    "cardData": {
      "title": "MultiSignal Trader",
      "emoji": "\ud83d\udd25",
      "colorFrom": "pink",
      "colorTo": "purple",
      "sdk": "gradio",
      "sdk_version": "6.26.0",
      "python_version": "3.13",
      "app_file": "app.py",
      "pinned": false,
      "license": "mit",
      "short_description": "Toma decisiones de Inversion "
    },
    "lastModified": "2026-09-08T01:17:16.000Z",
    "gated": false,
    "private": false
  },
  "files": [
    {
      "path": ".gitattributes",
      "size": 1519,
      "type": "file"
    },
    {
      "path": "README.md",
      "size": 326,
      "type": "file"
    },
    {
      "path": "app.py",
      "size": 6599,
      "type": "file"
    },
    {
      "path": "requirements.txt",
      "size": 70,
      "type": "file"
    }
  ]
}
```

## README

---
title: MultiSignal Trader
emoji: 🔥
colorFrom: pink
colorTo: purple
sdk: gradio
sdk_version: 6.26.0
python_version: '3.13'
app_file: app.py
pinned: false
license: mit
short_description: 'Toma decisiones de Inversion '
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


## app.py

```
import gradio as gr
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from transformers import pipeline

# 1. Cargar el modelo NLP de finanzas para análisis de noticias
# Usamos ProsusAI/finbert (modelo ligero entrenado específicamente para textos financieros)
sentiment_pipeline = pipeline(
    "text-classification", 
    model="ProsusAI/finbert"
)

def analizar_noticias(ticker):
    """Extrae titulares recientes de Yahoo Finance de forma robusta"""
    try:
        t = yf.Ticker(ticker)
        news_data = t.news
        
        if not news_data:
            return "No se encontraron noticias recientes en este momento.", 0.0

        titulares = []
        for item in news_data[:5]:
            # Manejar la nueva estructura multinivel de noticias de yfinance
            title = item.get('title')
            if not title and isinstance(item.get('content'), dict):
                title = item.get('content', {}).get('title')
            
            if title:
                titulares.append(title)

        if not titulares:
            return "No se pudieron procesar los titulares.", 0.0

        # Analizar con FinBERT
        resultados = sentiment_pipeline(titulares)
        
        score_total = 0
        resumen_titulares = []
        
        for idx, res in enumerate(resultados):
            label = res['label']
            score = res['score']
            titular = titulares[idx]
            
            if label == 'positive':
                score_total += score
                emoji = "🟢"
            elif label == 'negative':
                score_total -= score
                emoji = "🔴"
            else:
                emoji = "⚪"
                
            resumen_titulares.append(f"{emoji} {titular}")

        puntuacion_sentimiento = score_total / len(resultados)
        texto_noticias = "\n".join(resumen_titulares)
        
        return texto_noticias, puntuacion_sentimiento

    except Exception as e:
        return f"Error leyendo noticias: {str(e)}", 0.0

def calcular_indicadores(df):
    """Calcula indicadores técnicos sobre el DataFrame"""
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Volatilidad'] = (df['High'] - df['Low']) / df['Close']
    df['Retorno'] = df['Close'].pct_change()
    
    # Target: Predecir si el precio sube al día siguiente (1 día vista)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    return df.dropna()


def entrenar_y_predecir(ticker):
    ticker = ticker.strip().upper()
    if not ticker:
        return "Por favor ingresa un Ticker válido.", None

    try:
        # A. Análisis de Noticias (LLM / NLP)
        texto_noticias, score_noticias = analizar_noticias(ticker)

        # B. Análisis Cuantitativo (Random Forest)
        datos = yf.download(ticker, period="2y", progress=False)

        if datos.empty or len(datos) < 100:
            return f"No se encontraron suficientes datos para el ticker: {ticker}", None

        if isinstance(datos.columns, pd.MultiIndex):
            datos.columns = datos.columns.get_level_values(0)

        df = calcular_indicadores(datos.copy())

        features = ['Close', 'SMA_10', 'SMA_50', 'RSI', 'Volatilidad', 'Retorno']
        X = df[features]
        y = df['Target']

        # División temporal
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        model = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X_train, y_train)

        accuracy = model.score(X_test, y_test)

        # Predicción técnica
        ultimos_datos = X.iloc[[-1]]
        prediccion_tecnica = model.predict(ultimos_datos)[0]
        
        # C. Combinación de Señales (Técnica + Sentimiento)
        if score_noticias > 0.2 and prediccion_tecnica == 1:
            decision_final = "🟢 COMPRA FUERTE (Técnica y Noticias Positivas)"
        elif score_noticias < -0.2 and prediccion_tecnica == 0:
            decision_final = "🔴 VENTA FUERTE (Técnica y Noticias Negativas)"
        elif prediccion_tecnica == 1:
            decision_final = "🟡 COMPRA MODERADA (Técnica Alcista / Noticias Neutras)"
        else:
            decision_final = "⚪ MANTENER / VENTA MODERADA"

        ultimo_precio = float(df['Close'].iloc[-1])
        ultima_fecha = str(df.index[-1].strftime('%Y-%m-%d'))

        # D. Reporte Final
        reporte = f"""
        ### 📊 Análisis Combinado para {ticker}
        * **Decisión del Agente:** {decision_final}
        * **Puntuación de Sentimiento (Noticias):** {score_noticias:.2f} (-1.0 a 1.0)
        * **Precisión del Modelo Técnico:** {accuracy * 100:.1f}%
        * **Último Precio:** ${ultimo_precio:.2f} ({ultima_fecha})

        ---
        #### 📰 Titulares Analizados por la IA:
        {texto_noticias}
        """

        df_grafica = datos[['Close']].tail(120).reset_index()
        df_grafica.columns = ['Fecha', 'Precio']

        return reporte, df_grafica

    except Exception as e:
        return f"Error procesando la solicitud: {str(e)}", None

# --- Interfaz de Gradio ---
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 Agente Cuantitativo de Inversión (Técnico + Noticias)")
    gr.Markdown("Combina un modelo Random Forest con un modelo NLP FinBERT para analizar tendencias y noticias en tiempo real.")

    with gr.Row():
        with gr.Column(scale=1):
            ticker_input = gr.Textbox(label="Ticker de la acción", value="AAPL", placeholder="Ej: AAPL, MSFT, TSLA")
            btn_predict = gr.Button("Analizar Mercado", variant="primary")

        with gr.Column(scale=2):
            salida_resultado = gr.Markdown(label="Resultados")
            salida_grafica = gr.LinePlot(
                x="Fecha", 
                y="Precio", 
                title="Precio de cierre (Últimos 120 días)",
                tooltip=["Fecha", "Precio"],
                height=300
            )

    btn_predict.click(
        fn=entrenar_y_predecir, 
        inputs=[ticker_input], 
        outputs=[salida_resultado, salida_grafica]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())

```

## requirements.txt

```
gradio
yfinance
pandas
numpy
scikit-learn
transformers
torch
requests

```
