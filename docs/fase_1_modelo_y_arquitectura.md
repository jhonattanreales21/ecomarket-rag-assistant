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
| **LLM de propósito general** (ej. GPT-4 vía API) | Modelo grande, sin adaptación, usado tal cual | Alto costo por volumen, dependencia de proveedor externo, riesgo de privacidad al enviar datos del cliente |
| **LLM fine-tuned** | Modelo reentrenado con datos propios de EcoMarket | Requiere datos etiquetados, tiempo de entrenamiento y costos de infraestructura elevados para un prototipo |
| **Solución híbrida con few-shot prompting** ✅ | Modelo open-source guiado por ejemplos y conectado a fuentes de datos estructuradas | Equilibrio adecuado entre costo, flexibilidad y calidad para el contexto del problema |

Se elige la **solución híbrida**, que se define así en este contexto:

> Una arquitectura donde el modelo de lenguaje **no actúa solo**, sino que se combina
> con (1) datos estructurados como fuente de verdad operativa, y (2) ejemplos de
> conversación (few-shot prompting) que guían el tono y el comportamiento del modelo,
> sin necesidad de reentrenarlo.

### 2.3 Modelo seleccionado para el prototipo

Se eligió **Gemma 2B** como modelo de lenguaje open-source, ejecutado localmente
mediante Ollama. Sus componentes en la solución híbrida para esta etapa inicial del proyecto son:

- **Gemma 2B** → genera las respuestas en lenguaje natural
- **Módulo de datos estructurados** → provee la verdad operativa (estado de pedidos)
- **Documento de política de devoluciones** → provee las reglas de negocio
- **Biblioteca de ejemplos few-shot** → define el tono, estilo y estructura esperados
- **Router de intención** → clasifica la consulta antes de construir el prompt
- **Mecanismo de escalamiento** → deriva a un agente humano cuando es necesario

#### ¿Por qué Gemma 2B y no un modelo más robusto?

La elección no responde únicamente al tamaño del modelo o sus capacidades, sino al **reparto de responsabilidades** dentro de la solucion propuesta.

El sistema afrontaría las siguientes necesidades:

| Tipo de consulta | Qué exige del modelo | Cómo se resuelve en esta arquitectura |
|---|---|---|
| **Estado de pedido** | Alta precisión — ningún dato puede inventarse | La precisión la aporta la base de datos estructurada, **no el LLM**. El modelo solo redacta la respuesta a partir de datos ya recuperados. |
| **Política de devoluciones** | Fidelidad a las reglas de negocio | Las reglas se inyectan en el prompt. El modelo las parafrasea, no las genera. |
| **Preguntas generales / empatía** | Fluidez y naturalidad conversacional | Aquí sí actúa el LLM de manera autónoma, guiado por ejemplos few-shot que definen el tono esperado. |

Dado este reparto, un modelo más grande (7B, 13B o superior) aportaría poco en precisión y añadiría costos de infraestructura incompatibles con el contexto de un prototipo (MVP) para EcoMarket. Gemma 2B es suficiente porque su único rol crítico es **redactar con naturalidad**, no memorizar hechos operativos.

Además, las limitaciones tecnicas de Gemma 2B (vocabulario reducido, contexto menor que modelos grandes) no representan un problema aquí porque:

1. El dominio es acotado: comercio electrónico de productos sostenibles, no conocimiento enciclopédico.
2. Cada respuesta se construye sobre un prompt que ya contiene todos los datos relevantes.
3. Los ejemplos few-shot compensan la falta de afinamiento, guiando tono y estructura.
4. La temperatura se podria fijar en 0 para maximizar la determinismo y evitar divagaciones.
5. Ante posibles preguntas por fuera del contexto del comercio, se podria definir una respuesta para el usuario recordandole el objetivo del canal de soporte.

Para preguntas generales dentro del contexto del soporte (por ejemplo, *"¿cómo sé si mi devolución fue aceptada?"*), el modelo es capaz de articular respuestas coherentes y empáticas apoyado en el prompt y los ejemplos. No se le pide que resuelva razonamiento complejo ni que genere contenido fuera del dominio.

#### Modelos alternativos comparables

En caso de necesitar escalar o sustituir el componente generativo, los siguientes modelos open-source presentan perfil similar en tamaño, licencia y desempeño conversacional:

| Modelo | Parámetros | Organización | Ventaja principal frente a Gemma 2B |
|---|---|---|---|
| **Phi-3 Mini** | 3.8B | Microsoft | Mayor razonamiento lógico por parámetro; excelente para instrucciones estructuradas |
| **LLaMA 3.2 3B** | 3B | Meta | Mejor fluidez en español; comunidad amplia y soporte activo |
| **Qwen2.5 1.5B / 3B** | 1.5–3B | Alibaba | Fuerte en contextos multilingües y textos cortos tipo soporte |
| **Mistral 7B Instruct** | 7B | Mistral AI | Respuestas notablemente más fluidas; viable si se dispone de recursos de computo decentes |
| **Phi-2** | 2.7B | Microsoft | Tamaño similar, buen desempeño en tareas de comprensión y seguimiento de instrucciones |

Todos ellos son compatibles con Ollama y podrían integrarse en esta arquitectura sin modificar la lógica del router, los prompts ni los módulos de datos.

## 3. Arquitectura propuesta

La arquitectura de la solución se diseñó para separar claramente la **verdad operativa** de la **capa conversacional**.

### Componentes principales

1. **Interfaz de usuario**
   - Se implementó una interfaz conversacional en Streamlit para interactuar con el asistente.

2. **Router de intención**
   - Detecta si la consulta corresponde a:
     - Estado de pedido.
     - Devoluciones.
     - Soporte general.
     - Escalamiento humano.

3. **Módulo de pedidos**
   - Consulta un archivo estructurado con el estado de pedidos de ejemplo.
   - Esta capa evita que el modelo invente información sensible.

4. **Módulo de devoluciones**
   - Usa un documento de política de devoluciones como base para responder.
   - El modelo formula la respuesta, pero la política sigue siendo la fuente principal.

5. **Biblioteca de ejemplos**
   - Contiene ejemplos tipo cliente-agente para distintos escenarios.
   - Se usa como few-shot prompting para enseñar tono y comportamiento.

6. **Modelo generativo**
   - Gemma 2B genera la respuesta final a partir del prompt, los ejemplos y los datos de contexto.

7. **Escalamiento a humano**
   - Si la consulta implica queja, frustración o un caso sensible, el sistema recomienda transferir la atención a un agente humano.

## . Justificación del modelo elegido

La elección de Gemma 2B se justifica por cuatro razones principales:

### a. Costo
Al ser un modelo open-source, no requiere el pago por uso de una API comercial. Esto lo convierte en una alternativa apropiada para un prototipo académico y para una empresa que busque explorar soluciones de automatización con bajo costo inicial.

### b. Escalabilidad
Aunque Gemma 2B no es el modelo más grande del mercado, sí permite construir una primera versión funcional de la solución. La arquitectura propuesta además es escalable, ya que en el futuro el modelo puede ser reemplazado por uno más potente sin cambiar la lógica general del sistema.

### c. Facilidad de integración
Gemma 2B puede integrarse fácilmente con una aplicación local a través de Ollama. Esto permitió conectarlo con una interfaz en Streamlit, con datos estructurados de pedidos y con documentos internos como la política de devoluciones.

### d. Calidad esperada de respuesta
Para este caso no se necesita que el modelo “adivine” información crítica como el estado del pedido. La fuente de verdad para esos casos es una base de datos estructurada. El modelo se utiliza principalmente para redactar respuestas claras, empáticas y naturales a partir de datos ya recuperados. Esto reduce el riesgo de error y aprovecha la fortaleza principal del LLM: la generación de lenguaje natural.

## 5. ¿Por qué esta arquitectura y no otra?

### No se eligió un LLM puro
Un LLM por sí solo no es suficiente para responder con precisión preguntas operativas como el estado de un pedido, porque puede alucinar o inventar información.

### No se eligió una solución completamente basada en reglas
Una solución puramente basada en reglas sería rígida, difícil de escalar y poco natural en la interacción con el cliente.

### Se eligió una solución híbrida
La solución híbrida aprovecha lo mejor de ambos mundos:
- precisión operativa mediante datos estructurados,
- flexibilidad lingüística mediante IA generativa.

## 6. Relación con las necesidades del negocio

La solución propuesta responde de forma directa al problema descrito en el caso:

- Atiende el **80% de consultas repetitivas** con automatización.
- Reduce el tiempo de respuesta.
- Mejora la disponibilidad del servicio.
- Conserva un canal humano para el **20% de casos complejos**. 

Además, permite construir una experiencia de soporte más consistente, más rápida y potencialmente disponible 24/7.

## 7. Conclusión

La solución más adecuada para EcoMarket es una arquitectura híbrida basada en un modelo open-source, concretamente Gemma 2B, complementado con datos estructurados, prompts con ejemplos y escalamiento humano.

Esta elección ofrece un buen equilibrio entre costo, escalabilidad, facilidad de integración y calidad de respuesta. Más importante aún, evita delegar en el modelo tareas críticas que deben permanecer ancladas a fuentes confiables, como el estado del pedido o las restricciones de devolución.

En conclusión, la propuesta no busca reemplazar completamente al equipo humano, sino automatizar de manera inteligente las consultas repetitivas y liberar a los agentes para los casos donde el juicio y la empatía siguen siendo indispensables.