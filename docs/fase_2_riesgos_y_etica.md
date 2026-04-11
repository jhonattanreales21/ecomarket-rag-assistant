# Fase 2: Evaluación de fortalezas, limitaciones y riesgos éticos

## 1. Introducción

Una vez definida la solución de IA generativa para EcoMarket, es necesario analizar críticamente sus beneficios, sus límites y los riesgos éticos asociados a su implementación. Esta evaluación es fundamental, ya que una solución técnicamente funcional no siempre es suficiente si no se consideran sus implicaciones operativas, humanas y sociales. El caso enfatiza precisamente la necesidad de examinar fortalezas, limitaciones, alucinaciones, sesgos, privacidad de datos e impacto laboral. :contentReference[oaicite:3]{index=3}

## 2. Fortalezas de la solución propuesta

### a. Reducción del tiempo de respuesta
La principal fortaleza del sistema es su capacidad para automatizar la atención de consultas repetitivas, que constituyen aproximadamente el 80% del volumen total. Esto puede reducir de forma importante el tiempo de respuesta frente al promedio actual de 24 horas. :contentReference[oaicite:4]{index=4}

### b. Disponibilidad continua
El asistente puede operar de manera constante, lo que permite ofrecer soporte fuera del horario laboral tradicional y mejorar la experiencia del cliente.

### c. Consistencia en las respuestas
Al utilizar una política explícita de devoluciones y datos estructurados para pedidos, el sistema puede responder de manera más uniforme que un proceso totalmente manual.

### d. Mejor uso del talento humano
Al automatizar preguntas frecuentes, los agentes humanos pueden concentrarse en casos complejos, sensibles o conflictivos, donde la empatía y el juicio son más importantes.

### e. Escalabilidad operativa
La arquitectura modular permite crecer en complejidad sin rehacer el sistema completo. Por ejemplo, se podría reemplazar el modelo generativo, ampliar la base de conocimiento o conectar una base de datos real de pedidos.

## 3. Limitaciones de la solución

### a. No reemplaza el juicio humano
El sistema no puede manejar adecuadamente todos los casos. Situaciones de enojo, reclamos delicados, errores logísticos complejos o clientes muy frustrados siguen requiriendo intervención humana.

### b. Dependencia de la calidad de los datos
Si la base de pedidos contiene información incorrecta o desactualizada, el sistema responderá incorrectamente, aunque el modelo esté funcionando bien. El LLM no corrige errores de la fuente.

### c. Capacidad limitada del modelo
Gemma 2B es adecuado para prototipos, pero no tiene el mismo nivel de capacidad que modelos más grandes. Esto puede afectar:
- la calidad del lenguaje,
- la precisión en casos ambiguos,
- y la capacidad de seguir instrucciones complejas.

### d. Rendimiento computacional
Al ejecutarse localmente en un equipo con recursos limitados, el tiempo de respuesta puede ser más alto de lo deseado. Esto reduce la experiencia del usuario y muestra una limitación práctica del despliegue local.

### e. Cobertura parcial del problema
El sistema actual cubre bien pedidos, devoluciones y soporte general, pero todavía no integra completamente:
- catálogo de productos,
- historial de compras,
- múltiples idiomas,
- o contexto multi-turno más sofisticado.

## 4. Riesgos éticos

## 4.1 Alucinaciones

Uno de los principales riesgos de un LLM es inventar información. En atención al cliente esto puede ser especialmente grave si el modelo responde incorrectamente sobre:
- el estado de un pedido,
- una fecha de entrega,
- una política de devolución,
- o una excepción que no existe.

### Mitigación
La arquitectura propuesta reduce este riesgo al separar:
- **datos estructurados** como fuente de verdad para pedidos,
- **política escrita** como fuente de verdad para devoluciones,
- y **modelo generativo** solo para redactar la respuesta.

## 4.2 Sesgo

El modelo podría reflejar sesgos presentes en los datos de entrenamiento o en los ejemplos few-shot. Esto podría generar diferencias no deseadas en el tono, el nivel de ayuda o la calidad de respuesta según la forma en que un cliente formule su pregunta.

### Mitigación
- Diseñar ejemplos diversos y balanceados.
- Revisar respuestas de prueba con distintos tipos de usuarios y estilos de escritura.
- Mantener supervisión humana en casos sensibles.

## 4.3 Privacidad de datos

El sistema de atención al cliente puede manejar información sensible como:
- nombre del cliente,
- dirección,
- historial de compras,
- número de pedido,
- reclamaciones o incidentes.

Si esta información se usa sin control dentro del modelo o se almacena sin medidas adecuadas, se corre el riesgo de vulnerar la privacidad del cliente.

### Mitigación
- Minimizar los datos enviados al modelo.
- Evitar exponer información personal innecesaria.
- Usar identificadores operativos en lugar de datos personales completos.
- Aplicar principios de acceso mínimo y control de logs.

## 4.4 Impacto laboral

Automatizar el 80% de las consultas repetitivas puede generar preocupación sobre el reemplazo de agentes humanos. Este es un punto ético importante porque la implementación tecnológica puede transformar el trabajo y la distribución de tareas dentro de la empresa. :contentReference[oaicite:5]{index=5}

### Mitigación
La solución debe plantearse como una herramienta de **empoderamiento** y no de sustitución total. Su objetivo es:
- reducir carga operativa repetitiva,
- mejorar tiempos de respuesta,
- y permitir que los agentes se concentren en los casos de mayor valor humano.

## 4.5 Transparencia ante el usuario

Existe también un riesgo de opacidad si el cliente no sabe si está hablando con un sistema automatizado o con una persona.

### Mitigación
La empresa debería indicar claramente que el primer nivel de atención es asistido por IA y que existe la posibilidad de escalar a un agente humano.

## 5. Evaluación crítica general

La solución propuesta es útil y realista para el contexto de EcoMarket, pero no debe interpretarse como un sustituto total del servicio al cliente humano. Su mayor fortaleza está en manejar consultas repetitivas y estructuradas de manera rápida y consistente. Su mayor limitación está en los casos que involucran ambigüedad, emociones intensas o situaciones excepcionales.

Desde una perspectiva ética, el diseño híbrido es una decisión responsable porque reconoce que:
- el modelo puede equivocarse,
- los datos sensibles deben protegerse,
- y los agentes humanos siguen siendo necesarios.

## 6. Conclusión

La implementación de una solución de IA generativa en EcoMarket ofrece ventajas claras en velocidad, escalabilidad y eficiencia operativa. Sin embargo, también introduce riesgos importantes relacionados con alucinaciones, sesgo, privacidad y transformación del trabajo.

Por ello, la propuesta más adecuada no es una automatización total, sino una automatización supervisada y modular, donde el modelo generativo actúa como apoyo para el servicio al cliente, mientras que los datos estructurados y la intervención humana siguen desempeñando un papel central.

En conclusión, una solución de este tipo solo es sostenible y ética si se implementa con límites claros, controles adecuados y una estrategia explícita de escalamiento humano.