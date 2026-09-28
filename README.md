# Auditoría de Google Ads con ChatGPT o Claude (es-CL)

Un skill —un documento de instrucciones más un programa pequeño— que convierte a ChatGPT o a Claude en auditor de
cuentas de Google Ads. Le das los informes que tú mismo descargas de la interfaz, le cuentas tu negocio en un par de
minutos, y te dice **dónde está el dinero** y qué búsquedas de otro negocio conviene cortar primero.

Desde la v3 el trabajo se reparte: **la IA conversa contigo y etiqueta cada búsqueda; el programa `auditor.py` hace
todas las cuentas y toma las decisiones** (qué se corta, qué se protege, qué te pregunta). Así las cifras cuadran y
lo que vendes no se toca, aunque la IA se equivoque al etiquetar.

**Sin credenciales, sin tokens, sin darle acceso a tu cuenta a nadie.** Corre dentro de tu propio ChatGPT o Claude,
con archivos que exportas en tres clics.

> Mantenido por el equipo de **[herihe.digital](https://herihe.digital/)** — agencia Google Partner en Valparaíso,
> Chile. Operamos n8n y Chatwoot gestionados en **[n8n.cl](https://www.n8n.cl/)** y
> **[chatwoot.cl](https://chatwoot.cl/)**; marketing automation en **[mautic.cl](https://mautic.cl/)**.

## Cómo se usa, en 3 pasos

1. **Descarga el informe.** Google Ads → Informes → **Términos de búsqueda**, últimos 90 días. En «Columnas», añade:
   **Campaña**, **Grupo de anuncios**, **Tipo de concordancia** (o «Concordancia»), Clics, Impresiones, Costo,
   **Conversiones**, **Todas las conversiones** y **Valor de conversión**. Descargar → CSV, con todas las filas.
   Adjúntalo tal como te lo dio Google, sin abrirlo ni guardarlo en Excel. **Recomendado:** descarga también
   **Ubicaciones coincidentes** (Campañas → Informes y estadísticas → Cuándo y dónde se mostraron los anuncios →
   Ubicaciones coincidentes → descargar), mismo período: con él revisa el gasto fuera de tu zona y el tráfico por
   «área de interés».
2. **Abre un chat nuevo** en ChatGPT o Claude **con el análisis de datos activado** («Análisis de datos» en ChatGPT,
   la herramienta de análisis en Claude). Adjunta **[`SKILL.md`](SKILL.md)**, **[`auditor.py`](auditor.py)** y el
   informe, y escribe: *«Audita esta cuenta siguiendo el documento adjunto.»* `auditor.py` sólo usa Python estándar,
   no se conecta a internet y no toca tu cuenta: puedes leerlo entero antes de usarlo.
3. **Responde la entrevista.** La primera respuesta es corta: lo que el archivo deja ver (cobertura, si la medición
   cuadra) y unas pocas preguntas —qué vendes y dónde, cuál de tus temas es tu **servicio principal**, tu marca, qué
   hacer con cada competidor que aparece y cómo cierras la venta—. Con tus respuestas viene la auditoría, y al final
   una **ficha del negocio**: guárdala y pégala al comienzo de la próxima vez. Si prefieres que siga sin responder,
   escribe *«sigue sin mis respuestas»* y el informe declara sus supuestos.

En **Claude Code** puedes dejarlo instalado copiando `SKILL.md` y `auditor.py` a `~/.claude/skills/auditor-google-ads/`.
Sin análisis de datos, el skill hace la entrevista y te entrega la lista de búsquedas para revisar, pero no inventa
cuentas: sin el programa no hay totales ni negativas de frase.

## Qué hace, en orden

- **Protege tu núcleo.** Lo que marcas como servicio principal nunca recibe «pausa», «negativa» ni «baja la puja» por
  rendimiento. Si rinde mal, lo que se revisa es la página, la medición o el valor de la conversión.
- **Limpia primero las búsquedas de otro negocio**: empleo y freelance, «gratis», cursos y tutoriales, hazlo tú
  mismo, marketplaces, otros rubros y los competidores donde no quieres aparecer. Salen en listas temáticas, listas
  para pegar, con cada término que bloquean a la vista. Estas no necesitan volumen: las decide tu negocio, no los
  números. Las búsquedas de otras ciudades salen aparte, para que las confirmes: nunca se cortan solas.
- **Revisa dónde se gasta** (con el informe de ubicaciones): lo que cae fuera de tu zona sale para confirmar, como
  exclusión de ubicación, y el tráfico por «área de interés» se compara con el físico antes de sugerir nada. En 8 de
  17 cuentas medidas había tráfico por interés, y en 7 convertía en proporción a su costo: cambiar a «Presencia» por
  regla corta ventas.
- **Pregunta por cada competidor**: *«¿quieres aparecer cuando buscan a X?»* No → negativa. Sí → campaña propia. No
  sé → te muestra sus números. Un nombre que no conoce nunca se decide solo.
- **Después busca el dinero grande**, que casi nunca está en una negativa por rendimiento:

| Palanca | Cuánto movió, medido |
|---|---|
| La medición estaba mal configurada | **20,6×** entre las dos columnas de conversión, en una cuenta |
| Un grupo de anuncios roto por dentro | **67 %** del gasto visible en el archivo, en 3 grupos, en una cuenta |
| La misma consulta comprada por varias campañas | **18,2 %** del gasto visible en el informe, con CPC 24× distinto, en una cuenta |
| El tipo de concordancia | **15,7 %** del gasto visible en el informe, en exceso de CPA, en una cuenta |

En las cuatro cuentas donde se midió término por término (florería, ferretería, control de plagas y seguridad
privada), **cero** términos tenían datos suficientes para negativarse por rendimiento. Por eso el skill separa dos
preguntas: *¿esta búsqueda es de mi negocio?* la respondes tú; *¿está rindiendo?* la responden los números, y casi
nunca alcanzan para cortar.

## Tres errores caros que evita

**`temu` coincide dentro de `TEMUCO`.** Si una revisión busca marketplaces por letras, marca como ajena
`flores a domicilio temuco`, que tenía 2 conversiones, y negativarla cortaría ventas; esa trampa apareció en 7 de las
8 cuentas medidas. En un e-commerce, `free` coincidía dentro de `zodiac freerider`, un limpiafondos de piscina: 43 términos y 4
conversiones. Antes de proponer una negativa, el skill la simula contra todo el archivo.

**La columna «Conversiones» depende de cómo se configuró.** En una ferretería marcaba 8,61 mientras «Todas las
conversiones» marcaba 177,73, porque 1.196 envíos de formulario estaban como acción secundaria.

**El informe de términos no es tu cuenta.** Con Performance Max, ese informe puede estar viendo el **3,4 % de tu
dinero**. El skill abre cada informe diciendo cuánto ve y cuánto no.

## Si quieres la auditoría completa

Con un archivo el skill dice **cómo está** la cuenta. Con estos otros dice **qué pasó** y **por qué**. Todos se
descargan de la interfaz, ninguno necesita API:

| Export | Para qué |
|---|---|
| **Campañas**, con la columna «Tipo de campaña» añadida a mano | la cobertura real: cuánto de tu dinero este análisis **no** ve |
| El mismo informe de términos, **ventana anterior de igual duración** | qué cambió, y dónde exactamente |
| **Historial de cambios** | relacionar lo que cambió con lo que alguien hizo, con fecha |
| **Acciones de conversión** | el denominador, cuando las dos columnas no coinciden |

La API de Google Ads sólo entrega el historial de cambios de los **últimos 30 días**; la interfaz cubre mucho más.
Para esa pregunta, quien descarga CSV ve más que quien consulta la API.

## Lo que este skill NO resuelve

- **No ejecuta nada.** No toca tu cuenta. Todo lo aplicas tú.
- **Puede no ver la mayor parte de tu dinero** si tienes Performance Max o Shopping: ahí hay feed, señales de audiencia y
  estructura — otro oficio.
- **No arregla tu página.** Cuando el problema está después del clic, lo que sigue es rehacer una oferta o un
  formulario.
- **No sabe si contestas el teléfono.** Lo que pasa después del contacto no está en el informe.
- **No reemplaza a alguien mirando la cuenta cada semana.** Un archivo es una foto.

Si al correrlo descubres que lo que falta es ejecutar —la medición, la estructura, lo que pasa después del clic—,
escríbenos si quieres que lo miremos: **[herihe.digital](https://herihe.digital/)**.

## Cómo fue validado

| Prueba | Resultado |
|---|---|
| 8 cuentas chilenas reales, más de 280.000 filas de informes de términos, compuertas corridas de forma determinista | **cero** recomendaciones que un humano vetaría |
| Lectura del archivo real de la interfaz | el export es **UTF-16 con tabulaciones**, no un CSV común: la lectura ingenua falla o devuelve una sola columna sin error |
| Filas `Total:` del pie | son hasta **ocho**, no una; incluirlas infla toda la cuenta **7,18×** |
| Dos pruebas a ciegas, con otro modelo y sin contexto | 14 defectos encontrados y corregidos |
| v3: el programa, contra controles con datos reales | protege un servicio secundario aunque la IA lo etiquete mal, no corta una búsqueda que convirtió y no negativa a un competidor sin tu respuesta |

Los cambios de cada versión están en [`CHANGELOG.md`](CHANGELOG.md).

## Licencia

MIT — úsalo, modifícalo, cóbralo. Si te sirve, una mención se agradece.
