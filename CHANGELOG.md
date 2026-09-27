# Cambios

## v3.0 — 2026-09-27

- **La IA etiqueta, el programa decide.** Nuevo `auditor.py` (Python estándar, sin internet): lee el export, arma los
  temas, suma, calcula conversiones esperadas, simula el daño de cada negativa contra todo el archivo y escribe el
  informe y la ficha. La IA sólo conversa, etiqueta cada búsqueda con una lista cerrada (o «no sé») y copia lo que el
  programa imprime. Las cifras dejan de depender de que la IA sume bien.
- **Lo que vendes, protegido por construcción:** servicio principal y secundarios nunca reciben pausa, negativa ni baja
  de puja. Si la etiqueta de la IA contradice lo que dijiste, gana tu respuesta y la búsqueda queda como pregunta.
- **Tres señales para cortar:** una búsqueda ajena se corta si tú la marcaste como algo que no vendes, o si coinciden
  la etiqueta de la IA, la lista de palabras del programa y una segunda pregunta («¿quien busca esto podría
  comprarte?»). Si no, sale «para confirmar», con su dinero.
- **Ficha literal:** el programa rechaza cualquier texto de la ficha que no sea una frase tuya; lo que infiere la IA
  va a «Supuestos».
- **La ficha no pierde lo que dijiste:** cada «no vendemos X» y cada «X sí la vendemos» tiene que quedar en ella, y
  el valor de un tema partido sale sólo de lo que dijiste del resto («lo demás 2»); si no lo dijiste, el resto queda
  como pregunta.
- **Una respuesta que no se reescribe:** la primera línea y «Qué hacer primero» los escribe el programa; en el chat va
  el informe corto y el detalle queda en `informe_completo.md`.
- **La oferta de la agencia la decide el programa**, sólo con un gatillo medido.
- **Ubicaciones:** con el informe «Ubicaciones coincidentes», el gasto fuera de la zona sale para confirmar (exclusión
  de ubicación, nunca automática) y el tráfico por «área de interés» se compara con el físico antes de sugerir
  «Presencia».
- **Rendimiento sin cortes automáticos:** lo que tiene evidencia y no es de lo que vendes sale como pregunta.
- **SKILL.md de 678 a ~260 líneas**: las reglas de cálculo viven en el código.
- Sale de esta versión el informe gráfico en HTML; vuelve cuando lo genere el programa.

## v2.3 — 2026-09-27

- **Archivo grande sin código:** con más de 300 filas y sin ejecución de código, la IA pide activar el análisis de
  datos; si no se puede, audita los términos del 80 % del costo y lo declara. El README lo recomienda desde el paso 2.
- **Ficha sin glosa:** cada línea lleva sólo lo que dijo el dueño; toda explicación va en «Supuestos».
- **Temas fijos entre turnos:** cada tema de P1b lleva su regla (grupo o palabras) y el turno 2 la reusa.
- **Sumas y esperadas:** con código, cada total imprime sus términos; las esperadas se escriben con las dos cifras y
  la menor (no se reducen a una fórmula: costo ÷ CPA sólo es la menor cuando el CPC del término está bajo el de la base).

## v2.2 — 2026-09-27

- **Simulación visible:** toda negativa de frase lleva la línea «Simulación: N términos contienen "x"», con cada término
  y su grupo; si uno cae en un tema o grupo 1 o 2, o convirtió, la negativa baja a exacta. Sin esa línea no hay frase.
- **Ficha de formato fijo:** temas copiados con el número del dueño; «No vende» sólo con lo marcado 3; supuestos aparte.
- **Cuentas más livianas:** con código, todo en código; sin código, sólo las cifras que sostienen una recomendación o
  una negativa. Conversiones esperadas con ejemplo numérico (el menor de los dos valores) y un atajo por grupo.

## v2.1 — 2026-09-27

- **Cifras agregadas:** toda suma nombra sus filas (o «n términos»), se cuadra con la fila de total y, si hay
  ejecución de código, se calcula ahí; en la duda, se muestra la cuenta.
- **La simulación de daño protege los temas 1 y 2** (principal y secundario, con sinónimos y el grupo de anuncios del
  tema); si el dueño parte un tema, sólo es irrelevante la parte que nombró como 3.
- **La ficha transcribe al dueño:** lo inferido va como «(supuesto)» y nunca rebaja un tema declarado.
- **La recomendación exige un gatillo nombrado** (medición, G5, 5.3, 5.2, G6) y ningún hallazgo se agranda más allá
  de su muestra. Si el usuario hizo una pregunta directa, el informe la contesta en su primera línea.
- **Turno 1 más liviano:** sólo encabezado, totales, cobertura, medición y temas; nada término a término.

## v2 — 2026-09-27

- **El primer turno es la entrevista.** Al recibir el archivo, la IA responde sólo con lo que puede leer (cobertura,
  portón de medición) y las preguntas, y espera. Sin saber qué es el núcleo del negocio, cualquier consejo sobre
  palabras puede tocar el servicio principal. Con «sigue sin mis respuestas» audita igual y declara sus supuestos.
- **Servicio principal (P1b) y ficha del negocio.** Una pregunta de múltiple opción armada con los temas del propio
  archivo; las respuestas forman una ficha que el informe devuelve al final, para pegarla en la próxima auditoría.
- **Núcleo protegido (G1b).** Nada del servicio principal se pausa, se negativa ni baja de puja por rendimiento o
  CPA: si rinde mal, se revisan la página, la medición o el valor de la conversión.
- **La limpieza por irrelevancia va primero.** Taxonomía en español de Chile (empleo, gratis, formación, hazlo tú
  mismo, otra zona, marketplaces, usados, otro negocio, competidores) con sus colisiones medidas. G2 no exige
  conversiones esperadas: la irrelevancia la decide el negocio. Frase sobre la palabra, con plural y sinónimos, en
  listas temáticas, tras la simulación de daño; las de rendimiento siguen exactas y con ≥ 3 conversiones esperadas.
- **Competidores y nombres desconocidos pasan a ser preguntas:** «¿quieres aparecer cuando buscan a X?».
- **Preguntas nuevas:** cómo se cierra la venta (P4) y, opcional, cuánto vale un cliente (P6). El export pide también
  Grupo de anuncios, Tipo de concordancia y Valor de conversión.
- **Más corto:** de 1.150 a 650 líneas y un tercio menos de texto, con las mismas reglas y cifras medidas. El README
  describe la entrevista nueva, las columnas del export y qué es cada cifra de calibración.
