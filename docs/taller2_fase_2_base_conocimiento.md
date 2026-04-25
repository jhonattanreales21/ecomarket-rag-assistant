# Fase 2: Creación de la Base de Conocimiento para el Sistema RAG

## 1. Introducción

El éxito de un sistema RAG no depende únicamente del modelo de lenguaje ni de la base vectorial seleccionada. Una parte fundamental de la solución está en la calidad, estructura y preparación de la base de conocimiento que el sistema puede consultar antes de generar una respuesta.

En el caso de EcoMarket, el objetivo de esta fase es construir una base documental que permita al asistente responder preguntas frecuentes de atención al cliente con información precisa, actualizada y alineada con las reglas del negocio. Para ello, se integran documentos de políticas, datos estructurados de productos, inventario, pedidos y ejemplos de soporte.

Esta fase representa una evolución natural del Taller Práctico #1. En el primer taller, la solución ya separaba la fuente de verdad de la capa generativa: los pedidos se consultaban desde datos estructurados y las políticas se inyectaban en el prompt. En este segundo taller, esa idea se amplía mediante una arquitectura RAG, donde los documentos no se insertan completos en el prompt, sino que se fragmentan, vectorizan e indexan para recuperar únicamente los fragmentos más relevantes ante cada consulta.

La base de conocimiento cumple tres funciones principales:

1. Proveer información confiable para reducir alucinaciones.
2. Permitir que el asistente responda más tipos de preguntas.
3. Mantener la solución modular y extensible para futuras fuentes documentales.

---

## 2. Visión profesional vs. MVP académico

Antes de describir los documentos y el proceso de indexación, es importante distinguir entre la visión profesional de la solución y la versión académica implementada en el repositorio.

En una implementación profesional para EcoMarket, la base de conocimiento podría integrarse con sistemas internos reales: gestor de pedidos, CRM, ERP, sistema de inventario, catálogo de productos, base de tickets históricos y repositorios documentales corporativos. Además, debería contar con controles de actualización, versionamiento, trazabilidad, seguridad, auditoría y monitoreo de calidad de recuperación.

Sin embargo, el objetivo del taller es demostrar el núcleo funcional de una arquitectura RAG. Por esta razón, el MVP académico utiliza archivos locales que simulan las principales fuentes de información de una empresa de e-commerce: documentos PDF, hojas de cálculo Excel y archivos JSON. Esta simplificación permite ejecutar el sistema localmente, mantener bajo el costo del prototipo y explicar con claridad cómo se conectan las piezas del flujo RAG.

| Dimensión | Visión profesional | MVP académico implementado |
|---|---|---|
| Fuentes de datos | CRM, OMS, ERP, gestor documental, base histórica de tickets | Archivos PDF, Excel y JSON locales |
| Actualización | Incremental, automatizada y con versionamiento | Manual o mediante reconstrucción local del índice |
| Seguridad | Control de acceso, auditoría, cifrado y gobernanza | Datos sintéticos o de ejemplo sin información sensible real |
| Escala | Miles o millones de documentos y consultas frecuentes | Corpus controlado de tamaño pequeño o mediano |
| Integración | Servicios internos y APIs empresariales | Carga local desde la carpeta `data/` |
| Objetivo | Operación en producción | Demostración académica funcional y reproducible |

Esta separación es importante porque evita evaluar el prototipo con exigencias propias de una plataforma empresarial completa, pero al mismo tiempo muestra que la solución está diseñada siguiendo principios que podrían escalar hacia una implementación real.

---

## 3. Documentos seleccionados para la base de conocimiento

La base de conocimiento se diseñó para cubrir las consultas más representativas de un asistente de atención al cliente en un e-commerce sostenible. Se incluyeron seis tipos de fuentes: políticas de devolución, políticas de envío, inventario, catálogo de productos, pedidos y ejemplos de soporte.

Estas fuentes combinan documentos no estructurados, como PDFs de políticas, con datos estructurados, como hojas de cálculo y archivos JSON. Esta combinación es importante porque no todas las preguntas deben resolverse de la misma manera. Algunas requieren recuperación semántica de documentos; otras requieren búsqueda exacta sobre datos operativos.

---

## 4. Política de devoluciones

### Archivo utilizado

`EcoMarket ReturnPolicy.pdf`

### Relevancia para el sistema

Las preguntas sobre devoluciones y reembolsos son una de las categorías más comunes en atención al cliente. Los usuarios pueden preguntar si un producto puede devolverse, cuál es el plazo permitido, qué ocurre con productos dañados, si un producto de higiene abierto aplica para devolución o cuáles son los pasos del proceso.

La política de devoluciones funciona como fuente oficial para este tipo de respuestas. El asistente no debe inventar excepciones ni interpretar libremente las reglas, sino recuperar los fragmentos relevantes de la política y redactar una respuesta clara para el usuario.

### Rol dentro del RAG

En el Taller 1, la política podía inyectarse completa en el prompt. Esa estrategia es aceptable para documentos pequeños, pero no escala bien. A medida que las políticas crecen, insertar el documento completo consume espacio de contexto y aumenta el riesgo de que el modelo use información no relevante.

Con RAG, el sistema recupera únicamente los fragmentos más cercanos a la pregunta del usuario. Por ejemplo, ante una consulta sobre un producto de higiene abierto, el sistema debería recuperar la sección relacionada con productos no elegibles para devolución, no toda la política completa.

---

## 5. Política de envíos

### Archivo utilizado

`EcoMarket ShippingPolicy.pdf`

### Relevancia para el sistema

Las preguntas sobre envío también son frecuentes en e-commerce. Los clientes suelen preguntar por tiempos estimados de entrega, envíos internacionales, costos, envío gratuito, retrasos, métodos express y compensaciones por demoras.

La política de envíos representa la fuente de verdad para estas reglas. Su inclusión permite que el asistente responda preguntas como:

- ¿Cuánto tarda el envío estándar?
- ¿EcoMarket realiza envíos internacionales?
- ¿Qué pasa si mi pedido está retrasado?
- ¿Existe envío gratuito?
- ¿Cuál es la diferencia entre envío estándar y express?

### Rol dentro del RAG

Este documento es especialmente adecuado para recuperación semántica, porque los clientes no siempre formulan sus preguntas con las mismas palabras exactas de la política. Un usuario puede preguntar “¿cuándo llega mi paquete?” o “¿cuánto demora el envío?”, y ambas consultas deberían recuperar información relacionada con tiempos de entrega.

---

## 6. Inventario de productos

### Archivo utilizado

`inventory_200_products_named.xlsx`

### Relevancia para el sistema

El inventario permite responder preguntas relacionadas con disponibilidad, stock, bodega, fecha de fabricación, fecha de expiración, vida útil y condición perecedera de los productos.

El archivo contiene 200 registros, uno por producto, con campos como:

```text
product_id
product_name
category
batch
perishable
manufacturing_date
expiration_date
shelf_life
stock
warehouse
```

Estas preguntas son sensibles desde el punto de vista operativo, porque una respuesta incorrecta sobre disponibilidad o expiración puede afectar directamente la experiencia del cliente.

### Enfoque utilizado

Cada fila del Excel se convierte en un documento de texto con estructura de pares clave-valor. Por ejemplo:

```text
Inventory record — product_id: P0001 | product_name: Organic Whole Milk | category: Food | perishable: Yes | expiration_date: 2026-05-10 | stock: 35 | warehouse: A
```

Sin embargo, para consultas exactas, el sistema no depende únicamente del RAG. El repositorio incluye un servicio estructurado (`inventory_service.py`) que permite buscar productos por `product_id` o por coincidencias parciales de nombre. Esto es coherente con el principio definido desde el Taller 1: los datos operativos deben venir de fuentes estructuradas siempre que sea posible.

Por tanto, el inventario cumple una doble función:

1. Fuente estructurada para consultas exactas.
2. Fuente documental indexada para recuperación semántica y enriquecimiento contextual.

---

## 7. Catálogo de productos

### Archivo utilizado

`product_catalog.xlsx`

### Relevancia para el sistema

El catálogo de productos permite responder preguntas sobre características, materiales, ingredientes, certificaciones, usos y sostenibilidad de los productos vendidos por EcoMarket.

Este tipo de información es especialmente útil para RAG porque los clientes pueden formular preguntas de forma abierta o imprecisa. Por ejemplo:

- ¿Qué productos de limpieza sostenibles tienen?
- ¿Tienen cepillos de bambú?
- ¿Qué productos son orgánicos?
- ¿Qué opciones ecológicas tienen para higiene personal?

En estos casos, el usuario no necesariamente conoce el identificador del producto. Por eso, la recuperación semántica ayuda a encontrar productos relevantes aunque la consulta no coincida exactamente con el nombre registrado en el catálogo.

### Enfoque utilizado

Cada fila del catálogo se transforma en un documento textual. Esto permite preservar los atributos del producto y convertirlos en unidades recuperables por similitud semántica. A diferencia de una búsqueda exacta tradicional, el RAG permite relacionar consultas generales con productos potencialmente relevantes.

---

## 8. Pedidos

### Archivo utilizado

`orders_enhanced.json`

### Relevancia para el sistema

Los pedidos son una de las fuentes más importantes para un asistente de e-commerce. Permiten responder preguntas sobre estado de pedido, retrasos, fecha estimada de entrega, productos incluidos, método de envío y enlace de tracking.

En el MVP se usa un archivo JSON con pedidos de ejemplo. En una versión profesional, esta información debería venir de un Order Management System o de una base transaccional interna.

### Enfoque utilizado

La estrategia principal para pedidos es la búsqueda estructurada mediante `order_service.py`, usando el número de seguimiento. Esto evita que el estado de un pedido sea inferido mediante similitud semántica.

El RAG se utiliza como capa secundaria de enriquecimiento. Puede aportar contexto adicional cuando la pregunta no contiene un número exacto de tracking o cuando se quiere complementar la respuesta con información de políticas de envío o patrones de demora.

### Consideración de privacidad

En una implementación real, los pedidos pueden contener datos sensibles: nombres, direcciones, teléfonos, medios de pago o historial de compras. Por eso, una solución profesional debería aplicar controles de privacidad, anonimización, minimización de datos en prompts y políticas claras de retención de logs.

En el MVP académico, los pedidos son datos de ejemplo y no contienen información personal real. Esta decisión permite demostrar la lógica del sistema sin exponer datos sensibles.


---

## 9. Diferencia entre documentos estructurados y no estructurados

Un aspecto importante de la solución es que no todos los documentos se tratan igual.

Los documentos no estructurados, como políticas en PDF, se benefician directamente del RAG porque contienen texto largo, reglas, cláusulas y explicaciones. En estos casos, la segmentación y recuperación semántica permiten extraer las partes relevantes sin enviar todo el documento al modelo.

Los documentos estructurados, como inventario, catálogo y pedidos, tienen registros compactos y con campos definidos. En estos casos, el sistema debe preservar cada registro como una unidad completa. Dividir una fila de inventario o un pedido en varios fragmentos sería perjudicial, porque separaría campos que deben interpretarse juntos.

| Tipo de fuente | Ejemplos | Tratamiento principal |
|---|---|---|
| No estructurada | Políticas PDF | Chunking semántico y recuperación RAG |
| Semi-estructurada | Ejemplos de soporte JSON | Indexación como texto conversacional |
| Estructurada | Inventario, catálogo, pedidos | Registro completo como unidad atómica + lookup estructurado |

Esta decisión es clave para evitar que el sistema recupere información incompleta. Por ejemplo, no sería deseable que el nombre de un producto quedara en un chunk y su fecha de expiración en otro.

---

## 10. Pipeline de carga de documentos

La carga de documentos se implementa en el módulo:

```text
src/rag/document_loader.py
```

El objetivo de este módulo es convertir diferentes formatos de archivo en objetos `Document` de LangChain, manteniendo tanto el contenido textual como la metadata relevante.

### 10.1 Carga de PDFs

Los documentos PDF se cargan usando `pypdf`. Cada página se convierte en un documento independiente.

Esta estrategia conserva la referencia a la página original, lo cual sería útil en una versión profesional para trazabilidad, auditoría o citación de fuentes.

### 10.2 Carga de Excel

Los archivos Excel se cargan con `pandas`. Cada fila se transforma en un documento textual con formato de pares clave-valor.

Convertir todos los valores a texto evita errores con fechas, números o campos vacíos, y permite que el contenido sea compatible con el modelo de embeddings.

### 10.3 Carga de JSON

Los archivos JSON se cargan registro por registro. Cada pedido o ejemplo de soporte se serializa como texto legible antes de ser indexado.

Esta estrategia permite que información estructurada sea recuperable por similitud semántica, sin perder su organización original.

---

## 11. Preservación de metadata

Cada documento cargado conserva metadata básica y, cuando aplica, metadata específica del dominio. Esto es importante porque la metadata permite filtrar resultados, explicar de dónde salió una respuesta y depurar el comportamiento del sistema.

Ejemplos de metadata utilizada:

```text
source
doc_type
page
product_id
tracking_number
intent
```

La metadata permite responder preguntas como:

- ¿De qué archivo proviene este fragmento?
- ¿Este resultado pertenece a política de envíos o devoluciones?
- ¿Qué producto o pedido está asociado al documento recuperado?
- ¿Qué tipo de intención cubre este ejemplo de soporte?

En el MVP académico, esta metadata se usa principalmente para organización y depuración. En una visión profesional, sería relevante para trazabilidad, auditoría, filtros por permisos, control de versiones y explicación de respuestas.

---

## 12. Estrategia de segmentación o chunking

La segmentación de documentos es una decisión crítica en cualquier sistema RAG. Si los chunks son demasiado grandes, pueden mezclar temas distintos y reducir la precisión de la recuperación. Si son demasiado pequeños, pueden perder contexto y generar respuestas incompletas.

En este proyecto se utilizó:

```python
RecursiveCharacterTextSplitter(
    chunk_size=391,
    chunk_overlap=45,
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

La estrategia seleccionada fue el splitter recursivo de LangChain porque intenta dividir el texto respetando primero separaciones naturales:

1. Párrafos (`\n\n`)
2. Saltos de línea (`\n`)
3. Oraciones (`. `)
4. Palabras (` `)
5. Caracteres, solo como último recurso

Esto es especialmente útil para documentos de políticas, donde las cláusulas suelen estar separadas por saltos de línea o numeración.

---

## 13. Justificación empírica del chunking

Los parámetros `chunk_size=391` y `chunk_overlap=45` se derivaron de un análisis exploratorio sobre los archivos reales de la base de conocimiento. El lector puede revisar el razonamiento detallado, las distribuciones por fuente y la evaluación de candidatos en [`docs/eda_chunking_analysis.md`](eda_chunking_analysis.md).

En resumen, el criterio principal fue **preservar la integridad de los registros estructurados**: el pedido más largo mide 341 caracteres, por lo que cualquier `chunk_size` menor habría partido registros a la mitad. Se añadió un margen de seguridad de 50 caracteres:

```text
chunk_size = 341 + 50 = 391
```

El overlap de 45 caracteres (~12% del chunk) mantiene continuidad entre fragmentos consecutivos de los PDFs, sin afectar a las fuentes estructuradas, que nunca se dividen.

El resultado final fue un corpus de **445 chunks** a partir de 433 documentos crudos — únicamente los PDFs de políticas fueron segmentados; inventario, catálogo y pedidos permanecieron intactos.

---

## 14. Proceso de indexación

El proceso de indexación se implementa en:

```text
src/rag/rag_pipeline.py
```

Este módulo coordina el flujo completo de construcción o carga de la base vectorial.

El proceso puede resumirse en seis pasos:

1. Cargar los documentos desde PDF, Excel y JSON.
2. Convertirlos en objetos `Document` de LangChain.
3. Dividir los documentos largos en chunks.
4. Generar embeddings con `sentence-transformers/all-MiniLM-L6-v2`.
5. Construir el índice vectorial con FAISS.
6. Guardar el índice en disco para reutilizarlo en futuras ejecuciones.

En forma de flujo:

```text
Archivos en data/
        ↓
document_loader.py
        ↓
LangChain Documents
        ↓
RecursiveCharacterTextSplitter
        ↓
Chunks
        ↓
HuggingFaceEmbeddings
        ↓
Vectores
        ↓
FAISS
        ↓
vectorstore/faiss_index/
```

---

## 15. Persistencia y reconstrucción del índice

Una vez construido el índice FAISS, este se guarda localmente en:

```text
vectorstore/faiss_index/
```

Esto evita recalcular los embeddings cada vez que se inicia la aplicación. En la primera ejecución, el sistema construye el índice. En ejecuciones posteriores, simplemente lo carga desde disco.

Si se actualizan los documentos de la carpeta `data/`, el índice debe reconstruirse. Esto puede hacerse de dos formas:

1. Eliminando manualmente la carpeta `vectorstore/`.
2. Ejecutando el pipeline con un parámetro como `force_rebuild=True`.

Esta estrategia es suficiente para el MVP académico. En una implementación profesional, sería preferible contar con actualizaciones incrementales, control de versiones de documentos y monitoreo de cambios en la base de conocimiento.

---

## 16. Relación entre RAG y lookup estructurado

Una decisión importante de diseño es que el RAG no reemplaza todas las búsquedas del sistema. Para información operativa crítica, como pedidos e inventario, se usa búsqueda estructurada cuando existe un identificador claro.

Por ejemplo:

- Si el usuario pregunta por `ECO20105`, el sistema consulta `orders_enhanced.json` usando el tracking number.
- Si el usuario pregunta por `P0001`, el sistema consulta el inventario por `product_id`.
- Si el usuario pregunta por políticas o características generales, el sistema usa RAG.

Esta combinación reduce el riesgo de respuestas incorrectas. El RAG es muy útil para preguntas abiertas y documentos textuales; la búsqueda estructurada es más confiable para datos exactos.

| Tipo de pregunta | Mejor mecanismo |
|---|---|
| Estado de un pedido con tracking number | Lookup estructurado |
| Stock de un producto con ID | Lookup estructurado |
| Política de devolución | RAG |
| Política de envío | RAG |
| Preguntas generales de producto | RAG + catálogo |
| Casos de queja o frustración | Escalamiento humano |

Esta decisión mantiene coherencia con la arquitectura del Taller 1: el LLM redacta, pero no debe inventar información operativa.

---

## 17. Por qué estos documentos cubren el caso de EcoMarket

La selección de documentos responde directamente a las necesidades del caso de estudio. EcoMarket recibe consultas repetitivas sobre pedidos, devoluciones y características de productos, además de consultas más generales sobre envíos, disponibilidad y soporte.

| Documento | Preguntas que permite responder |
|---|---|
| Política de devoluciones | ¿Puedo devolver este producto? ¿Cuál es el plazo? ¿Qué pasa si está abierto? |
| Política de envíos | ¿Cuánto tarda el envío? ¿Hay envío internacional? ¿Qué pasa si se retrasa? |
| Inventario | ¿Hay stock? ¿Es perecedero? ¿Cuándo vence? ¿En qué bodega está? |
| Catálogo | ¿Qué características tiene? ¿Es orgánico? ¿Es sostenible? |
| Pedidos | ¿Dónde está mi pedido? ¿Está retrasado? ¿Qué productos incluía? |
| Ejemplos de soporte | ¿Cómo debe responder el asistente? ¿Qué tono debe usar? |

En conjunto, estas fuentes cubren una parte significativa de las consultas repetitivas que motivaron la solución inicial para EcoMarket.

---


## 18. Conclusión

La base de conocimiento del sistema RAG de EcoMarket fue diseñada para cubrir las principales necesidades de atención al cliente en un e-commerce sostenible: devoluciones, envíos, inventario, catálogo, pedidos y estilo de soporte.

La selección de documentos no fue arbitraria. Cada fuente cumple un rol específico dentro de la arquitectura: las políticas proporcionan reglas oficiales, el inventario y los pedidos aportan datos operativos, el catálogo permite responder preguntas de producto y los ejemplos de soporte orientan el tono del asistente.

La estrategia de chunking también fue definida de forma empírica. El análisis exploratorio mostró que los registros estructurados debían conservarse completos y que solo los PDFs requerían división. Por eso se seleccionó `chunk_size=391` y `chunk_overlap=45`, una configuración que preserva registros atómicos y permite dividir políticas en fragmentos útiles para recuperación.

En síntesis, esta fase demuestra cómo convertir archivos empresariales en una base de conocimiento recuperable por un sistema RAG. El resultado no es únicamente una colección de documentos, sino una estructura organizada que permite al asistente consultar información relevante antes de responder, reduciendo alucinaciones y manteniendo coherencia con las fuentes de verdad de EcoMarket.
