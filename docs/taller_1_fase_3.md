# Fase 3: Ingeniería de Prompts

## 1. Objetivo

El objetivo de esta fase es demostrar cómo el diseño del prompt determina la calidad
de las respuestas generadas por el modelo. Se implementaron dos ejercicios centrales:

- Consulta de estado de pedido
- Gestión de devoluciones 
En cada caso comparamos un prompt básico contra un prompt mejorado con few-shot prompting, contextoestructurado y restricciones explícitas de comportamiento.

El sistema combina Gemma 2B (ejecutado localmente con Ollama), datos estructurados
de pedidos, un documento de política de devoluciones y una biblioteca de ejemplos
de conversación. La orquestación se realiza con LangChain y la interfaz de usuario
con Streamlit.

---

## 2. Configuración del entorno

### 2.1 Requisitos

- Python 3.11
- `uv` como gestor de entornos virtuales
- Ollama instalado y en ejecución
- Streamlit

### 2.2 Instalación y ejecución

```bash
# Instalar dependencias
uv sync

# Instalar Ollama (Windows)
winget install Ollama.Ollama

# o en MAC
brew install ollama

# Verificar instalación
ollama --version

# Descargar el modelo
ollama pull gemma2:2b

# Levantar el servidor de Ollama
ollama serve

# En otra terminal, ejecutar la aplicación
uv run streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`.

> Si `ollama serve` retorna "address already in use", el servidor ya está activo.

---

## 3. Arquitectura de prompts

El sistema construye el prompt de forma dinámica según la intención detectada por
el router. Cada intención tiene su propio constructor:

| Intención detectada | Constructor de prompt |
|---|---|
| Consulta de pedido | `build_order_prompt` |
| Devolución de producto | `build_return_prompt` |
| Escalamiento a humano | `build_human_prompt` |
| Soporte general | `build_general_prompt` |

Todos los constructores siguen la misma estructura base:

1. **Rol e instrucciones**: define quién es el modelo y cómo debe comportarse.
2. **Contexto estructurado**: datos del pedido o fragmento de política relevante.
3. **Restricciones**: qué no debe hacer el modelo (inventar datos, salirse del dominio).
4. **Ejemplos few-shot**: conversaciones modelo que definen tono y estructura.
5. **Consulta del cliente**: el mensaje real que debe responderse.

---

## 4. Ejercicio 1 — Prompt de consulta de estado de pedido

### 4.1 Fuente de datos: pedidos de ejemplo

El sistema utiliza un archivo estructurado (`data/orders.json`) como fuente de
verdad operativa. El modelo nunca infiere el estado de un pedido: lo recibe ya
recuperado e inyectado en el prompt.

```json
[
  {
    "tracking_number": "ECO1001", 
    "status": "In transit",
    "estimated_delivery": "2026-04-15",
    "tracking_url": "https://tracking.ecomarket.com/ECO1001"
  },
  {
    "tracking_number": "ECO1002",
    "status": "Delivered",
    "estimated_delivery": "2026-04-10",
    "tracking_url": "https://tracking.ecomarket.com/ECO1002"
  }
]
```

El archivo completo contiene un mínimo de 10 pedidos cubriendo los estados:
`Delivered`, `In Transit`, `Delayed`, `Processing` y `Cancelled`.

---

### 4.2 Prompt básico (sin ejemplos)

```text
You are a customer support assistant.
Answer the user's question using the order data below.

Order data:
{order_data}

Customer question: {user_input}
```

**Limitaciones observadas:**
- Respuestas escuetas y poco naturales.
- Ausencia de empatía ante pedidos retrasados.
- Sin estructura consistente entre respuestas.
- El modelo puede completar con datos no proporcionados.

---

### 4.3 Prompt mejorado (con few-shot prompting)

```text
You are a friendly and professional customer support agent for EcoMarket,
a sustainable products e-commerce company.

Your role is to help customers with their order inquiries clearly and empathetically.

Rules:
- Only use the order information provided below. Do not invent or assume any data.
- If the order is delayed, acknowledge it with empathy and provide a clear explanation.
- Always include the tracking link if available.
- If the order ID is not found in the data, inform the customer politely and suggest
  they double-check the number or contact support.
- Keep your response concise, warm and professional.

--- ORDER DATA ---
{order_data}
-----------------

--- EXAMPLES ---

Example 1 — Order in transit:
Customer: Where is my order ECO1002?
Agent: Hi Luis! Your Organic Cotton Tote Bag (ECO1002) is currently on its way
to you and is on schedule. You can expect it to arrive by June 5th, 2025.
Track your package in real time here: https://track.ecomarket.com/ECO1002
Let me know if there's anything else I can help you with! 🌿

Example 2 — Delayed order:
Customer: What happened to my order ECO1003?
Agent: Hi María, I'm sorry to hear your Solar Charger (ECO1003) hasn't arrived
yet. Your order has been delayed due to weather conditions, but we're doing
everything we can to get it to you as soon as possible. The new estimated
delivery date is June 8th, 2025.
You can track your package here: https://track.ecomarket.com/ECO1003
We truly appreciate your patience and are here if you need anything else. 🌱

Example 3 — Delivered order:
Customer: Has my order ECO1001 been delivered?
Agent: Great news, Ana! Your Bamboo Water Bottle (ECO1001) was successfully
delivered on June 1st, 2025 — right to your front door.
We hope you love your new sustainable product! If you have any questions or
concerns, don't hesitate to reach out. 😊

----------------

Customer question: {user_input}
Agent:
```

**Mejoras observadas frente al prompt básico:**
- Respuestas empáticas y diferenciadas según el estado del pedido.
- Estructura consistente: saludo, estado, fecha estimada, enlace de tracking.
- El modelo no inventa datos gracias a la restricción explícita.
- Tono alineado con la identidad de marca de EcoMarket.

---

## 5. Ejercicio 2 — Prompt de devolución de producto

### 5.1 Fuente de conocimiento: política de devoluciones

El módulo de devoluciones no consulta una base de datos operativa, sino un documento
de política (`data/return_policy.txt`) que se inyecta en el prompt. El modelo
parafrasea las reglas; no las genera.

```text
EcoMarket Return Policy

Return window: 30 days from delivery date.

Eligible for return:
- Unopened products in original packaging
- Defective or damaged products (photo evidence required)
- Incorrect items received

NOT eligible for return:
- Opened hygiene or personal care products
- Perishable or consumable goods
- Digital products or downloadable content
- Items marked as final sale

Return process:
1. Contact support with your order number and reason for return.
2. Our team will review the request within 24–48 hours.
3. If approved, you will receive a prepaid return label by email.
4. Refunds are processed within 5–7 business days after the item is received.

Note: EcoMarket reserves the right to deny returns that do not meet the above
conditions.
```

---

### 5.2 Prompt básico (sin ejemplos)

```text
You are a customer support assistant.
Help the customer with their return request using the policy below.

Return policy:
{return_policy}

Customer question: {user_input}
```

**Limitaciones observadas:**
- Incapacidad consistente para distinguir entre productos retornables y no retornables
  sin orientación explícita.
- Respuestas frías ante negativas de devolución.
- Sin guía de próximos pasos para el cliente.

---

### 5.3 Prompt mejorado (con few-shot prompting y lógica de distinción)

```text
You are a friendly and empathetic customer support agent for EcoMarket.

Your role is to assist customers with return requests based strictly on the
return policy provided below.

Rules:
- Determine clearly whether the product is eligible for return based on the policy.
- If the return IS eligible: explain the process step by step in a clear and
  encouraging tone.
- If the return is NOT eligible: communicate the decision respectfully and with
  empathy. Never be dismissive. Offer an alternative if possible (e.g., contacting
  support for special review, or product care advice).
- Do not invent exceptions or policies that are not in the document.
- Always acknowledge the customer's situation before delivering the decision.

--- RETURN POLICY ---
{return_policy}
---------------------

--- EXAMPLES ---

Example 1 — Eligible return (damaged product):
Customer: I received a defective reusable straw set. Can I return it?
Agent: I'm really sorry to hear that, and I completely understand how frustrating
that must be. Defective products are absolutely eligible for a return under our
policy.
Here's what to do next:
1. Contact our support team with your order number and a photo of the defect.
2. We'll review your request within 24–48 hours.
3. If approved, you'll receive a prepaid return label by email.
4. Your refund will be processed within 5–7 business days after we receive the item.
We'll make this right for you! 🌿

Example 2 — Non-eligible return (opened hygiene product):
Customer: I want to return an opened natural deodorant I bought last week.
Agent: Thank you for reaching out, and I understand your concern. Unfortunately,
opened hygiene and personal care products cannot be accepted for return under our
policy, as we're unable to resell them once opened — this also ensures the safety
and integrity of the products for all our customers.
If you're experiencing an issue with the product's quality or if it arrived damaged,
please let us know and we'll be happy to review your case individually.
Is there anything else I can help you with? 💚

Example 3 — Eligible return (wrong item received):
Customer: I ordered a bamboo toothbrush but received a different product entirely.
Agent: Oh no, I'm so sorry about that mix-up! Receiving the wrong item is definitely
something we want to resolve right away.
Here's how we'll fix this:
1. Please reach out with your order number so we can confirm the details.
2. We'll send you a prepaid label to return the incorrect item — no cost to you.
3. Once we receive it, we'll process your refund or send the correct product,
   whichever you prefer.
Again, we apologize for the inconvenience and appreciate your patience. 🌱

----------------

Customer question: {user_input}
Agent:
```

**Mejoras observadas frente al prompt básico:**
- El modelo distingue correctamente entre productos retornables y no retornables.
- Las negativas se comunican con empatía y sin dejar al cliente sin opciones.
- Las respuestas afirmativas incluyen los pasos del proceso de forma ordenada.
- El tono es consistente con la identidad de marca en todos los escenarios.

---

## 6. Impacto del few-shot prompting: síntesis comparativa

| Criterio | Prompt básico | Prompt mejorado |
|---|---|---|
| Empatía ante situaciones negativas | Ausente | Presente y consistente |
| Distinción retornable / no retornable | Inconsistente | Correcta en todos los casos |
| Estructura de la respuesta | Variable | Uniforme entre respuestas |
| Riesgo de datos inventados | Alto | Mitigado por restricciones explícitas |
| Alineación con tono de marca | Baja | Alta |
| Pasos del proceso incluidos | Rara vez | Siempre que aplica |

La mejora más relevante no proviene de cambiar el modelo, sino de **diseñar el
prompt como un sistema**: rol + restricciones + ejemplos + datos. Cada uno de estos
elementos cumple una función específica y su combinación determina la calidad final
de la respuesta.

---

## 7. Decisiones de diseño clave

**Separación de fuentes de verdad y capa generativa.**
Los datos operativos (pedidos) y las reglas de negocio (política de devoluciones)
nunca son generados por el modelo: se recuperan y se inyectan en el prompt. El LLM
solo redacta. Esta decisión es la principal salvaguarda contra alucinaciones en los
puntos más críticos del sistema.

**Few-shot prompting en lugar de fine-tuning.**
Los ejemplos incluidos en el prompt enseñan al modelo el tono, la estructura y el
nivel de empatía esperados sin necesidad de reentrenamiento. Cualquier ajuste en
el comportamiento del sistema se realiza modificando los ejemplos, no el modelo.
Esto reduce el costo de mantenimiento y permite iteración rápida.

**Restricciones explícitas en el prompt.**
Instrucciones como "do not invent data" o "only use the information provided" no
son redundantes: son necesarias para acotar el comportamiento del modelo y reducir
la probabilidad de respuestas fuera del dominio o con información no verificada.

---

## 8. Conclusión

El ejercicio demuestra que la calidad del sistema de atención al cliente no depende
exclusivamente del tamaño o la capacidad del modelo generativo, sino del diseño del
prompt que lo guía. Un modelo pequeño como Gemma 2B, correctamente orientado mediante
few-shot prompting, contexto estructurado y restricciones explícitas, produce
respuestas empáticas, precisas y alineadas con las políticas del negocio.

La ingeniería de prompts no es un detalle de implementación: es una decisión
arquitectónica que determina el comportamiento observable del sistema para el cliente
final.
