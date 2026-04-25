# Fase 3: Integración y Ejecución del Código — Pipeline RAG End-to-End

## 1. Introducción

Esta fase aterriza en código la arquitectura RAG propuesta para EcoMarket. A diferencia de las dos fases anteriores, que se enfocan en decisiones de diseño y preparación de la base de conocimiento, esta sección explica cómo se conectan los componentes del repositorio para construir un asistente virtual funcional.

El objetivo principal es demostrar que el sistema no depende únicamente del conocimiento interno del modelo de lenguaje. En su lugar, cada respuesta se genera a partir de una combinación controlada de tres elementos: intención detectada, información recuperada desde la base de conocimiento y datos estructurados cuando la consulta lo requiere.

La solución implementada mantiene el principio central definido desde el Taller Práctico #1: el LLM no debe actuar como fuente de verdad. Su rol es redactar respuestas en lenguaje natural a partir de información previamente recuperada o consultada en fuentes internas.

---

## 3. Arquitectura general del sistema

El sistema sigue un flujo modular, desde el mensaje del usuario hasta la respuesta final en la interfaz.

```text
Mensaje del usuario en Streamlit
        ↓
Detección de intención
        ↓
Búsqueda estructurada si aplica
        ↓
Recuperación RAG desde FAISS
        ↓
Construcción del prompt
        ↓
Generación con Gemma 2B vía Ollama
        ↓
Respuesta final en Streamlit
```

La arquitectura implementa siete intenciones principales:

| Intención | Propósito |
|---|---|
| `order_status` | Consultar estado de pedidos usando número de seguimiento |
| `return_policy` | Responder preguntas sobre devoluciones y reembolsos |
| `shipping` | Responder preguntas sobre envíos, tiempos y cobertura |
| `inventory` | Consultar disponibilidad, perecibilidad y vencimientos |
| `product` | Responder preguntas sobre productos del catálogo |
| `human` | Escalar solicitudes complejas o emocionales |
| `general` | Atender consultas generales usando la base de conocimiento completa |

Esta organización permite que cada tipo de consulta siga una ruta distinta, con fuentes de información y prompts especializados.

---

## 4. Estructura modular del repositorio

El repositorio se organizó para separar responsabilidades y facilitar el mantenimiento del sistema. La estructura principal es la siguiente:

```text
ecomarket-rag-assistant/
├── app.py
├── src/
│   ├── core/
│   │   ├── router.py
│   │   └── utils.py
│   ├── llm/
│   │   ├── llm_client.py
│   │   └── prompts.py
│   ├── rag/
│   │   ├── document_loader.py
│   │   ├── rag_pipeline.py
│   │   └── retriever.py
│   ├── services/
│   │   ├── inventory_service.py
│   │   └── order_service.py
│   └── ui_blocks/
│       ├── chat_handler.py
│       └── sidebar.py
├── data/
├── vectorstore/
└── docs/
```

Cada carpeta cumple una función específica:

| Módulo | Responsabilidad |
|---|---|
| `core` | Detección de intención y utilidades compartidas |
| `rag` | Carga documental, chunking, embeddings, FAISS y recuperación |
| `services` | Consulta estructurada de pedidos e inventario |
| `llm` | Construcción de prompts y generación de respuestas |
| `ui_blocks` | Componentes auxiliares de la interfaz |
| `app.py` | Punto de entrada de Streamlit |

Esta separación permite que la lógica de negocio, la recuperación documental, la generación de lenguaje y la interfaz no queden mezcladas en un único archivo.

---

## 5. Detección de intención y enrutamiento

El primer paso del sistema es clasificar el mensaje del usuario. Esta tarea se implementa en `src/core/router.py` mediante la función `detect_intent()`.

El router utiliza reglas basadas en palabras clave para clasificar la consulta en una de las siete intenciones soportadas. Por ejemplo, una consulta que incluya términos como `order`, `tracking` o un código tipo `ECO20105` se dirige al flujo de pedidos. Una pregunta con palabras como `return`, `refund` o `exchange` se dirige al flujo de devoluciones.

Esta estrategia fue elegida por su simplicidad, velocidad y transparencia. En un MVP académico, un router basado en reglas permite explicar claramente por qué una consulta siguió una ruta determinada. Además, evita usar el LLM para clasificar intención antes de generar la respuesta, reduciendo latencia y complejidad.

Su principal limitación es que puede fallar ante consultas ambiguas o redactadas de forma poco común. En una visión profesional, este componente podría evolucionar hacia un clasificador basado en embeddings, un modelo supervisado o un router híbrido que combine reglas, similitud semántica y confianza de clasificación.

---

## 6. Carga de documentos y construcción del índice RAG

La carga de documentos se implementa en `src/rag/document_loader.py`. Este módulo convierte diferentes tipos de archivos en objetos `Document` de LangChain, preservando tanto el contenido textual como metadatos útiles para la recuperación.

Las fuentes incluidas son:

| Fuente | Formato | Uso dentro del sistema |
|---|---|---|
| Política de devoluciones | PDF | Responder preguntas sobre elegibilidad, proceso y reembolsos |
| Política de envíos | PDF | Responder preguntas sobre tiempos, cobertura y condiciones |
| Inventario | Excel | Consultar stock, perecibilidad y vencimientos |
| Catálogo de productos | Excel | Responder preguntas descriptivas sobre productos |
| Pedidos | JSON | Consultar estados y contexto operativo de pedidos |
| Ejemplos de soporte | JSON | Guiar tono, estructura y estilo de respuesta |

Después de cargar los documentos, el pipeline RAG se ejecuta desde `src/rag/rag_pipeline.py`. El proceso general es:

1. Cargar todos los documentos.
2. Dividir los textos largos en chunks.
3. Convertir cada chunk en un embedding.
4. Construir el índice FAISS.
5. Guardar el índice en disco.
6. Reutilizar el índice en ejecuciones posteriores.

La configuración de chunking utilizada está alineada con el análisis EDA realizado sobre los documentos del proyecto:

```python
RecursiveCharacterTextSplitter(
    chunk_size=391,
    chunk_overlap=45,
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

Esta configuración permite mantener intactos los registros estructurados de inventario, catálogo y pedidos, mientras divide los PDFs en fragmentos más pequeños y útiles para recuperación semántica. El índice se guarda en `vectorstore/faiss_index/`, evitando recalcular embeddings cada vez que se inicia la aplicación.

---

## 7. Recuperación de contexto con FAISS

La recuperación semántica se implementa en `src/rag/retriever.py`. La función principal recibe la consulta del usuario, el índice FAISS y un número de fragmentos a recuperar. También puede aplicar filtros por tipo de documento cuando la intención lo requiere.

Por ejemplo:

| Intención | Recuperación esperada |
|---|---|
| `return_policy` | Fragmentos de la política de devoluciones |
| `shipping` | Fragmentos de la política de envíos |
| `product` | Fragmentos del catálogo de productos |
| `general` | Búsqueda sobre toda la base de conocimiento |

El resultado de la recuperación tiene dos usos. Primero, se concatena como contexto dentro del prompt enviado al modelo. Segundo, sus metadatos se muestran en la interfaz para hacer visible qué fuentes fueron recuperadas.

Este diseño mejora la transparencia del sistema. El usuario no solo recibe una respuesta generada, sino que el sistema puede mostrar qué documentos o fragmentos sirvieron como soporte.

---

## 8. Integración con datos estructurados

No todas las consultas deben resolverse únicamente con recuperación semántica. Para información crítica, como pedidos e inventario, el sistema usa búsqueda estructurada.

El servicio `src/services/order_service.py` permite buscar pedidos por número de seguimiento. Si el usuario pregunta por un pedido como `ECO20105`, el sistema extrae ese identificador y consulta directamente el archivo de pedidos. La respuesta del LLM se construye usando esa información como fuente autoritativa.

De forma similar, `src/services/inventory_service.py` permite buscar productos por ID o por coincidencia parcial de nombre. Esto es importante para preguntas como disponibilidad, stock, categoría, lote, fecha de fabricación o fecha de expiración.

Esta decisión es una de las más importantes del proyecto: el RAG no reemplaza las fuentes estructuradas. Las complementa. La información operativa exacta se consulta de manera determinística, mientras que RAG aporta contexto adicional, políticas relacionadas o explicaciones en lenguaje natural.

---

## 9. Construcción de prompts y generación con el LLM

Los prompts se construyen en `src/llm/prompts.py`. Existe un constructor de prompt para cada intención del sistema:

| Constructor | Intención |
|---|---|
| `build_order_prompt()` | Estado de pedido |
| `build_return_prompt()` | Política de devolución |
| `build_shipping_prompt()` | Envíos |
| `build_inventory_prompt()` | Inventario |
| `build_product_prompt()` | Producto |
| `build_human_prompt()` | Escalamiento humano |
| `build_general_prompt()` | Consulta general |

Cada prompt combina instrucciones de comportamiento, contexto recuperado, datos estructurados cuando aplican, ejemplos few-shot y la pregunta del usuario. Las instrucciones incluyen reglas explícitas para evitar que el modelo invente información.

La generación se realiza en `src/llm/llm_client.py`, usando Gemma 2B a través de Ollama. El modelo se ejecuta localmente con temperatura `0`, buscando respuestas más determinísticas y menos creativas. Esta configuración es adecuada para soporte al cliente, donde la prioridad no es la originalidad sino la consistencia, precisión y claridad.

El sistema también maneja errores comunes: modelo no descargado, servidor de Ollama apagado o fallos inesperados. Esto mejora la experiencia de ejecución del MVP y facilita su revisión por parte de terceros.

---

## 10. Interfaz en Streamlit

La interfaz se implementa en `app.py` y componentes auxiliares dentro de `src/ui_blocks/`. Streamlit permite construir una demo funcional de forma rápida, manteniendo una experiencia similar a un chat de atención al cliente.

La aplicación cumple varias funciones:

1. Recibe el mensaje del usuario.
2. Mantiene historial de conversación en `st.session_state`.
3. Ejecuta el flujo de detección de intención.
4. Llama al pipeline de recuperación y generación.
5. Muestra la respuesta generada.
6. Presenta información adicional como intención detectada, estado del RAG y fuentes recuperadas.

El índice FAISS se carga usando caché de recursos, de modo que no se reconstruye en cada interacción. Esto mejora el rendimiento de la aplicación y hace viable la ejecución local.

Aunque Streamlit no representa una arquitectura productiva final para atención omnicanal, sí es adecuado para el propósito académico: demostrar de forma visual e interactiva que la solución RAG funciona de extremo a extremo.

---

## 11. Ejemplo de flujo end-to-end

Supongamos que el usuario escribe:

```text
Where is my order ECO20105?
```

El flujo interno sería:

1. `detect_intent()` clasifica la consulta como `order_status`.
2. `extract_tracking_number()` identifica el código `ECO20105`.
3. `get_order()` consulta el archivo de pedidos y recupera la información estructurada.
4. `retrieve_context_text()` recupera contexto adicional desde FAISS, por ejemplo fragmentos sobre políticas de envío.
5. `build_order_prompt()` construye el prompt con instrucciones, datos del pedido y contexto recuperado.
6. `generate_llm_response()` envía el prompt a Gemma 2B mediante Ollama.
7. El sistema formatea la respuesta y la muestra en Streamlit.
8. La interfaz presenta también la intención detectada y las fuentes recuperadas.

Este flujo demuestra la idea central del sistema: el modelo no responde desde memoria ni inventa el estado del pedido. La respuesta se apoya en una consulta estructurada y se complementa con recuperación documental.

---

## 12. Limitaciones, supuestos y conclusión

La solución implementada es funcional para el alcance académico, pero tiene limitaciones claras.

Primero, el router basado en palabras clave puede fallar ante consultas ambiguas. Segundo, Gemma 2B es un modelo pequeño y puede producir respuestas limitadas si el contexto recuperado no es suficiente. Tercero, la base de conocimiento es estática: si los documentos cambian, es necesario reconstruir el índice. Cuarto, la memoria conversacional es limitada, por lo que cada consulta se procesa principalmente como una interacción independiente. Finalmente, FAISS no está diseñado como una base vectorial gestionada para actualizaciones en tiempo real o múltiples usuarios concurrentes.

Los principales supuestos del MVP son:

- Los archivos de datos están disponibles en la carpeta `data/`.
- Ollama se ejecuta localmente.
- El modelo `gemma2:2b` está descargado.
- El índice FAISS puede construirse localmente en la primera ejecución.
- Los documentos del taller son representativos de la base de conocimiento de EcoMarket.

A pesar de estas limitaciones, la implementación cumple el objetivo central del Taller 2: integrar un sistema RAG funcional en la solución del Taller 1. El repositorio demuestra cómo cargar documentos, dividirlos en chunks, generar embeddings, construir una base vectorial, recuperar contexto relevante, combinarlo con datos estructurados y producir respuestas mediante un LLM local.

En síntesis, esta fase muestra que la arquitectura propuesta no se queda en un diseño conceptual. El sistema implementado permite ejecutar un flujo completo de atención al cliente basado en recuperación aumentada, manteniendo una separación clara entre datos, conocimiento documental, lógica de enrutamiento, prompts y generación de lenguaje natural.
