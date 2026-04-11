# Fase 3: Ingeniería de Prompts y Evaluación

## 1. Objetivo

El objetivo de esta fase es demostrar cómo el uso de prompts y ejemplos (few-shot prompting) impacta la calidad de las respuestas generadas por el modelo de lenguaje, en el contexto del servicio de atención al cliente de EcoMarket.

Para ello se implementó un sistema que combina:

* un modelo open-source (Gemma 2B),
* datos estructurados,
* documentos de política,
* y una biblioteca de ejemplos de conversaciones.

---

## 2. Configuración del entorno

### 2.1 Requisitos

* Python 3.11
* uv (gestor de entornos)
* Ollama instalado
* Streamlit

---

### 2.2 Instalación del entorno

Desde la raíz del proyecto:

```bash
uv sync
```

---

### 2.3 Instalación de Ollama

En Windows:

```bash
winget install Ollama.Ollama
```

Verificar instalación:

```bash
ollama --version
```

---

### 2.4 Descargar el modelo

```bash
ollama pull gemma2:2b
```

---

### 2.5 Levantar el servidor de Ollama

```bash
ollama serve
```

Nota:
Si aparece un error de "address already in use", significa que el servidor ya está corriendo.

---

### 2.6 Ejecutar la aplicación

En otra terminal:

```bash
uv run streamlit run app.py
```

La aplicación estará disponible en:

```
http://localhost:8501
```

---

## 3. Arquitectura de prompts

El sistema utiliza distintos tipos de prompts dependiendo de la intención detectada:

* Estado del pedido → `build_order_prompt`
* Devoluciones → `build_return_prompt`
* Escalamiento humano → `build_human_prompt`
* General → `build_general_prompt`

Cada prompt contiene:

* instrucciones claras,
* contexto estructurado,
* ejemplos de conversaciones (few-shot).

---

## 4. Biblioteca de ejemplos (Few-shot)

Se creó un archivo:

```
data/support_examples.json
```

Este archivo contiene ejemplos de interacción cliente-agente para distintos escenarios:

* pedido retrasado
* pedido entregado
* pedido en tránsito
* devolución permitida
* devolución no permitida
* producto dañado
* quejas y escalamiento

Estos ejemplos se incorporan dinámicamente al prompt según la intención detectada.

---

## 5. Comparación: sin ejemplos vs con ejemplos

### 5.1 Prompt básico (sin ejemplos)

Ejemplo de prompt:

```text
You are a customer support assistant.
Answer the user's question using the order data.
```

**Resultado esperado:**

* Respuestas más simples
* Menor empatía
* Menor consistencia
* Menor claridad

---

### 5.2 Prompt mejorado (con ejemplos)

Ejemplo:

* incluye ejemplos reales de soporte
* define tono (empático, claro)
* restringe al modelo (no inventar datos)

**Resultado observado:**

* Mayor naturalidad en el lenguaje
* Respuestas más empáticas
* Uso consistente de estructura
* Mejor alineación con el negocio

---

## 6. Casos de prueba

### Caso 1: Pedido retrasado

**Input:**

```text
Where is my order ECO1003?
```

**Output esperado:**

* Respuesta empática
* Explicación del estado
* Fecha estimada
* Link de tracking
* Información estructurada adicional

---

### Caso 2: Política de devolución

**Input:**

```text
How can I return a product?
```

**Output esperado:**

* Explicación clara de la política
* Lenguaje natural
* Solicitud de información adicional

---

### Caso 3: Producto no retornable

**Input:**

```text
I want to return an opened hygiene product.
```

**Output esperado:**

* Negativa clara
* Explicación respetuosa
* Alternativa (si aplica)

---

### Caso 4: Escalamiento a humano

**Input:**

```text
I am very upset and want to complain
```

**Output esperado:**

* Respuesta empática
* Escalamiento a agente humano

---

## 7. Evaluación del modelo (Gemma 2B)

### Fortalezas observadas

* Buen desempeño en generación de lenguaje natural
* Capacidad de seguir instrucciones del prompt
* Mejora significativa al usar ejemplos
* Funciona adecuadamente en entorno local

---

### Limitaciones observadas

* Tiempo de respuesta elevado (dependiente del hardware)
* Menor capacidad que modelos más grandes
* Sensible al tamaño del prompt

---

## 8. Decisiones de diseño clave

### Separación de responsabilidades

* Datos estructurados → verdad del negocio
* LLM → generación del lenguaje

Esto evita alucinaciones en información crítica.

---

### Uso de few-shot prompting

Se decidió usar ejemplos en lugar de fine-tuning porque:

* es más simple
* es más flexible
* permite iteración rápida
* no requiere reentrenamiento

---

### Uso de modelo open-source

Se utilizó Gemma 2B porque:

* no requiere costos de API
* permite ejecución local
* es suficiente para un prototipo funcional

---

## 9. Conclusión

El uso de ingeniería de prompts, especialmente mediante few-shot prompting, mejora significativamente la calidad de las respuestas generadas por el modelo.

La solución demuestra que es posible construir un sistema de atención al cliente funcional combinando:

* IA generativa,
* datos estructurados,
* reglas de negocio,
* y ejemplos bien diseñados.

Aunque el modelo utilizado es relativamente pequeño, el diseño del prompt permite obtener resultados adecuados para el contexto del problema.

En conclusión, el éxito del sistema no depende únicamente del modelo, sino del diseño del sistema y de los prompts utilizados.
