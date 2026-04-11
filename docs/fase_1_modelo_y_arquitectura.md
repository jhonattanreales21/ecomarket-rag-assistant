# Fase 1: Selección y justificación del modelo de IA

## 1. Contexto del problema

EcoMarket es una empresa de comercio electrónico enfocada en productos sostenibles que enfrenta un cuello de botella en su servicio de atención al cliente. La empresa recibe miles de consultas diarias por distintos canales, y aproximadamente el 80% de esas consultas corresponden a solicitudes repetitivas como estado del pedido, devoluciones y preguntas sobre productos. El 20% restante corresponde a casos más complejos que requieren empatía, criterio humano y manejo especial. Actualmente, el tiempo promedio de respuesta es de 24 horas, lo que afecta negativamente la satisfacción del cliente. :contentReference[oaicite:1]{index=1}

## 2. Modelo propuesto

Se propone una **solución híbrida de IA generativa** compuesta por los siguientes elementos:

- Un **modelo de lenguaje open-source** para la generación de respuestas en lenguaje natural.
- Un módulo de **datos estructurados** para consultas críticas como el estado de los pedidos.
- Un conjunto de **prompts con ejemplos (few-shot prompting)** para enseñar al modelo el tono, la estructura y el estilo de respuesta esperados.
- Un sistema de **clasificación de intención** para distinguir entre consultas de pedidos, devoluciones, soporte general y casos que deben escalarse a un humano.
- Un mecanismo de **escalamiento a agente humano** cuando la solicitud del cliente supera las capacidades del sistema automático.

Para el prototipo se eligió **Gemma 2B**, ejecutado localmente mediante Ollama, como modelo open-source de generación.

## 3. Justificación del modelo elegido

La elección de Gemma 2B se justifica por cuatro razones principales:

### a. Costo
Al ser un modelo open-source, no requiere el pago por uso de una API comercial. Esto lo convierte en una alternativa apropiada para un prototipo académico y para una empresa que busque explorar soluciones de automatización con bajo costo inicial.

### b. Escalabilidad
Aunque Gemma 2B no es el modelo más grande del mercado, sí permite construir una primera versión funcional de la solución. La arquitectura propuesta además es escalable, ya que en el futuro el modelo puede ser reemplazado por uno más potente sin cambiar la lógica general del sistema.

### c. Facilidad de integración
Gemma 2B puede integrarse fácilmente con una aplicación local a través de Ollama. Esto permitió conectarlo con una interfaz en Streamlit, con datos estructurados de pedidos y con documentos internos como la política de devoluciones.

### d. Calidad esperada de respuesta
Para este caso no se necesita que el modelo “adivine” información crítica como el estado del pedido. La fuente de verdad para esos casos es una base de datos estructurada. El modelo se utiliza principalmente para redactar respuestas claras, empáticas y naturales a partir de datos ya recuperados. Esto reduce el riesgo de error y aprovecha la fortaleza principal del LLM: la generación de lenguaje natural.

## 4. Arquitectura propuesta

La arquitectura de la solución se diseñó para separar claramente la **verdad operativa** de la **capa conversacional**.

### Componentes principales

1. **Interfaz de usuario**
   - Se implementó una interfaz conversacional en Streamlit para interactuar con el asistente.

2. **Router de intención**
   - Detecta si la consulta corresponde a:
     - estado de pedido,
     - devoluciones,
     - soporte general,
     - o escalamiento humano.

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
- Conserva un canal humano para el **20% de casos complejos**. :contentReference[oaicite:2]{index=2}

Además, permite construir una experiencia de soporte más consistente, más rápida y potencialmente disponible 24/7.

## 7. Conclusión

La solución más adecuada para EcoMarket es una arquitectura híbrida basada en un modelo open-source, concretamente Gemma 2B, complementado con datos estructurados, prompts con ejemplos y escalamiento humano.

Esta elección ofrece un buen equilibrio entre costo, escalabilidad, facilidad de integración y calidad de respuesta. Más importante aún, evita delegar en el modelo tareas críticas que deben permanecer ancladas a fuentes confiables, como el estado del pedido o las restricciones de devolución.

En conclusión, la propuesta no busca reemplazar completamente al equipo humano, sino automatizar de manera inteligente las consultas repetitivas y liberar a los agentes para los casos donde el juicio y la empatía siguen siendo indispensables.