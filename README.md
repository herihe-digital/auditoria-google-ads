# Auditoría de Google Ads con ChatGPT o Claude (es-CL)

Un **skill** —un documento de instrucciones— que convierte a ChatGPT o a Claude en un auditor de
cuentas de Google Ads que no inventa. Le das los informes que tú mismo descargas de la interfaz y te
dice **dónde está el dinero**, que casi nunca está en la lista de negativas que te entregaron.

**Sin credenciales, sin tokens, sin darle acceso a tu cuenta a nadie.** Corre dentro de tu propio
ChatGPT o Claude, con archivos que exportas en tres clics.

> Mantenido por el equipo de **[herihe.digital](https://herihe.digital/)** — agencia Google Partner en
> Valparaíso, Chile. Operamos n8n y Chatwoot gestionados en **[n8n.cl](https://www.n8n.cl/)** y
> **[chatwoot.cl](https://chatwoot.cl/)**; marketing automation en **[mautic.cl](https://mautic.cl/)**.

## Por qué existe

Construimos tres versiones de este auditor y **las tres fallaron** cuando las corrimos contra cuentas
reales. Lo que está publicado acá es lo que sobrevivió a esos ataques, calibrado contra **ocho cuentas
chilenas** —una florería, una ferretería de pueblo, control de plagas, seguridad privada, un
laboratorio, dos e-commerce y una agencia— sumando **más de 63.000 términos de búsqueda**.

El resultado que ordena todo el documento:

> En más de 63.000 términos de ocho cuentas reales, la cantidad de palabras con evidencia estadística
> suficiente para ser negativadas por rendimiento fue **cero**.

Un auditor cuya salida principal es una lista de negativas está, en cuatro de cuatro cuentas
medidas, inventando. El dinero estaba en otra parte, siempre:

| Palanca | Cuánto movió, medido |
|---|---|
| La medición estaba mal configurada | **20,6×** entre las dos columnas de conversión, en una cuenta |
| Un grupo de anuncios roto por dentro | **67 % del gasto** de una cuenta, en 3 grupos |
| La misma consulta comprada por varias campañas | **18,2 %** del gasto, con CPC hasta 24× distinto |
| El tipo de concordancia | **15,7 %** del gasto en exceso de CPA |
| Negativas por irrelevancia | **0,21 %** |

## Los errores que este skill se niega a cometer

Son 27 trabas explícitas. Estas tres son las que más plata cuestan y las vimos en cuentas reales:

**`temu` coincide dentro de `TEMUCO`.** Una lista de marketplaces aplicada como negativa por
substring borra `flores a domicilio temuco` —2 conversiones— y coincide en **7 de 8 cuentas**
medidas. En un e-commerce, `free` coincidía dentro de `zodiac freerider`, el modelo de un limpiafondos
de piscina: 43 términos y 4 conversiones. La regla es frontera de palabra, y mostrarte la lista
completa de lo que va a morir antes de matarla.

**La columna «Conversiones» es una decisión, no un dato.** En una ferretería marcaba 8,61 mientras
«Todas las conversiones» marcaba 177,73, porque 1.196 envíos de formulario estaban como acción
secundaria. La CVR aparente era 0,08 % y la real 1,70 %.

**El informe de términos no es tu cuenta.** Cuando hay Performance Max, ese informe puede estar
viendo el **3,4 % de tu dinero**. Cualquier cifra de ahorro calculada sobre él, sin decirlo, es
autoelogio.

## Cómo se usa

1. Descarga de Google Ads → Informes → **Términos de búsqueda**, últimos 90 días, con las columnas
   «Conversiones» **y** «Todas las conversiones». Adjunta el archivo tal como te lo dio Google.
2. Abre un chat nuevo en ChatGPT o Claude, adjunta **[`SKILL.md`](SKILL.md)** y el informe, y escribe:
   *«Audita esta cuenta siguiendo el documento adjunto.»*
3. Responde las dos preguntas de la entrevista. Son obligatorias: sin saber qué vendes y dónde
   atiendes, cualquier auditor —humano o no— recomienda estupideces.

En **Claude Code** puedes dejarlo instalado copiando el archivo a `~/.claude/skills/auditoria-google-ads/SKILL.md`.

### Si quieres la auditoría completa

Con un solo archivo el skill dice **cómo está** la cuenta. Con estos otros dice **qué pasó** y **por
qué**, que es la mitad del valor de una auditoría. Todos se descargan de la interfaz, ninguno necesita
API:

| Export | Para qué |
|---|---|
| **Campañas**, con la columna «Tipo de campaña» añadida a mano | la cobertura real: cuánto de tu dinero este análisis **no** ve |
| El mismo informe de términos, **ventana anterior de igual duración** | qué cambió, y dónde exactamente |
| **Historial de cambios** | relacionar lo que cambió con lo que alguien hizo, con fecha |
| **Acciones de conversión** | el denominador, cuando las dos columnas no coinciden |

Un detalle que sorprende: la API de Google Ads sólo entrega el historial de cambios de los **últimos
30 días**. La interfaz cubre mucho más. Para esa pregunta, quien descarga CSV ve más que quien
consulta la API.

## Lo que este skill NO resuelve

Está escrito adentro, y es la parte que más nos importa que se lea:

- **No ejecuta nada.** No toca tu cuenta. Todo lo aplicas tú.
- **No ve el 60–90 % de tu dinero** si tienes Performance Max o Shopping: ahí no hay términos que
  auditar, hay feed, señales de audiencia y estructura — otro oficio.
- **No arregla tu página.** Cuando el diagnóstico dice «el problema está después del clic» —que es lo
  más frecuente— lo que sigue es rehacer una oferta o un formulario, y eso no lo hace un chat.
- **No sabe si contestas el teléfono.** En servicios locales, la mitad de las «no conversiones» es
  atención, no publicidad.
- **No reemplaza a alguien mirando la cuenta cada semana.** Un archivo es una foto.

Si al correrlo descubres que el problema no era ninguna palabra sino la medición, la estructura o lo
que pasa después del clic —que es lo que encontramos en las ocho cuentas donde lo calibramos— lo que
necesitas ya no es un auditor. Escríbenos si quieres que lo miremos:
**[herihe.digital](https://herihe.digital/)**.

## Cómo fue validado

| Prueba | Resultado |
|---|---|
| 8 cuentas reales, compuertas corridas de forma determinista | **cero** recomendaciones que un humano vetaría |
| Lectura del archivo real de la interfaz | el export es **UTF-16 con tabulaciones**, no un CSV: la lectura ingenua falla o —peor— devuelve una sola columna sin error |
| Filas `Total:` del pie | son hasta **ocho**, no una; incluirlas infla toda la cuenta **7,18×** |
| Dos pruebas a ciegas, con otro modelo y sin contexto | 14 defectos encontrados y corregidos, entre ellos uno que hacía que un bloque de tráfico pareciera basura cuando no lo era |

## Licencia

MIT — úsalo, modifícalo, cóbralo. Si te sirve, una mención se agradece.
