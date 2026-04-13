# Fase 2: Evaluación de Fortalezas, Limitaciones y Riesgos Éticos

## 1. Introducción

Una solución técnicamente funcional no es suficiente si no se examinan con rigor
sus beneficios reales, sus límites operativos y las implicaciones éticas de su
despliegue. Esta fase evalúa críticamente la arquitectura híbrida propuesta para
EcoMarket, reconociendo que toda decisión de implementación de IA en un contexto
de atención al cliente involucra no solo variables técnicas, sino también
responsabilidades hacia los clientes, los trabajadores y la empresa.

---

## 2. Fortalezas de la solución propuesta

### a. Reducción drástica del tiempo de respuesta

El sistema puede responder de forma inmediata al 80% de las consultas repetitivas,
frente al promedio actual de 24 horas. Para consultas operativas como el estado de
un pedido, la respuesta no depende de disponibilidad de agentes sino de la velocidad
de recuperación del dato estructurado y la generación del LLM, que en conjunto idealmente
operarian en segundos.

### b. Disponibilidad continua

El asistente puede operar las 24 horas del día, los 7 días de la semana, sin
interrupciones por turnos, vacaciones o picos de demanda estacional. Esto es
especialmente relevante para una empresa de e-commerce en crecimiento acelerado,
donde el volumen de consultas puede ser impredecible.

### c. Consistencia y uniformidad en las respuestas

Al anclar las respuestas a fuentes de verdad explícitas (datos estructurados para
pedidos, documentos de política para devoluciones) el sistema reduce la variabilidad
que puede existir entre distintos agentes humanos. Todos los clientes reciben
información basada en las mismas fuentes y con el mismo nivel de detalle.

### d. Escalabilidad operativa sin costo lineal

La arquitectura modular permite crecer en volumen de consultas sin contratar
proporcionalmente más agentes. En la visión profesional, la incorporación de nuevas
categorías de consulta, canales de entrada o fuentes de conocimiento se realiza
extendiendo los módulos existentes, no rediseñando el sistema.

### e. Redistribución del talento humano hacia mayor valor

Al automatizar las consultas repetitivas, los agentes humanos pueden concentrarse
en los casos donde su intervención es genuinamente necesaria: situaciones de alta
carga emocional, reclamaciones complejas o excepciones que requieren criterio y
empatía. Esto no solo mejora la experiencia del cliente en esos casos, sino también
la calidad del trabajo del agente.

### f. Adaptabilidad sin reentrenamiento

Gracias al few-shot prompting, el comportamiento del modelo puede ajustarse ante
cambios en el tono de comunicación de la marca, nuevas categorías de consulta o
actualizaciones de política, modificando únicamente los ejemplos o los documentos
fuente. No se requieren ciclos de reentrenamiento ni infraestructura de MLOps.

---

## 3. Limitaciones de la solución

### a. Incapacidad para manejar casos que requieren juicio humano

El sistema no está diseñado para resolver situaciones que involucran ambigüedad
emocional, conflictos de criterio o excepciones fuera del dominio definido. Un
cliente con una reclamación grave, una situación de fraude o una solicitud inusual
requiere intervención humana que el modelo no puede sustituir. El módulo de
escalamiento mitiga pero no elimina esta limitación.

### b. Dependencia de la calidad de las fuentes de datos

El sistema es tan preciso como los datos que lo alimentan. Si la base de pedidos
contiene información incorrecta, desactualizada o incompleta, el modelo responderá
en consecuencia, sin capacidad de detectar o corregir el error en la fuente. Esta
limitación es especialmente crítica en el módulo operativo.

### c. Capacidad del modelo generativo en el MVP

Gemma 2B es adecuado para el prototipo dentro del dominio acotado del soporte de
e-commerce, pero presenta limitaciones frente a modelos más grandes en tres aspectos
concretos: seguimiento de instrucciones complejas en un mismo turno, manejo de
conversaciones con mucho contexto acumulado, y calidad del lenguaje en casos
borderline. En la visión profesional, este componente puede ser reemplazado por un
modelo de mayor capacidad sin modificar el resto de la arquitectura.

### d. Rendimiento computacional en entornos locales

La ejecución local de Gemma 2B con Ollama introduce latencia que puede percibirse
en equipos con recursos limitados. En el MVP académico esta es una limitación
aceptada; en producción, la solución requeriría infraestructura de cómputo dedicada
o servicios en la nube para garantizar tiempos de respuesta adecuados a la escala
de EcoMarket.

### e. Cobertura parcial en el MVP

La versión prototipo cubre pedidos, devoluciones y soporte general, pero no integra
aún: catálogo completo de productos, historial de compras, múltiples canales de
entrada ni conversaciones multi-turno de larga duración. Estas capacidades están
contempladas en la visión profesional y representan iteraciones futuras, no
limitaciones estructurales de la arquitectura.

---

## 4. Riesgos Éticos

### 4.1 Alucinaciones

Un LLM puede generar información plausible pero incorrecta. En el contexto de
atención al cliente, esto es especialmente grave cuando la información inventada
refiere a fechas de entrega, estados de reembolso, excepciones de política o
disponibilidad de producto; datos cuya inexactitud puede dañar directamente la
confianza del cliente y la reputación de EcoMarket.

**Mitigación en la arquitectura propuesta:**
La solución reduce este riesgo de forma estructural al separar fuentes de verdad
del componente generativo. El LLM nunca genera datos operativos: los recibe del
módulo de pedidos o del módulo de conocimiento y los redacta. Si el dato no está
disponible en la fuente, el sistema está diseñado para indicarlo explícitamente
en lugar de inferirlo. Esta decisión arquitectónica es la principal **salvaguarda
contra las alucinaciones en los puntos críticos del sistema**.

---

### 4.2 Sesgo

El modelo puede reflejar sesgos presentes en sus datos de entrenamiento o en los
ejemplos few-shot diseñados para guiar su comportamiento. Esto podría manifestarse
como diferencias en el tono, el nivel de ayuda o la calidad de la respuesta según
el estilo de escritura del cliente, su vocabulario o la forma en que formula su
consulta.

**Mitigación:**
- Diseñar los ejemplos few-shot con diversidad deliberada: distintos estilos de
  escritura, niveles de formalidad y tipos de consulta.
- Revisar periódicamente una muestra de respuestas generadas en busca de patrones
  diferenciales.
- Mantener supervisión humana activa en las etapas iniciales de despliegue para
  detectar comportamientos no esperados.

---

### 4.3 Privacidad de datos

El sistema procesa información sensible: nombres, direcciones de entrega, historial
de compras, números de pedido y, en casos de reclamo, información sobre situaciones
personales del cliente. El uso de esta información sin controles adecuados introduce
riesgos de exposición, uso indebido o incumplimiento de regulaciones de protección
de datos.

**Mitigación:**
- La ejecución local del modelo garantiza que los datos no se transmiten a
  proveedores externos, lo que representa una ventaja estructural frente a
  soluciones basadas en APIs comerciales.
- Los prompts deben construirse con el principio de mínima exposición: incluir
  solo los datos estrictamente necesarios para responder la consulta, usando
  identificadores operativos en lugar de datos personales completos cuando sea
  posible.
- Los registros de conversación deben gestionarse con políticas claras de retención,
  acceso y anonimización.
- En la visión profesional, el cumplimiento normativo (GDPR u equivalentes locales)
  debe considerarse desde el diseño del sistema, no como una capa posterior.

---

### 4.4 Impacto laboral

Automatizar el 80% de las consultas repetitivas plantea una pregunta legítima sobre
el futuro de los agentes de servicio al cliente actuales. Este riesgo no es solo
reputacional para EcoMarket: tiene implicaciones reales sobre el empleo, la
distribución de tareas y el bienestar de las personas que hoy conforman el equipo
de soporte.

**Posición de la propuesta:**
La solución no está diseñada para reemplazar al equipo humano sino para redistribuir
su carga de trabajo. Los agentes dejan de destinar capacidad a responder
mecánicamente las mismas preguntas y pueden concentrarse en los casos donde su
intervención genera mayor valor: situaciones complejas, clientes con alta frustración,
resolución de excepciones. En ese sentido, la automatización bien implementada puede
mejorar tanto la experiencia del cliente como la calidad del trabajo del agente.

---

### 4.5 Transparencia ante el cliente

Existe un riesgo ético cuando el cliente no sabe si está interactuando con un sistema
automatizado o con una persona. La omisión de esta información puede percibirse como
engaño y afecta potencialmente la confianza de los clientes.

**Mitigación:**
El sistema debe identificarse explícitamente como un asistente virtual desde el inicio
de la conversación e informar al cliente de su derecho a escalar a un agente humano
en cualquier momento. Esta transparencia no debilita la experiencia: los clientes
toleran bien la atención automatizada cuando es rápida, precisa y honesta sobre sus
límites.

---

## 5. Evaluación crítica consolidada

| Dimensión | Evaluación |
|---|---|
| Reducción de tiempo de respuesta | Alta. Automatización inmediata del 80% de consultas |
| Precisión en datos operativos | Alta, condicionada a la calidad de la fuente de datos |
| Manejo de casos complejos | Baja. Requiere escalamiento humano estructurado |
| Riesgo de alucinaciones | Mitigado estructuralmente por la separación de fuentes de verdad |
| Riesgo de sesgo | Presente. Requiere diseño cuidadoso de ejemplos y supervisión continua |
| Privacidad de datos | Favorecida por la ejecución local; requiere políticas de gestión de logs |
| Impacto laboral | Manejable si se acompaña de una estrategia organizacional clara |
| Transparencia | Requiere decisión explícita de comunicación hacia el cliente |

La solución es técnicamente viable, éticamente responsable en su diseño, y operativamente
pertinente para el problema de EcoMarket. Sus limitaciones más críticas no son fallas
del modelo generativo, sino condiciones de implementación que deben gestionarse con
igual rigor que los componentes técnicos: calidad de los datos, supervisión del
comportamiento del sistema, gestión del cambio con el equipo humano y transparencia
hacia el cliente.

---

## 6. Conclusión

La implementación de IA generativa en el soporte al cliente de EcoMarket ofrece
ventajas concretas y medibles en velocidad, consistencia y escalabilidad. Sin embargo,
esas ventajas solo son sostenibles si la solución se despliega con controles claros
sobre los riesgos éticos identificados.

El diseño híbrido adoptado (con fuentes de verdad separadas del LLM, escalamiento
humano estructurado y ejecución local de los modelos) reconoce que el modelo puede equivocarse,
que los datos sensibles deben protegerse, y que los agentes humanos no son un
componente prescindible sino una capa crítica del sistema.