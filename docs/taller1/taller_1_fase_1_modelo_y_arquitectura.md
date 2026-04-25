# Fase 1: Selección y justificación del modelo de IA

## 1. Contexto del problema

EcoMarket es una empresa de comercio electrónico enfocada en productos sostenibles que enfrenta un cuello de botella en su servicio de atención al cliente. La empresa recibe miles de consultas diarias por distintos canales, y aproximadamente el 80% de esas consultas corresponden a solicitudes repetitivas como estado del pedido, devoluciones y preguntas sobre productos. El 20% restante corresponde a casos más complejos que requieren empatía, criterio humano y manejo especial. Actualmente, el tiempo promedio de respuesta es de 24 horas, lo que afecta negativamente la satisfacción del cliente.

## 2. Modelo propuesto

### 2.1 ¿Por qué un modelo de lenguaje y no otro tipo de IA generativa?

La IA generativa abarca múltiples paradigmas: modelos de difusión para imágenes,
modelos de síntesis de audio, modelos de código, y modelos de lenguaje, entre otros.
Para el problema de EcoMarket, la tarea central es **comprender texto escrito por un
cliente y generar una respuesta en lenguaje natural**. Esto delimita el problema al
dominio de los **modelos de lenguaje (LLM)**, que son la herramienta adecuada cuando
la entrada y la salida son texto conversacional.

### 2.2 ¿Qué tipo de modelo de lenguaje es el más adecuado?

Dentro de los modelos de lenguaje, existen tres enfoques principales para este caso:

| Opción | Descripción | Por qué se descarta |
|---|---|---|
| **LLM de propósito general** (ej. GPT-4 vía API) | Modelo grande, sin adaptación, consumido como servicio externo | Alto costo por volumen, dependencia de proveedor externo, riesgo de privacidad al enviar datos del cliente |
| **LLM fine-tuned** | Modelo reentrenado con datos propios de EcoMarket | Requiere datos etiquetados, infraestructura de entrenamiento costosa y ciclos largos de iteración; poco viable para un prototipo y difícil de mantener ante cambios de política |
| **Solución híbrida con few-shot prompting** ✅ | Modelo open-source guiado por ejemplos y conectado a fuentes de datos estructuradas | Equilibrio adecuado entre costo, privacidad, flexibilidad y calidad para el volumen y contexto del problema |

Se elige la **solución híbrida** y se rechaza explícitamente el fine-tuning como estrategia de adaptación. El few-shot prompting permite iterar el comportamiento del modelo modificando únicamente los ejemplos en el prompt, sin reentrenar, sin pipelines de datos y sin interrupciones del servicio. Para un dominio acotado como el soporte de e-commerce, esta flexibilidad supera con creces el costo adicional del fine-tuning.:

> **Definición operativa de la solución híbrida en este contexto:**
> Una arquitectura donde el LLM *no actúa solo*, sino combinado con: (1) fuentes de
> datos estructuradas como verdad operativa, (2) un módulo de conocimiento con
> documentos internos, y (3) ejemplos few-shot que guían tono y comportamiento, todo
> orquestado por un router de intención.

### 2.3 Modelo generativo seleccionado: Gemma 2B

#### Justificación por reparto de responsabilidades

La elección del modelo no depende únicamente de su tamaño o benchmarks generales,
sino del **rol específico que cumple dentro de la arquitectura**. La siguiente tabla
describe qué exige cada tipo de consulta y cómo lo resuelve el sistema:

| Tipo de consulta | Qué exige del sistema | Cómo se resuelve |
|---|---|---|
| Estado de pedido | Alta precisión — ningún dato puede inventarse | La precisión la aporta el módulo de datos estructurados. El LLM solo redacta a partir de datos ya recuperados. |
| Política de devoluciones | Fidelidad a las reglas de negocio | Las reglas se inyectan en el prompt. El modelo las parafrasea, no las genera. |
| Preguntas generales y empatía | Fluidez y naturalidad conversacional | Aquí actúa el LLM de manera autónoma, guiado por ejemplos few-shot que definen tono y estructura. |

Dado este reparto, **un modelo más grande aportaría poco en precisión y añadiría costos
de infraestructura incompatibles con el prototipo**. Gemma 2B es suficiente porque su
único rol crítico es redactar con naturalidad, no memorizar hechos operativos.

Las limitaciones del modelo (contexto reducido, vocabulario acotado) no representan un
problema por las siguientes razones:

1. El dominio es acotado: soporte de e-commerce de productos sostenibles, no conocimiento enciclopédico.
2. Cada respuesta se construye sobre un prompt que ya contiene todos los datos relevantes.
3. Los ejemplos few-shot compensan la ausencia de fine-tuning, guiando tono y estructura.
4. La temperatura puede fijarse en `0` para maximizar el determinismo y evitar divagaciones.
5. Las consultas fuera del dominio se interceptan con una respuesta predefinida que recuerda al usuario el propósito del canal.

#### Modelos alternativos comparables

En caso de necesitar escalar o sustituir el componente generativo, los siguientes modelos open-source presentan perfil similar en tamaño, licencia y desempeño conversacional:

| Modelo | Parámetros | Organización | Ventaja frente a Gemma 2B |
|---|---|---|---|
| **Phi-3 Mini** | 3.8B | Microsoft | Mayor razonamiento lógico; excelente para instrucciones estructuradas |
| **LLaMA 3.2 3B** | 3B | Meta | Mejor fluidez en español; comunidad activa y amplio soporte |
| **Qwen2.5 1.5B / 3B** | 1.5–3B | Alibaba | Fuerte en contextos multilingües y textos cortos tipo soporte |
| **Mistral 7B Instruct** | 7B | Mistral AI | Respuestas notablemente más fluidas; viable con recursos de cómputo decentes |
| **Phi-2** | 2.7B | Microsoft | Tamaño similar; buen desempeño en comprensión y seguimiento de instrucciones |

Todos ellos son compatibles con Ollama y podrían integrarse en esta arquitectura sin modificar la lógica del router, los prompts ni los módulos de datos.

## 3. Arquitectura propuesta

La arquitectura de la solución se diseñó bajo un principio central: **separar la
verdad operativa de la capa conversacional**. El modelo de lenguaje no es la fuente
de los datos — es el redactor que los transforma en respuestas naturales. Esta
distinción determina la estructura de todos los componentes.

La solución no es un LLM de propósito general usado directamente, ni un modelo
afinado con datos de EcoMarket. Es una **arquitectura híbrida orquestada**, donde
el modelo generativo actúa como el último eslabón de una cadena que primero
clasifica la consulta, luego recupera la información necesaria, y finalmente
construye el prompt que el modelo recibe. A continuación se describe cada capa,
distinguiendo entre la visión profesional y el MVP académico construido para este
taller.

---

### 3.1 Visión profesional de la arquitectura

En una implementación de producción, la arquitectura se organiza en cuatro capas
funcionales:

#### Capa 1 — Router de intención

Toda consulta entrante pasa primero por un clasificador de intención que determina
a qué módulo debe dirigirse antes de construir cualquier prompt. Las categorías
principales son: consulta operativa (pedidos, reembolsos, inventario), consulta de
conocimiento (políticas, características de producto, FAQs) y caso complejo
(quejas, situaciones que requieren empatía o criterio humano).

#### Capa 2 — Módulos de recuperación de información

Según la clasificación recibida, se activan uno o más módulos en paralelo:

- **Módulo operativo**: conectado a los sistemas internos de EcoMarket (CRM, Order Management Systems,
   catálogo de productos, etc) para recuperar en tiempo real datos como estado de
   pedidos, historial de compras, estado de reembolsos, disponibilidad de inventario
   y facturas. Esta capa garantiza que ningún dato operativo sea generado por el LLM.

- **Módulo de conocimiento con RAG**: los documentos internos de EcoMarket
   (políticas, FAQs, fichas técnicas de producto) se indexan semánticamente en una
   base de vectores. Ante cada consulta, se recuperan únicamente los fragmentos más
   relevantes, en lugar de inyectar documentos completos en el prompt. Esto permite
   escalar el repositorio de conocimiento sin incrementar el costo de inferencia.

#### Capa 3 — Constructor de prompt

Con los datos recuperados, el constructor ensambla dinámicamente el prompt final,
incorporando: los datos operativos o fragmentos de conocimiento relevantes, el
historial conversacional (memoria de sesión) y los ejemplos few-shot que definen
el tono, el estilo y la estructura esperada en la respuesta.

#### Capa 4 — LLM generativo con memoria conversacional

El modelo recibe el prompt ensamblado y genera la respuesta en lenguaje natural.
La memoria conversacional permite mantener el contexto entre turnos de la misma
sesión, resolviendo una limitación inherente de los LLMs puros. La salida se
entrega al cliente, o se escala a un agente humano si el router identificó un
caso complejo desde el inicio.

---

### 3.2 MVP académico

Para este taller se construye el núcleo funcional de la arquitectura anterior,
con simplificaciones que no comprometen su validez como prototipo:

| Componente | Visión profesional | MVP académico |
|---|---|---|
| Router de intención | Clasificador semántico sobre múltiples categorías | Lógica de clasificación por palabras clave y patrones |
| Módulo operativo | Integración en tiempo real con CRM / OMS | Archivo estructurado con 10+ pedidos de ejemplo |
| Módulo de conocimiento | RAG sobre repositorio indexado semánticamente | Política de devoluciones inyectada directamente en el prompt |
| Memoria conversacional | Gestión de sesión persistente entre canales | **TBD** |
| Canal de entrada | Chat, email, WhatsApp, redes sociales | Interfaz de chat única en Streamlit |
| Infraestructura | Servicios en la nube con alta disponibilidad | Ejecución local con Ollama |
| Modelo generativo | LLM de mayor capacidad según demanda | Gemma 2B ejecutado localmente |

Las simplificaciones permiten demostrar el corazón de la solución  (la clasificación
de intención, la recuperación de datos, la construcción dinámica del prompt y la
generación de respuestas naturales) sin la complejidad de las integraciones
productivas. 

Por lo tanto, el MVP **implementa la lógica central de la arquitectura**
con datos y modelos de menor escala.

---

### 3.3 Integración con datos de EcoMarket

La solución no se afina con datos de la empresa ni depende de un modelo de
propósito general usado directamente. En cambio, la adaptación al dominio de
EcoMarket se logra por dos vías complementarias:

- **Datos estructurados como fuente de verdad**: la información operativa
  (pedidos, reembolsos, inventario) se recupera de los sistemas de la empresa
  y se entrega al modelo ya procesada. El LLM no infiere ni inventa estos datos.

- **Few-shot prompting como mecanismo de adaptación**: en lugar de reentrenar el
  modelo, se incluyen en cada prompt ejemplos de conversaciones cliente-agente
  que definen el tono, el nivel de formalidad y la estructura de respuesta
  esperada. Esto permite ajustar el comportamiento del modelo modificando
  únicamente los ejemplos, sin ciclos de entrenamiento ni infraestructura adicional.
## 4. Justificación de la solución propuesta

Esta sección argumenta la elección de la arquitectura híbrida y del modelo generativo
seleccionado a partir de los criterios relevantes para una implementación real: costo,
escalabilidad, facilidad de integración y calidad de respuesta esperada. Se añaden
además criterios de privacidad y mantenibilidad, que resultan determinantes en un
sistema de soporte al cliente con datos sensibles.

---

### 4.1 Costo

El uso de un modelo open-source como Gemma 2B elimina el costo por llamada a una API
comercial, que a escala de miles de consultas diarias representaría un gasto operativo
significativo. La ejecución local mediante Ollama no requiere infraestructura de nube
dedicada en la fase de prototipo, lo que reduce la barrera de entrada para EcoMarket.

En la visión profesional, el costo de infraestructura escala de forma predecible:
al no depender de un proveedor externo por volumen, la empresa mantiene control
sobre su estructura de costos a medida que crece la demanda. El few-shot prompting
refuerza esta ventaja: adaptar el comportamiento del modelo no requiere ciclos de
reentrenamiento ni equipos de MLOps, lo que reduce el costo de mantenimiento a
largo plazo frente a una solución basada en fine-tuning.

---

### 4.2 Escalabilidad

La arquitectura está diseñada para escalar en dos dimensiones independientes:

- **Escalabilidad del conocimiento**: en la visión profesional, el módulo RAG permite
  incorporar nuevos documentos (políticas actualizadas, nuevas FAQs, fichas de
  producto) sin modificar el código ni el modelo. El repositorio de conocimiento
  crece sin impactar el tamaño del prompt ni el costo de inferencia.

- **Escalabilidad del componente generativo**: dado que el LLM es un módulo
  intercambiable dentro de la arquitectura, puede reemplazarse por un modelo más
  potente (Mistral 7B, LLaMA 3, u otro compatible con Ollama) sin modificar la
  lógica del router, los módulos de datos ni los prompts. El MVP ya está diseñado
  con esta separación de responsabilidades.

---

### 4.3 Privacidad y control de datos

Este criterio justifica de forma determinante el rechazo a soluciones basadas en APIs
comerciales externas. En el soporte al cliente de EcoMarket circula información
sensible: nombres, direcciones, historial de compras, estados de reembolso. Enviar
esta información a un proveedor externo introduce riesgos legales y de cumplimiento
normativo (GDPR, legislaciones locales de protección de datos) que una empresa en
crecimiento debe considerar desde el inicio.

La ejecución local del modelo garantiza que los datos del cliente nunca salen de la
infraestructura propia de EcoMarket, lo que simplifica el cumplimiento normativo y
genera mayor confianza en los usuarios.

---

### 4.4 Facilidad de integración

La combinación de Ollama, LangChain y Streamlit permite construir e iterar la solución
con herramientas de código abierto, ampliamente documentadas y con comunidades activas.
LangChain en particular simplifica tres aspectos críticos de la integración: la gestión
de prompts, la memoria conversacional y la orquestación entre módulos. Esto reduce el
tiempo de desarrollo y facilita la incorporación de nuevos componentes (como el módulo
RAG) en iteraciones futuras sin reescribir la lógica base.

En la visión profesional, la misma arquitectura puede integrarse con los sistemas
internos de EcoMarket (CRM, OMS) mediante conectores estándar, sin cambiar la capa
de orquestación.

---

### 4.5 Calidad de respuesta esperada

La calidad en este sistema no depende exclusivamente del tamaño del modelo, sino del
**reparto de responsabilidades** dentro de la arquitectura:

- La **precisión** en respuestas operativas (estado de pedido, reembolsos) la garantiza
  la fuente de datos estructurada, no el LLM. El modelo nunca infiere ni inventa
  información crítica.
- La **fidelidad a las políticas** de la empresa la garantiza el módulo de conocimiento,
  que inyecta las reglas directamente en el prompt.
- La **fluidez y naturalidad** conversacional es la única responsabilidad exclusiva del
  LLM, y es donde Gemma 2B demuestra ser suficiente para el dominio acotado del
  soporte de e-commerce.

Este diseño reduce el riesgo de alucinaciones en los puntos más críticos del sistema,
al tiempo que aprovecha la fortaleza principal del modelo generativo: producir lenguaje
natural empático y coherente.

---

### 4.6 Mantenibilidad y adaptabilidad

Una solución de soporte al cliente está expuesta a cambios frecuentes: nuevas políticas
de devolución, actualizaciones del catálogo, cambios en el tono de comunicación de la
marca. La arquitectura propuesta permite absorber estos cambios de forma localizada:

- Cambios en políticas → se actualiza el documento fuente en el módulo de conocimiento.
- Cambios en tono o estilo → se actualizan los ejemplos few-shot en el prompt.
- Cambios en datos operativos → se actualiza la fuente de datos estructurada.

Ninguno de estos cambios requiere reentrenar el modelo ni modificar la arquitectura.
Esta separación entre lógica de negocio y componente generativo es una de las ventajas
estructurales más importantes de la solución híbrida frente al fine-tuning.

---

### 4.7 Relación directa con las necesidades del negocio

La solución responde de forma directa al problema descrito en el caso de EcoMarket:

| Necesidad del negocio | Cómo la resuelve la arquitectura propuesta |
|---|---|
| Reducir el tiempo de respuesta promedio de 24 horas | Automatización inmediata del 80% de consultas repetitivas |
| Manejar miles de consultas diarias | Arquitectura escalable con modelo local de bajo costo por inferencia |
| Mantener calidad y precisión en respuestas operativas | Fuente de verdad estructurada separada del LLM |
| Conservar el toque humano en casos complejos | Módulo de escalamiento a agente humano integrado en el router |
| Disponibilidad continua del servicio | Sistema automatizado operable 24/7 sin depender de turnos de agentes |
| Proteger los datos sensibles de los clientes | Ejecución local sin transmisión de datos a proveedores externos |

## 5. Conclusión


La solución propuesta para EcoMarket no es simplemente la elección de un modelo de
lenguaje: es el diseño de una arquitectura que asigna cada responsabilidad al
componente más adecuado para asumirla. La precisión operativa recae en los datos
estructurados; la fidelidad a las políticas de la empresa recae en el módulo de
conocimiento; la fluidez y naturalidad conversacional recae en el modelo generativo;
y el criterio ante situaciones complejas recae en el agente humano. Esta separación
es el argumento central que justifica la arquitectura híbrida sobre cualquier
alternativa de componente único.

Frente a las opciones evaluadas — un LLM de propósito general vía API y un modelo
fine-tuned — la solución híbrida con few-shot prompting demuestra ventajas concretas
en los criterios que importan para el contexto de EcoMarket: menor costo operativo,
control sobre los datos sensibles de los clientes, capacidad de adaptarse a cambios
del negocio sin reentrenamiento, y una arquitectura modular que puede escalar
gradualmente hacia una implementación de producción completa.

El MVP académico construido en este taller implementa el núcleo de esa arquitectura
con simplificaciones deliberadas y transparentes. No simula la solución: demuestra
su lógica central. La distancia entre el MVP y la visión profesional está definida
con claridad — RAG, integraciones con CRM y OMS, multicanal — y representa un
camino de evolución natural, no un rediseño.

Finalmente, la propuesta asume desde el inicio que la automatización inteligente y
la intervención humana no son opciones excluyentes. El objetivo no es reemplazar al
equipo de soporte de EcoMarket, sino redistribuir la carga: que el sistema asuma
el 80% de consultas repetitivas con consistencia y disponibilidad 24/7, y que los
agentes concentren su capacidad en el 20% de casos donde el juicio, la empatía y
la experiencia humana siguen siendo insustituibles.