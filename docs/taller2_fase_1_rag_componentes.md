# Fase 1: Selección de componentes clave del sistema RAG

## 1. Introducción

En el Taller Práctico #1 se propuso una arquitectura híbrida para el asistente virtual de EcoMarket. La idea central era separar la fuente de verdad operativa de la capa generativa: el modelo de lenguaje no debía inventar estados de pedidos, políticas de devolución ni información de productos, sino redactar respuestas naturales a partir de información previamente recuperada.

En este segundo taller, esa visión evoluciona hacia una arquitectura RAG, es decir, una solución de generación aumentada por recuperación. El objetivo es que el asistente no dependa únicamente del conocimiento interno del modelo, sino que consulte documentos propios de EcoMarket antes de generar una respuesta. Esto reduce el riesgo de alucinaciones y permite que el sistema responda con información más precisa, actualizada y alineada con las reglas reales del negocio.

Para construir este sistema RAG se deben tomar dos decisiones arquitectónicas fundamentales:

1. Qué modelo de embeddings utilizar para convertir documentos y consultas en representaciones vectoriales.
2. Qué base vectorial utilizar para almacenar esos vectores y hacer búsquedas por similitud.

Estas decisiones impactan directamente la calidad de recuperación, el costo, la complejidad de despliegue, la escalabilidad y la viabilidad del prototipo académico.

---

## 2. Visión profesional vs. MVP académico

Antes de justificar los componentes seleccionados, es importante distinguir entre la visión profesional de la solución y la versión académica implementada para el taller.

En una implementación profesional para EcoMarket, el sistema RAG debería estar preparado para manejar un volumen mayor de documentos, actualizaciones frecuentes de políticas, integración con sistemas internos, trazabilidad de respuestas, monitoreo de calidad y posiblemente despliegue en la nube. En ese escenario, podrían considerarse modelos de embeddings más robustos y bases vectoriales gestionadas o autoalojadas con capacidades avanzadas de filtrado, control de acceso, actualización incremental y escalabilidad horizontal.

Sin embargo, el objetivo del taller no es construir una plataforma empresarial completa, sino demostrar de forma funcional y defendible cómo un asistente de atención al cliente puede mejorar sus respuestas usando recuperación de conocimiento. Por eso, el MVP académico prioriza componentes locales, gratuitos, reproducibles y fáciles de ejecutar en un entorno de desarrollo.

La decisión final debe evaluarse bajo esa doble lectura:

| Dimensión | Visión profesional | MVP académico implementado |
|---|---|---|
| Escala esperada | Miles o millones de documentos y consultas frecuentes | Corpus pequeño o mediano con documentos de ejemplo |
| Infraestructura | Nube, servicios gestionados o despliegue controlado | Ejecución local |
| Costo | Puede justificar servicios pagos si hay valor de negocio | Debe minimizar costos |
| Actualización de documentos | Frecuente e incremental | Reindexación manual o local |
| Base vectorial | Pinecone, Weaviate, Qdrant, ChromaDB o FAISS según necesidad | FAISS local |
| Modelo de embeddings | Preferiblemente multilingüe y robusto | `sentence-transformers/all-MiniLM-L6-v2` |
| Objetivo principal | Producción, monitoreo y escalabilidad | Demostración técnica clara y reproducible |

Esta distinción permite justificar por qué algunas decisiones son suficientes para el taller, aunque no necesariamente serían la única opción en un despliegue empresarial real.

---

## 3. Modelo de embeddings seleccionado

### 3.1 Modelo elegido

Para el MVP académico se seleccionó el modelo:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Este modelo se utiliza mediante la librería `sentence-transformers`, integrada al flujo de LangChain a través de `HuggingFaceEmbeddings`.

| Característica | Valor |
|---|---|
| Modelo | `sentence-transformers/all-MiniLM-L6-v2` |
| Librería | `sentence-transformers` / `langchain-huggingface` |
| Tamaño aproximado | 22 MB |
| Dimensión del embedding | 384 |
| Longitud máxima de entrada | 512 tokens |
| Requiere GPU | No |
| Ejecución | Local en CPU |
| Normalización | Embeddings normalizados para similitud coseno |

---

## 4. Justificación del modelo de embeddings

La elección del modelo de embeddings no se basó únicamente en rendimiento técnico, sino en su adecuación al contexto del taller, al tamaño del corpus y a las restricciones de ejecución local.

### 4.1 Bajo costo y ejecución local

`all-MiniLM-L6-v2` es un modelo liviano que puede ejecutarse localmente sin GPU. Esto es fundamental para un prototipo académico, porque permite que cualquier integrante del equipo pueda correr el sistema sin depender de infraestructura en la nube, tarjetas gráficas o servicios externos pagos.

A diferencia de modelos propietarios como OpenAI Embeddings o Cohere Embeddings, este modelo no genera costos por consulta, no tiene límites de uso por API y no requiere enviar documentos internos a un tercero. Esto es coherente con la decisión tomada desde el Taller 1: proteger la información de EcoMarket y mantener control local sobre los datos.

### 4.2 Suficiente calidad para un corpus acotado

El corpus del proyecto está compuesto por documentos relativamente controlados: políticas de devolución, políticas de envío, catálogo de productos, inventario y pedidos de ejemplo. No se trata de una base documental masiva ni altamente ambigua. En este contexto, un modelo pequeño pero eficiente es suficiente para capturar similitud semántica entre preguntas del usuario y fragmentos relevantes de documentos.

Además, el sistema no depende exclusivamente del RAG para todos los casos. La arquitectura también incorpora búsqueda estructurada para pedidos e inventario. Esto significa que los datos críticos, como el estado de un pedido o la disponibilidad de un producto, no se recuperan únicamente por similitud semántica, sino desde fuentes estructuradas. El modelo de embeddings se utiliza principalmente para recuperar contexto documental, no para reemplazar sistemas transaccionales.

### 4.3 Integración sencilla con LangChain

El modelo seleccionado tiene integración directa con LangChain. Esto permite construir el pipeline de RAG con una estructura clara:

1. Cargar documentos.
2. Dividirlos en chunks.
3. Convertir cada chunk en un vector.
4. Guardar los vectores en FAISS.
5. Recuperar los fragmentos más similares ante una consulta.
6. Inyectar esos fragmentos en el prompt final.

Esta integración reduce la complejidad del código y permite concentrar el taller en la comprensión del flujo RAG, no en detalles de bajo nivel sobre generación y almacenamiento manual de vectores.

### 4.4 Reproducibilidad

Al ser un modelo open-source descargado localmente, los embeddings generados son reproducibles entre ejecuciones. Esto es importante para un taller académico, porque permite que el sistema sea evaluado, ejecutado y explicado de forma consistente.

En una solución basada en servicios externos, podrían aparecer variaciones por cambios de versión del proveedor, límites de API, costos o configuraciones no controladas por el equipo. Para el objetivo del MVP, mantener un entorno reproducible es una ventaja clara.

---

## 5. Consideraciones sobre idioma español

Un punto importante del enunciado del taller es la capacidad de manejar el idioma español. En este caso, la decisión debe analizarse con cuidado.

`all-MiniLM-L6-v2` está optimizado principalmente para inglés. Por tanto, no sería la mejor elección si EcoMarket tuviera una base documental mayoritariamente en español o si el sistema debiera operar de forma bilingüe en producción.

Sin embargo, para el MVP académico actual, esta elección es aceptable por tres razones:

1. Los documentos de prueba del repositorio están principalmente en inglés.
2. Las preguntas de ejemplo también están formuladas en inglés.
3. El objetivo central del taller es demostrar el flujo RAG completo, no optimizar un sistema multilingüe productivo.

Aun así, si la solución evolucionara hacia una versión profesional para usuarios hispanohablantes, sería recomendable reemplazar el modelo por uno multilingüe. Dos alternativas razonables serían:

| Modelo alternativo | Ventaja |
|---|---|
| `intfloat/multilingual-e5-base` | Mejor desempeño multilingüe, adecuado para español e inglés |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Alternativa liviana y multilingüe basada en Sentence Transformers |

Por tanto, la decisión puede resumirse así: `all-MiniLM-L6-v2` es adecuado para el MVP académico actual por costo, simplicidad y compatibilidad con el corpus disponible; pero en una visión profesional bilingüe o en español, se recomendaría migrar a un modelo multilingüe.

---

## 6. Base vectorial seleccionada

### 6.1 Base vectorial elegida

Para almacenar los embeddings y realizar búsqueda por similitud se seleccionó:

```text
FAISS — Facebook AI Similarity Search
```

| Característica | Valor |
|---|---|
| Base vectorial | FAISS |
| Librería | `faiss-cpu` / `langchain-community` |
| Tipo de almacenamiento | Local |
| Persistencia | Disco local |
| Ruta en el proyecto | `vectorstore/faiss_index/` |
| Integración | LangChain |
| Tipo de búsqueda | Similitud vectorial |
| Costo | Gratuito |

---

## 7. Justificación de FAISS

### 7.1 Adecuada para un prototipo local

FAISS es una librería local de búsqueda vectorial. No requiere servidor externo, contenedor Docker, cuenta en la nube ni API key. Esto la convierte en una opción muy adecuada para un taller académico donde se busca que el sistema sea fácil de ejecutar y reproducir.

En el caso de EcoMarket, el corpus del MVP contiene un número limitado de documentos y aproximadamente algunos cientos de chunks. A esta escala, FAISS puede realizar búsquedas por similitud de forma rápida y eficiente.

### 7.2 Sin costo de infraestructura

Al ejecutarse localmente, FAISS no genera costos por almacenamiento ni por consulta. Esto es coherente con el enfoque del proyecto: construir una solución funcional, de bajo costo y ejecutable en equipos personales.

Bases vectoriales gestionadas como Pinecone pueden ser muy convenientes en producción, pero para este taller introducirían dependencias innecesarias: cuentas externas, configuración de servicios, posibles límites de uso y costos adicionales.

### 7.3 Integración directa con LangChain

FAISS cuenta con soporte directo en LangChain. Esto permite construir el índice vectorial desde documentos con métodos como `FAISS.from_documents()`, guardarlo localmente con `save_local()` y cargarlo en ejecuciones posteriores con `load_local()`.

Esta persistencia es importante porque evita recalcular embeddings cada vez que se inicia la aplicación. En el repositorio, el índice se construye en la primera ejecución y luego se reutiliza, haciendo que el arranque posterior del sistema sea más rápido.

### 7.4 Suficiente para el tamaño del corpus

Para un corpus pequeño o mediano, FAISS es más que suficiente. La búsqueda exacta o aproximada en un conjunto de cientos o miles de vectores tiene muy buen rendimiento local. En este proyecto, donde la base de conocimiento contiene documentos de políticas, catálogo e inventario, no se requiere una base vectorial distribuida ni capacidades avanzadas de escalabilidad.

---

## 8. Comparación con bases vectoriales alternativas

Aunque FAISS fue la opción seleccionada para el MVP, existen otras alternativas relevantes. La siguiente tabla resume sus ventajas y desventajas para el caso de EcoMarket.

| Base vectorial | Tipo | Ventajas | Desventajas | Adecuación al MVP |
|---|---|---|---|---|
| FAISS | Librería local | Gratuita, rápida, simple, sin infraestructura externa | Menos amigable para actualizaciones incrementales y gestión avanzada de metadatos | Muy alta |
| ChromaDB | Local / servidor | Fácil de usar, buena persistencia, API amigable | Menor madurez en escenarios de muy alto rendimiento | Alta |
| Pinecone | Servicio gestionado | Muy escalable, fácil de operar en producción, actualizaciones en tiempo real | Costo, dependencia externa, requiere API y conexión a la nube | Media-baja para el MVP |
| Weaviate | Self-hosted / cloud | Potente, soporta filtros, esquemas, GraphQL y casos empresariales | Mayor complejidad de instalación y operación | Baja para el MVP |
| Qdrant | Self-hosted / cloud | Buen balance entre rendimiento, filtros y producción | Requiere servicio adicional o configuración más compleja | Media |
| pgvector | Extensión de PostgreSQL | Útil si la empresa ya usa PostgreSQL | Menos directo para un prototipo simple | Media |

---

## 9. FAISS frente a alternativas principales

### 9.1 FAISS vs. ChromaDB

ChromaDB era la alternativa local más cercana. También es gratuita, fácil de usar y adecuada para prototipos. Su principal ventaja es que ofrece una experiencia más amigable para desarrolladores, con persistencia y manejo de colecciones más directo.

Sin embargo, FAISS fue seleccionado porque es muy maduro, ampliamente usado en ejemplos de LangChain, rápido para búsqueda por similitud pura y suficiente para el tamaño del corpus del taller.

En una fase futura, ChromaDB podría ser una buena alternativa si el equipo quisiera una experiencia más organizada para colecciones, metadatos y persistencia.

### 9.2 FAISS vs. Pinecone

Pinecone es una base vectorial gestionada orientada a producción. Sería una opción fuerte para una versión profesional de EcoMarket si el sistema manejara grandes volúmenes de documentos, múltiples usuarios, actualizaciones frecuentes y requerimientos de disponibilidad.

Sin embargo, para el MVP académico, Pinecone introduce más complejidad de la necesaria. Requiere conexión a internet, cuenta externa, API key y potencialmente costos por uso. Además, enviar embeddings o información asociada a un servicio externo puede ser menos coherente con la decisión de mantener control local sobre la información.

Por eso, Pinecone es una buena opción para producción, pero no es la mejor para esta etapa académica.

### 9.3 FAISS vs. Weaviate

Weaviate es una solución más completa, pensada para casos empresariales con esquemas, filtros avanzados, consultas híbridas, despliegue en servidor y uso multimodal. Estas capacidades son valiosas, pero exceden las necesidades actuales del taller.

Para EcoMarket en una visión profesional, Weaviate podría considerarse si el asistente necesitara búsqueda híbrida entre texto y metadatos, separación por tipos de documentos, control de acceso o escalabilidad avanzada. Para el MVP, su complejidad operativa no se justifica.

---

## 10. Configuración del pipeline de embeddings

En el repositorio, la configuración del modelo de embeddings puede representarse de la siguiente forma:

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

La normalización de embeddings permite que la comparación semántica sea más estable usando similitud coseno. En términos prácticos, esto ayuda a que las preguntas del usuario se comparen mejor contra los fragmentos de documentos almacenados en la base vectorial.

El flujo general queda así:

```text
Documentos de EcoMarket
        ↓
Carga de documentos
        ↓
Segmentación en chunks
        ↓
Generación de embeddings
        ↓
Almacenamiento en FAISS
        ↓
Consulta del usuario
        ↓
Embedding de la consulta
        ↓
Búsqueda de chunks similares
        ↓
Construcción del prompt
        ↓
Respuesta generada por el LLM
```

---

## 11. Decisión final

La selección de `all-MiniLM-L6-v2` y FAISS responde a una lógica de prototipo académico: bajo costo, ejecución local, integración sencilla con LangChain, reproducibilidad y suficiente calidad para un corpus controlado.

No obstante, la decisión no se presenta como una solución única para todos los contextos. En una visión profesional de EcoMarket, especialmente si la base documental crece, si se requiere operación bilingüe o si el sistema debe actualizar documentos en tiempo real, sería recomendable evaluar componentes más robustos:

| Componente | MVP académico | Posible evolución profesional |
|---|---|---|
| Modelo de embeddings | `all-MiniLM-L6-v2` | `multilingual-e5-base`, `multilingual-e5-large` o embeddings propietarios |
| Base vectorial | FAISS local | Pinecone, Qdrant, Weaviate o ChromaDB persistente |
| Infraestructura | Local | Nube o servidor interno |
| Actualización del índice | Rebuild local | Upserts incrementales y monitoreo |
| Idioma | Principalmente inglés | Español / bilingüe |
| Seguridad | Datos locales | Control de acceso, auditoría, cifrado y gobernanza |

---

## 12. Conclusión

Para el sistema RAG de EcoMarket, el modelo `sentence-transformers/all-MiniLM-L6-v2` y la base vectorial FAISS representan una combinación adecuada para el MVP académico. Ambos componentes permiten construir un sistema funcional, económico y reproducible, sin depender de servicios externos ni infraestructura compleja.

La decisión es coherente con la arquitectura planteada desde el Taller 1: el modelo generativo no actúa como fuente de verdad, sino como una capa de redacción apoyada por recuperación de información. En este Taller 2, FAISS y el modelo de embeddings cumplen precisamente esa función: recuperar los fragmentos más relevantes de la base de conocimiento para que Gemma 2B pueda generar respuestas mejor fundamentadas.

En síntesis, la solución implementada no intenta simular una plataforma empresarial completa, sino demostrar el núcleo funcional de una arquitectura RAG: cargar documentos, segmentarlos, vectorizarlos, recuperarlos por similitud e incorporarlos al prompt final. Esta base es suficiente para el alcance académico y, al mismo tiempo, deja definido un camino claro de evolución hacia una implementación profesional más escalable, multilingüe y gobernada.
