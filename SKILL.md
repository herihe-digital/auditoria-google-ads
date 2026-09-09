---
name: auditor-google-ads
description: Audita una cuenta de Google Ads a partir de los reportes que tú mismo exportas desde la interfaz. No pide contraseñas, tokens ni acceso a tu cuenta. Encuentra dónde está el dinero — que casi nunca está en la lista de negativas — y dice en voz alta qué parte de tu cuenta no alcanza a ver. Úsalo cuando quieras entender un reporte de términos de búsqueda, decidir si una palabra es mala o si lo malo es la página, o revisar lo que te recomendó una agencia o un analista.
---

# Auditor de cuentas de Google Ads

Este skill convierte a Claude o a ChatGPT en un auditor de medios pagados que **no inventa**.

Está calibrado contra ocho cuentas chilenas reales — una florería, una ferretería de pueblo, una
empresa de control de plagas, una de seguridad privada, un laboratorio, dos e-commerce y una agencia —
sumando más de 63.000 términos de búsqueda. Cada número marcado **[medido]** salió de esas cuentas.
Tres diseños distintos de este mismo auditor fueron construidos y después atacados con datos reales:
**los tres fueron reprobados**. Lo que sigue es lo que sobrevivió a los ataques.

---

## 0. La conclusión que ordena todo el resto

> **Un dato de rendimiento nunca prueba que una palabra sea irrelevante. Prueba, como mucho, que
> rinde poco. «¿Esta palabra es de mi negocio?» y «¿esta palabra está rindiendo?» se responden con
> fuentes distintas y no se pueden contaminar.**

En más de 63.000 términos de ocho cuentas reales, la cantidad de términos con evidencia estadística
suficiente para ser negativados por rendimiento fue **[medido]**:

| cuenta | términos analizados | negativas por rendimiento estadísticamente defendibles |
|---|---|---|
| florería | 3.872 | 0 |
| ferretería | 43.530 | 0 |
| control de plagas | 10.238 | 0 |
| seguridad privada | 534 | 0 |

**Cero, sobre 63.000.** Un auditor cuya salida principal es una lista de negativas está, en cuatro de
cuatro cuentas reales, inventando. Si al terminar produces una lista larga de palabras para negativar,
te equivocaste en alguna parte: vuelve a la Fase 5 y busca el dinero donde de verdad está.

**El orden real del dinero, medido** — y por lo tanto el orden de la salida:

| # | Palanca | Cuánto movió en las cuentas medidas | Costo de ejecutarla |
|---|---|---|---|
| 1 | Arreglar la **medición** | factor **20,6×** entre columnas de conversión en la ferretería | 1 hora, gratis |
| 2 | Arreglar el **contenedor muerto** (página / oferta / teléfono) | **67 % del gasto** de la cuenta de plagas en 3 grupos de anuncios | días, pero es el único arreglo que devuelve conversiones |
| 3 | **Auto-competencia** entre campañas | **18,2 %** del reporte de la florería, con el mismo término a CPC 24× distinto | 1 tarde de estructura |
| 4 | **Tipo de concordancia** | **15,7 %** del gasto de la florería en exceso de CPA | media hora |
| 5 | Domar el **CPC fuera de escala** | **51,1 % del gasto** en 5,1 % de los clics, en la ferretería | 30 minutos de puja |
| 6 | **Separar intención** y darle puja propia | bloque de bricolaje = 40,5 % del gasto en plagas | 2 horas |
| 7 | **Negativas** por irrelevancia o geografía | **0,21 %** del gasto de la ferretería | 15 minutos |

Las negativas son la última línea y son diminutas. Todo el mercado empieza por ahí.

---

## 1. Qué necesitas — y qué NO necesitas

**No necesitas** darle a nadie tu contraseña, tu token, tu OAuth ni acceso a tu cuenta. Este skill
funciona con archivos que tú exportas desde la interfaz de Google Ads y pegas o adjuntas en el chat.
Si algún día un skill, una herramienta o una persona te pide credenciales de tu cuenta publicitaria
para «auditarla automáticamente», eso es un problema de seguridad, no una comodidad.

### El export mínimo (sin esto, el skill se niega a opinar)

**Términos de búsqueda, últimos 90 días, con las DOS columnas de conversión** — «Conversiones» y
«Todas las conversiones». En Informes → Términos de búsqueda → Descargar → CSV.

Adjunta el archivo tal como te lo dio Google, sin abrirlo ni volver a guardarlo. Si lo abres en Excel
y lo guardas encima, es fácil perder los acentos o partir las columnas — y el archivo original está
en un formato que el skill sabe leer (ver Fase 1).

⚠️ **Exporta TODAS las filas, no las primeras N.** Si tu herramienta o tu export corta en las 400
filas de mayor costo, estás mirando el 10 % del archivo. En la florería, las 400 más caras eran
1.459.548 CLP de… 3.872 filas. Todos los promedios cambian **[medido]**: la CVR de la cuenta pasa de
9,4 % a 8,24 %, y la dispersión entre campañas de 2,9× a 9,1× — que es la diferencia entre «puedes
usar el promedio de la cuenta» y «tienes prohibido usarlo».

### Los seis exports que destraban el resto (pídelos en este orden)

Todos se descargan de la interfaz. **Ninguno necesita API, permisos de desarrollador ni nada técnico**
— cualquiera con acceso a la cuenta los baja en un par de minutos.

| # | Export | Qué destraba | Cuándo pedirlo |
|---|---|---|---|
| 1 | **Campañas**, **con la columna «Tipo de campaña» añadida a mano** (ver Fase 2 bis) — **uno por cada ventana que analices**, con el período exacto de esa ventana | la cobertura real y qué tipo de campaña se lleva el dinero invisible | **siempre** |
| 2 | **El mismo informe de términos, ventana anterior de igual duración** | pasa de «cómo está» a **«qué pasó»** (Fase 7) — la mitad del valor de una auditoría | **siempre que exista historia**; imprescindible si algo se rompió |
| 3 | **Historial de cambios**, cubriendo las dos ventanas | relaciona lo que pasó con **lo que alguien hizo** (Fase 8) | siempre que la Fase 7 encuentre un quiebre |
| 4 | **Acciones de conversión** (nombre, categoría, principal/secundaria, ventana) | el denominador. Factor 20,6× en una cuenta real | siempre que la CVR del archivo sea < 1 %, o que las dos columnas diverjan |
| 5 | **Páginas de destino** (URL final, clics, costo, conversiones) | separar «palabra mala» de «página mala» | siempre que dispare S1 o S4 |
| 6 | **Palabras clave negativas** ya existentes | no recomendar una negativa que ya existe, y encontrar la negativa vieja que está matando un término bueno | antes de emitir cualquier negativa |

**Pídelos de a poco y en este orden.** Cada archivo es fricción; el 1 y el 2 pagan solos casi
siempre, y los demás sólo cuando el análisis los reclama por una razón que puedes nombrar.

---

## 2. Fase 0 — La entrevista (obligatoria)

**El negocio se declara, nunca se infiere.** Una de las cuentas medidas tiene un nombre que sugiere
climatización y es una **ferretería** de pueblo — cemento, malla acma, pellet. Un auditor que dedujera
el rubro del nombre habría marcado el inventario completo como irrelevante **[medido]**. Y deducirlo de los propios datos
también falla: un diseño construyó un léxico automático que **declaró que los tulipanes, los girasoles
y las orquídeas no eran el núcleo de una florería**; otro partió `los andes` en `and`.

### Las dos preguntas bloqueantes

> **P1.** En una frase, como lo diría tu cliente: **¿qué vendes, a quién, y en qué comunas o ciudades
> atiendes de verdad?** ¿Y qué NO vendes, pero te confunden con eso?

> **P2.** *(múltiple opción, la generas tú desde el archivo)* Corre el detector de marca y presenta
> 5–10 fichas: **«estos tokens tienen un CTR muy por encima del resto de la cuenta. Marca cada uno:
> (a) es mi marca (b) es un competidor (c) es mi ciudad o comuna (d) es otro negocio, parecido pero
> no soy yo (e) nada de eso.»**
>
> La opción (d) no sobra: **[medido]** en una cuenta de poda de árboles apareció el nombre de una
> **empresa eléctrica** que también poda árboles —los del tendido— y que no es marca propia, ni
> competidor, ni ciudad. Sin esa casilla el usuario la clasifica mal y el auditor decide sobre una
> mentira.
>
> **Si salen más de 10 candidatos, ordénalos por gasto, no por CTR**, y muestra los que expliquen al
> menos el 80 % del gasto de los candidatos. Lo que no entre, dilo en una línea: *«hay N tokens más
> con esta señal, que suman X»*. El detector suele devolver más ruido que señal — **[medido]** 25
> candidatos en una ventana, de los cuales uno era la marca y el resto eran modificadores de intención
> comercial (`cuánto`, `precio`, `vale`).
>
> Detector **[medido]**: token de ≥ 4 letras, presente en ≥ 2 términos, ≥ 20 impresiones y **CTR ≥ 2,5×
> el CTR de la cuenta**. En las cuentas reales puso la marca propia en primer lugar en las tres que
> probé (2,6× / 7,2× / 11,4×) — **y también trajo un competidor y una comuna en los primeros puestos.**
> Por eso es un generador de candidatos, jamás un clasificador autónomo, y por eso se resuelve con
> una múltiple opción de treinta segundos en vez de una pregunta abierta.
>
> ⚠️ **Si el detector devuelve CERO candidatos, no significa que no haya marca.** Cuando el archivo
> está dominado por una campaña de marca, el CTR de la cuenta ya es altísimo y **nada llega a 2,5×**
> — ni la propia marca. **[medido]** en una cuenta real cuyo CTR de referencia era 26 %, el token de
> marca concentraba el 74,8 % del costo y aun así no cruzaba el umbral. Cuando pase eso: baja el
> umbral a 1,5×, mira los nombres de las campañas y grupos de anuncios (ahí suele estar escrita la
> marca), y si sigue sin salir, **pregúntale directamente al usuario cuál es su marca y cómo la
> escriben mal**. Nunca sigas sin lista de marca: G1 depende de ella, y sin G1 el auditor puede
> recomendar negativar el nombre del negocio.

### Las tres opcionales (sigues sin ellas, pero declaras qué quedó ciego)

> **P3.** «Tu archivo muestra X conversiones en Y clics (Z %). ¿Coincide con los contactos reales que
> recibiste? Y si tus clientes llegan por WhatsApp o teléfono, ¿eso se está contando?»
> **P4.** *(casi nunca hace falta preguntarla — ver Fase 1)* La fila de totales viene en el propio
> archivo. Sólo pide el export de **Campañas** cuando el archivo esté recortado o cuando sus totales
> de cuenta y de búsqueda sean idénticos, que es la señal de que Performance Max quedó fuera.
> **P5.** «¿Cambiaste sitio, formulario, teléfono, WhatsApp o etiqueta en los últimos 90 días?»

### La anti-pregunta

**Nunca preguntes «¿qué palabras son importantes para ti?».** Es exactamente la pregunta que el dueño
responde mal y que el analista mediocre usa para lavarse las manos del resultado.

---

## 3. Fase 1 — Cómo se lee el archivo de verdad

**El export de Google Ads no es un CSV, aunque el archivo se llame `.csv`.** Esto está verificado
contra exports reales descargados de la interfaz **[medido]**:

| Lo que parece | Lo que es |
|---|---|
| CSV separado por comas | **separado por tabulaciones** |
| texto UTF-8 | **UTF-16** — abrirlo como UTF-8 revienta con `invalid start byte` |
| la primera fila es el encabezado | hay **2 líneas de preámbulo** antes (nombre del informe y período) |
| todas las filas son datos | las **últimas 8 son totales** |
| `97904` | `"97,904"` — separador de miles, entre comillas, sólo en algunas columnas |
| `5.48` | `5.48%` |
| columnas en tu idioma | el encabezado salió **en inglés** en una cuenta chilena |

**Cómo leerlo, en orden:**

1. **Decodifica probando UTF-16 antes de rendirte.** Si ves un solo carácter raro por letra, o el
   archivo «no abre», es esto.
2. **El delimitador es el que más se repite**, tabulación o coma. No lo asumas.
3. **El encabezado es la primera fila con 5 o más delimitadores.** Salta lo que venga antes.
4. 🚨 **Descarta TODA fila cuyo primer campo con texto empiece por `Total:`.** No es una: en un
   informe real había **ocho** — `Total: Account`, `Total: Search`, `Total: Your keywords`,
   `Total: All but removed keywords`, `Total: URL inclusions in your account`, y dos de
   `AI Max` (expanded matches y landing page matches). **Si no las excluyes, todos los números de la
   cuenta se inflan 7,18× [medido]**: el costo pasa de 1.872.341 a 13.438.211, y cada promedio, cada
   CVR y cada línea base que calcules después queda envenenada. Un auditor que sólo filtra
   `Total: Account` deja siete filas falsas adentro, cada una con el tamaño de la cuenta entera.
5. **Números:** quita comillas, quita el separador de miles, quita el `%`. `--`, `—`, vacío y `N/A`
   son **desconocido**, jamás cero.
6. **Las palabras clave de concordancia de frase vienen entre comillas dobles dentro del campo**
   (`"""tu palabra clave"""` en el archivo crudo → `"tu palabra clave"` tras parsear). Quítalas para
   comparar, pero recuerda que esas comillas son el tipo de concordancia.

### La pregunta que ya no hace falta hacer

**La fila `Total: Account` viene dentro del archivo.** No se la pidas al usuario: léela. Con ella
calculas la cobertura sin fricción — en el informe real medido, 75,3 %.

⚠️ Y si `Total: Account` y `Total: Search` traen **números idénticos**, el informe está limitado a
búsqueda: Performance Max y Shopping siguen fuera, y para la cobertura sobre la cuenta completa
necesitas igual el export de campañas.

---

## 3 bis. Sanidad de las filas, antes de calcular nada

| Chequeo | Regla | Por qué |
|---|---|---|
| **Guion es desconocido** | `--`, `—`, vacío y `N/A` → **desconocido**, jamás cero | «no hay dato» y «cero» son cosas opuestas |
| **Conversiones fraccionarias** | leer como decimal (`0,33`, `11,89`), nunca `int()` | Google reparte conversiones; redondear a cero mata términos buenos |
| **Clics > impresiones** | fila marcada `ARTEFACTO`, fuera de todo cálculo de CTR | **[medido]** 7 filas con 2 clics sobre 1 impresión (CTR 200 %) envenenaban el detector de marca y la matriz CTR |
| **Deduplicación por campaña** | sumar el mismo término servido por varias campañas… | …**pero guarda la vista sin sumar**: ahí vive el hallazgo nº 3 (Fase 5.3) |
| **Columna de valor** | si existe, se lee **siempre** | sin ella, todas las compuertas cuentan conversiones de 1 peso igual que ventas de 80.000 |

---

## 4. Fase 2 — Cuánto del dinero NO estás viendo (va en el encabezado)

```
cobertura = Σ costo(términos del archivo) ÷ costo TOTAL de la cuenta en el mismo período
```

**El denominador es la cuenta entera, no el gasto de búsqueda.** Calcularlo sobre el propio export es
autoelogio. Un diseño imprimía «este archivo explica el 62,5 % del gasto» — aritméticamente correcto
sobre búsqueda, y **la cobertura real era 10,0 %** **[medido]**, porque Performance Max era el 84 % de
la cuenta y no aparece en ningún reporte de términos.

| tipo de cuenta | PMax % del gasto | cobertura real del reporte de términos |
|---|---|---|
| florería | 84,0 % | **10,0 %** |
| e-commerce grande | 64,2 % | **19,2 %** |
| e-commerce mediano | 79,3 % | **9,4 %** |

**Reglas duras:**

**De dónde sale el denominador, en orden de preferencia** (y no hay contradicción entre estas dos
reglas: la primera dice de dónde leerlo, la segunda qué puedes afirmar con él):

1. La fila `Total: Account` del propio archivo de términos → te da la **cobertura**, sin pedir nada.
2. El export de **Campañas** → te da además el **desglose por tipo**, que es lo único que permite
   nombrar qué quedó invisible (Performance Max, Shopping, Display).

> **Con (1) puedes imprimir la cobertura.** Con (1) pero sin (2) **no puedes nombrar la composición
> de lo invisible ni imprimir una cifra de ahorro sobre la cuenta** — sólo sobre el gasto que ves, y
> diciéndolo con esas palabras. Sin (1) ni (2), la cobertura es «desconocida» y no imprimes ninguna
> cifra de ahorro, ni una.

- Si la cobertura es **< 25 %**, no emites ningún diagnóstico de palabras. Emites un solo hallazgo:
  *«la mayor parte de tu dinero está en campañas que este reporte no puede ver»*, y pides el export
  de campañas para hablar de ahí.
- ⚠️ **Pero el hallazgo de medición (Fase 3) sale igual, siempre.** La divergencia entre las dos
  columnas de conversión es un hecho de la **cuenta entera** y no depende de cuánto gasto vea el
  reporte de términos. Callarla porque la cobertura es baja fue un defecto de orden que encontramos
  validando este mismo skill: dos cuentas reales con divergencias de **18×** y **25×** salían sin que
  nadie se enterara, y ese es el arreglo número uno de la lista.
- **Sin el export de campañas, la cobertura es «desconocida» y no imprimes NINGUNA cifra de ahorro
  total.** Ni una.
- Nunca digas «estos son los términos que gastaron». Di **«estos son los términos que Google deja
  ver»**: entre 37 % y 55 % del gasto de búsqueda no tiene término visible por el umbral de
  privacidad, y esa parte invisible **convierte** (24–30 % de las conversiones) **[medido]**.

---

## 4 bis. Fase 2 bis — El archivo de Campañas, que es el que trae el denominador

Sin este archivo la cobertura es una suposición. Y es el archivo que **más veces llega mal pedido**,
porque la columna que lo hace útil no viene puesta por defecto.

### Cómo pedirlo, en este orden

> Campañas → **Columnas → Modificar columnas → añade «Tipo de campaña»** → selecciona el **mismo
> período exacto** del informe de términos → Descargar → CSV.

⚠️ **El paso de la columna no es opcional y es el que todos saltan.** Sin «Tipo de campaña» tienes
costos por campaña y ninguna forma de saber cuáles son Performance Max, Shopping o Display — que es
justamente el cálculo para el que pediste el archivo. Un archivo de campañas sin esa columna sirve
para el total y para nada más; dilo, y pídelo de nuevo.

⚠️ **Mismo período, exactamente.** Dos archivos de ventanas distintas producen una cobertura falsa,
y el error no se nota: los dos números existen y se dividen sin protestar.

### Cómo leerlo

Es el **mismo formato** que el informe de términos — UTF-16, tabulaciones, dos líneas de preámbulo,
filas `Total:` al final — así que se aplica la Fase 1 completa, incluida la regla de descartar todas
las filas de totales.

**No busques nombres de columna exactos: búscalos por significado.** El encabezado sale en el idioma
de la interfaz de quien exportó, y **[medido]** salió en inglés en una cuenta chilena. Lo que
necesitas es: nombre de campaña · tipo de campaña · costo · clics · conversiones · todas las
conversiones. Si una falta, dilo y sigue con las que hay.

### Qué haces con él

```
cobertura        = Σ costo(términos) ÷ Σ costo(TODAS las campañas)
gasto invisible  = Σ costo(campañas cuyo tipo NO es Búsqueda)   → nómbralo por tipo
```

Y el cruce que casi nadie hace: **campaña que aparece en el archivo de campañas y no aparece ni una
vez en el de términos**. Si es de búsqueda y gastó dinero, eso no es normal — o está entregando por
audiencia sin consulta, o sus términos cayeron bajo el umbral de privacidad. En una cuenta real, de
**83 campañas de búsqueda sólo una tenía gasto**, y el archivo de términos traía una sola campaña
**[medido]**: sin este cruce, el informe habría dicho «tu cuenta tiene una campaña» sobre una cuenta
de 107.

---

## 5. Fase 3 — El portón de medición (aquí se detiene casi todo)

> Si la CVR de la cuenta es **< 0,5 %** y el negocio declarado cierra por teléfono, WhatsApp o
> formulario → **el skill se detiene** y emite un único hallazgo: *«tu columna de conversión
> probablemente no mide lo que cierra»*, más el pedido del export de Acciones de conversión.
> **Ninguna negativa sale en ese estado.**

**[medido]** En la ferretería: columna «Conversiones» = 8,61 contra «Todas las conversiones» = 177,73.
Factor **20,6×**, porque 1.196 envíos de formulario estaban marcados como acción **secundaria**. La CVR
aparente era 0,08 % y la real 1,70 %. Y **228 términos que muestran «0 conversiones» tenían
conversiones registradas** — 11,6 % del gasto.

Si las dos columnas divergen, **el primer hallazgo del informe es la configuración de conversión**, no
los términos. Y un clic a WhatsApp o al teléfono **no es una conversión secundaria** en Chile: es la
puerta de entrada del negocio.

---

## 6. Fase 4 — Cómo agrupar variantes sin matar a nadie

**Nivel 1 (siempre):** minúsculas → quitar acentos → quitar palabras vacías (`de, en, el, la, para,
por, con, y, del, al, un, una, a`) → **conservar el orden**.

⚠️ **No singularices topónimos.** Un singularizador ingenuo de `-s`/`-es` convierte `los andes` en
`los and` y `las condes` en `las cond` **[medido]**, y entonces ninguna lista de comunas chilenas
vuelve a reconocerlas: el auditor queda estructuralmente ciego justo para las ciudades terminadas en
-s, que en Chile son muchas y a veces convierten.

**Nivel 2 (ignorar el orden): sólo para PROTEGER, nunca para acusar.** Y de ahí la asimetría que es el
corazón de la regla:

1. Toda negativa se emite sobre la **forma exacta del término**, nunca sobre el grupo.
2. Si **cualquier** miembro del grupo convirtió, **ninguno** puede ser negativado por rendimiento.

Así, agrupar de más sólo puede volverte conservador, nunca injusto.

**Lo que se gana [medido]** — grupos «mixtos», donde una variante convierte y su hermana marca cero:
**6,18 % del gasto** de la florería, 3,56 % de la ferretería, 2,11 % de plagas se habrían negativado
por error. Ejemplo literal: `flores a domicilio concepcion` (153 clics, 11,89 conv) + `flores a
domicilio en concepcion` (25 clics, 2,00) + `flores concepcion a domicilio` (11 clics, 0) + `flores
domicilio concepcion` (4 clics, 0). Cuatro filas, una sola consulta.

**Y agrega el eje idioma.** `floricultura em santiago chile` es portugués, no español: 2.997 CLP y 23
clics a cero conversiones que no se fusionaban con nada porque la lista de palabras vacías era sólo
española **[medido]**.

---

## 7. Fase 5 — Las compuertas, en orden. La primera que cierra decide.

**Si tienes dos ventanas, las compuertas corren sobre la MÁS RECIENTE.** Ella es el estado actual, y
es sobre ella que alguien va a actuar. La ventana anterior sirve para la Fase 7 (qué cambió) y como
control: cuando un hallazgo aparece en la reciente, mira si ya estaba en la anterior — si estaba, es
crónico; si no, tiene fecha, y eso vale mucho más.

⚠️ Si el quiebre de la Fase 7 fue **grande**, corre también las compuertas sobre la ventana anterior:
el período sano es el único donde algunos ejes se pueden medir sin contaminación. **[medido]** en una
cuenta real, el exceso de concordancia sólo era legible en la ventana sana; en la reciente, el 86,8 %
de ese gasto vivía dentro de un contenedor muerto y el número no significaba nada.

**Qué archivo responde qué** — no son intercambiables:

| pregunta | archivo |
|---|---|
| cobertura, y qué tipo de campaña se lleva el dinero invisible | Campañas |
| salud del contenedor (G5), intención, concordancia, cualquier cosa por **grupo de anuncios** | términos — el de Campañas **no tiene** columna de grupo, y por eso no puede alimentar G5 |
| qué cambió entre períodos | los dos informes de términos, y Campañas de **cada** ventana |
| quién hizo qué | historial de cambios |

### G0 — ¿Costó dinero?

```
costo == 0   → FUERA del análisis. No aparece ni como «monitorear».
clics == 1   → balde «GASTO NO JUZGABLE», reportado agregado, jamás fila por fila.
```
**[medido]** El 87 % de los términos de la ferretería y el 78 % de los de plagas tienen **cero clics y
cero costo**. Negativarlos no ahorra un peso y cierra alcance futuro: es el inflador nº 1 de las listas
de negativas que reparte el mercado. Y los términos de 1 clic son el 39,1 % del gasto de la ferretería
— la línea más grande del informe, y no sostiene ninguna decisión individual.

### G1 — Marca propia y navegacional → **INTOCABLE**

Nunca se negativa la marca propia, sus variantes mal escritas, el dominio, ni una consulta navegacional
(`horario`, `teléfono`, `dirección`, `cómo llegar`, `sucursal`). En ningún nivel de evidencia.

⚠️ **Dos errores que este portón produce si lo escribes ingenuamente:**

1. **La protección navegacional debe estar limitada a TU marca.** Sin ese límite, protegiste para
   siempre el teléfono de tu competencia: `teléfono de <competidor>`, `www <competidor> com`,
   `<eléctrica nacional> poda de árboles teléfono` **[medido]**, en cuatro cuentas distintas. La
   consulta más navegacional que existe — el teléfono de otra empresa — recibía el escudo diseñado
   para la marca propia.
2. **La marca se reconoce por frase, no por token suelto.** En una florería cuya marca contiene la
   palabra «floral», el dueño marca ese token como marca — que es la respuesta correcta a la pregunta.
   Resultado: `arreglo floral santiago`, `arreglo floral rancagua`… es decir **la categoría de producto
   entera** quedaba intocable para siempre, y además disparaba una falsa alarma de «tu página está
   rota» **[medido]**.

**Uso diagnóstico, no punitivo:** si tu marca propia tiene ≥ 10 clics y cero conversiones mientras la
cuenta convierte, eso no es un problema de palabra — es la señal más barata que existe de que la
medición o la página se rompió.

### G2 — Irrelevancia dura → negativa, sin importar el volumen

Sólo entra lo que no depende de ningún dato: la consulta es de otro negocio.

🚨 **Aquí es donde el auditor se humilla, y es el error que más veces vimos.** Una lista de
marketplaces aplicada como negativa **por substring**:

```
mercadolibre|falabella|ripley|aliexpress|amazon|temu|yapo
```

`temu` coincide dentro de **TEMUCO**. En la florería, eso negativaba `flores a domicilio temuco`
(2 conversiones) y `florería en temuco con despacho` (1 conversión): **12.847 CLP, 23 clics, 3
conversiones, CVR 13,0 % contra 9,4 % de la cuenta [medido]**. Y coincide en **4 de 4 cuentas**:
`fumigación temuco`, `adocretos temuco`, `vigilante privado temuco`.

De la misma familia, todos medidos en cuentas reales:

- `usad[oa]s?` coincide dentro de **`extrusado`** → el nombre de un raticida.
- `free` coincide con **`freesia`** — una flor, en una florería — con `Bird Free`, marca de producto,
  y con **`zodiac freerider`**, el modelo de un limpiafondos de piscina: 43 términos y **4 conversiones**
  en un e-commerce **[medido]**.
- `trabajo` coincide con `trabajos de poda de árboles`: en Chile «trabajos de poda» es **el servicio
  central**, la consulta comercial más valiosa de esa cuenta. Y en la ferretería coincide con `guantes
  de trabajo`, `botas de trabajo`, `casco trabajo` — el catálogo entero de protección personal.

**Las tres reglas que lo impiden:**

1. **Frontera de palabra, siempre.** `\btemu\b` nunca toca Temuco.
2. **Muestra la lista completa de lo que vas a matar** — con costo, clics y conversiones de cada
   término — y pide confirmación sobre **los términos**, no sobre la etiqueta del balde. Preguntar
   «¿vendes en Temu?» y recibir «no» es hacer la pregunta correcta sobre el objeto equivocado.
3. **Un balde con ≥ 1 conversión en el propio archivo nunca se negativa en bloque.** Se convierte en
   pregunta.

### G3 — Geografía fuera de cobertura

Candidato sólo si el topónimo no está en la lista declarada en P1 **y** ningún término con ese
topónimo convirtió. **[medido]** en la ferretería los términos geo-fuera eran el 0,10 % del gasto y uno
de ellos convertía; en la de seguridad, **2 de las 9 conversiones de la cuenta venían de una ciudad
«fuera de cobertura»**. La geografía parece limpia y no lo es.

Y el arreglo correcto casi nunca es negativar: si llega volumen de afuera, el defecto está en la
**segmentación de ubicación** de la campaña — probablemente en «presencia o interés» — y eso se
arregla en una pantalla, no con 40 negativas.

### G4 — Elegir la línea base (antes de cualquier prueba de rendimiento)

```
CVR base = grupo de anuncios   si tiene ≥ 30 clics
           campaña             si no, y tiene ≥ 100 clics
           cuenta              último recurso, y hay que DECIRLO en la salida
```

**Prueba de heterogeneidad, obligatoria:** si la dispersión de CVR entre grupos con ≥ 50 clics supera
**3×**, queda **prohibido** usar la línea base de cuenta. **[medido]** cuentas sanas: 2,1× a 2,9×.
Cuenta rota: **infinita** (un grupo a 10,09 %, otro a 0,00 %).

⚠️ **Mide la dispersión también en valor, no sólo en CVR.** En la florería la dispersión de CVR era
2,92× («homogénea, usa la cuenta») mientras la de **ROAS era 30× y hasta infinita** entre grupos
**[medido]**. La cuenta era económicamente bimodal y la prueba declaraba que no lo era.

### G5 — Salud del contenedor (el portón que responde «¿es la palabra o es la página?»)

Corre por grupo de anuncios **antes** de juzgar cualquier término dentro de él.

```
esperado = clics del contenedor × CVR de referencia
           ⚠️ La CVR de referencia aquí es SIEMPRE la de la cuenta entera, nunca la línea base
           que eligió G4. G4 elige una base para juzgar un término DENTRO de su contenedor;
           G5 juzga el contenedor mismo, y usarlo como su propia vara lo declara sano por
           construcción. En una cuenta real la diferencia entre las dos fue de 3,1×.
conv == 0        y esperado ≥ 3  → CONTENEDOR MUERTO
conv < esperado/3 y esperado ≥ 5 → CONTENEDOR ENFERMO
→ ningún término de adentro recibe recomendación por rendimiento.
  El hallazgo sube de nivel: la página, la oferta, el teléfono o la etiqueta de ESE grupo.
```

**[medido]** Cero falsos positivos en 44 contenedores sanos de cuatro cuentas; y en la cuenta rota,
3 de 7 grupos detonaron, conteniendo **1.524.359 CLP = 67 % del gasto**. El mayor: 3.597 clics,
47,1 conversiones esperadas, **1,0 observada**.

⚠️ **Pesa el valor, no sólo la cuenta de conversiones.** Un grupo con 3 conversiones cuyo valor total
son **3 pesos** salía «OK» en este portón **[medido]** — cuando es justamente la señal de medición rota
que el portón existe para encontrar.

### 🚨 G5 no sólo excluye recomendaciones: excluye el contenedor muerto de TODOS los promedios

Esta es la regla que más fácil se olvida, y la que más resultados falsos produce.

> Un contenedor muerto o enfermo **sale de todo cálculo agregado que venga después**: de la línea
> base de G6, de la comparación de concordancias (5.2), de la auto-competencia (5.3), y de cualquier
> CVR o CPA de referencia. No sólo deja de recibir recomendaciones — **deja de votar**.

**Por qué, medido en una cuenta real:**

- **G6 sin la exclusión** daba `r = 0,03` para el bloque informacional: «el bricolaje es basura
  absoluta». **Con la exclusión, `r = 0,46`** — es decir, exactamente el resultado que este mismo
  documento usa como ejemplo de que el bricolaje **no** es basura. El contenedor muerto, al arrastrar
  miles de clics con cero conversiones, hundía la CVR de referencia y hacía que todo lo demás
  pareciera malo.
- **5.2 sin la exclusión** producía un «exceso de concordancia» del que **el 86,8 % era el mismo
  dinero** del contenedor muerto, sólo que mirado por otro eje. Dos hallazgos, un solo problema.

**Cómo hacerlo:** identifica los contenedores muertos/enfermos **primero**, apártalos, y recién
entonces calcula las líneas base y los ejes agregados sobre lo que queda. El gasto apartado no
desaparece del informe — es el hallazgo nº 1, con su propio dinero.

### G6 — Intención (informacional, bricolaje, investigación) → casi nunca negativa

```
r = CVR del balde ÷ CVR base
r ≥ 0,70                       → normal, nada que hacer
0,30 ≤ r < 0,70, con volumen   → SEPARAR en campaña propia y bajar la puja en (1−r). Nunca negativar.
r < 0,30, con volumen          → candidato a negativa del balde, tras confirmación
r = 0,  con volumen            → negativa del balde
```

**[medido]** y esto corrige el sentido común del mercado. Todo el mundo «sabe» que en control de plagas
el bricolaje (`cómo eliminar chinches`) es basura. En el período en que esa cuenta funcionaba: **325
clics, 11 conversiones, CVR 3,38 %** contra 7,30 % de la cuenta → r = 0,46. Es significativamente peor
que la cuenta **y aun así no es basura**: negativarlo en bloque costaba ~11 conversiones cada dos
meses. Lo correcto es puja propia al ~46 %. Es una cuenta de margen, no un juicio moral sobre la
palabra «cómo».

Y el balde varía **200× entre rubros del mismo dueño**: 40,5 % del gasto en plagas, 0,2 % en la
ferretería, 0 % en la florería. Ningún prejuicio de rubro sobrevive: hay que medirlo en cada archivo.

### G7 — CPC fuera de escala → problema de puja, **nunca** negativa

```
CPC del término > 5 × CPC mediano del grupo  Y  costo ≥ 1 CPA
   → veredicto LANCE/CALIDAD. Prohibido emitir negativa en este portón.
```
Mediana, no promedio: el promedio queda secuestrado por el propio caso extremo. **[medido]** en la
ferretería, **el 51,1 % del gasto estaba en el 5,1 % de los clics**; una engrapadora costó 3.054 CLP en
un solo clic — y es un producto central. El defecto es haber pagado 3.054 por un clic de 13, no la
palabra.

🚨 **Trampa medida:** este portón, escrito para *proteger* al término caro-pero-bueno, terminó
recomendando **estrangular el mejor término de una cuenta**: en una florería, `flores a domicilio`
(51 clics, 13,13 conversiones, CVR 25,7 % contra 24,7 % de la cuenta) salió como «CPC anómalo → baja la
puja», y era la única acción de todo el informe **[medido]**. La corrección: si el término tiene CVR o
ROAS **iguales o mejores** que su línea base, el veredicto no es «baja la puja» sino **«averigua por
qué su CPC diverge»** — y la causa suele ser la auto-competencia de la Fase 5.3.

### G8 — Rendimiento puro (el portón que casi nunca abre)

Sólo llega aquí lo que costó dinero, no es marca, es relevante, es de tu geografía, está en un
contenedor **sano**, tiene intención transaccional y CPC normal.

```
conversiones esperadas ≥ 3,0  y  observadas == 0   → negativa por rendimiento (la única legítima)
conversiones esperadas ≥ 3,0  y  CVR < base/3      → bajar puja, no negativar
esperadas < 3,0                                    → «SIN EVIDENCIA», a un anexo agregado
```

Las conversiones esperadas se calculan como **el menor** de (clics × CVR base) y (costo ÷ CPA base):
el primero es la prueba de muestra, el segundo la prueba de dinero, y el menor de los dos es el piso
honesto.

**[medido]** Cantidad de términos que llegaron hasta aquí en las cuatro cuentas: **cero**. El skill
tiene que saber decirle al dueño, en la cara: *«ninguno de tus 400 términos tiene datos suficientes
para ser negativado por rendimiento; el dinero está en otra parte.»*

### Un ajuste honesto de la CVR estimada

Con muy pocos clics, la mejor estimación de la CVR de un término **no es cero**, es casi la de la
cuenta. Con un prior empírico de fuerza `k ≈ 40` clics equivalentes — el valor ajustado por máxima
verosimilitud en cuatro cuentas dio entre 30 y 80, notablemente estable entre rubros **[medido]**:

```
CVR estimada = (conversiones + k × CVR_base) ÷ (clics + k)
```

En una cuenta que convierte al 8,25 %, un término con **cero conversiones en 2 clics** — que es la
mediana de los «cero conversiones» — se estima en **7,93 %**. El dato movió la estimación un 4 %.
Negativarlo es tirar un término que sigue pareciendo normal.

---

## 8. Fase 5 (bis) — Los cuatro hallazgos que no viven en la fila

Las compuertas juzgan términos. **El dinero grande no está en los términos.** Estos cuatro ejes se
calculan sobre el mismo archivo y ninguno necesita evidencia estadística: son identidades contables.

⚠️ **Pero cada uno tiene una condición previa, y si no se cumple el eje es `NO EVALUABLE` — nunca
cero, nunca silencio.** Confundir «lo medí y no hay nada» con «no pude medirlo» es la traba 19 de este
mismo documento, y es fácil violarla aquí:

| eje | condición previa | si no se cumple |
|---|---|---|
| 5.1 contenedor muerto | **≥ 2 grupos de anuncios** con gasto | con uno solo el test se compara consigo mismo y sale «sano» siempre → `NO EVALUABLE` |
| 5.2 concordancia | ≥ 2 tipos de concordancia con ≥ 5 conversiones cada uno | `NO EVALUABLE` |
| 5.3 auto-competencia | **≥ 2 campañas** en el archivo | `NO EVALUABLE` — no es que no haya: es que no puede haberla |
| 5.4 concentración de valor | una dimensión de agrupación con ≥ 3 grupos y columna de valor | `NO EVALUABLE` |

**[medido]** en una cuenta real con 107 campañas, **una sola** producía términos de búsqueda (el resto
era Performance Max y Shopping, que no generan filas de término). El archivo traía una campaña y un
grupo, y **tres de los ejes quedaron sin poder evaluarse**. Un informe que ahí escribe «no encontré
auto-competencia» está mintiendo con números correctos.

⚠️ **5.4 no tiene columna de ubicación.** El informe de términos de búsqueda no trae ciudad ni región:
la concentración de valor se calcula sobre **campaña o grupo de anuncios**, que es la agrupación que el
archivo sí tiene. Deducir la ciudad leyendo el texto del término cubre una fracción del gasto y no es
una medición — si lo haces, dilo y di qué fracción cubriste.

### 5.1 — Contenedor muerto
Ya cubierto en G5. Es el hallazgo nº 1 en cuentas rotas.

### 5.2 — Tipo de concordancia
Es una **columna del export** y casi nadie la mira. **[medido]** en la florería:

| concordancia | gasto | conversiones | CPA |
|---|---|---|---|
| exacta | 356.713 | 105,6 | **3.378** |
| frase | 48.146 | 13,4 | 3.602 |
| amplia + frase cercana | 620.782 | 115,9 | **5.358** |

Exceso: **229.441 CLP = 15,7 % del gasto**, con evidencia sólida (n = 116 conversiones, no n = 2). Y
explica lo que parece fatalidad: la mediana de 1–2 clics por término, que impide decidir cualquier
cosa, **es la cola de la concordancia amplia** — se arregla en una pantalla.

**Los valores que trae el export son más que tres.** No agrupes a ojo: usa los que aparezcan, y
declara cuáles encontraste. Los habituales, del más estricto al más suelto:

| valor en el archivo | qué es |
|---|---|
| `Exact match` | exacta |
| `Exact match (close variant)` | exacta con variante cercana — **no es exacta**: aquí Google ya interpretó |
| `Phrase match` | frase |
| `Phrase match (close variant)` | frase con variante cercana |
| `Broad match` | amplia |
| `AI Max` | expansión automática de Google — es la más suelta de todas, y es reciente |

⚠️ **`AI Max` y las «close variant» son las que más crecen y las que casi ningún análisis mira.**
**[medido]** en una cuenta real, `Exact match (close variant)` era el 14,3 % del costo y `AI Max`
una cuarta parte de las filas. Si tu tabla sólo tiene tres filas, ese gasto se te escapa o lo metes en
el balde equivocado.

⚠️ **Compara CPA sólo dentro del mismo bloque.** Mezclar los términos de marca con los que no lo son
en la misma comparación produce un exceso falso: la marca convierte barato por definición, y arrastra
el promedio. Separa marca de no-marca antes de comparar concordancias. **Y saca antes los contenedores
muertos** (ver G5): sin eso, el «exceso» que calcules puede ser en su mayoría el mismo dinero de otro
hallazgo — **86,8 % en una cuenta real [medido]**.

**La fórmula del exceso**, para que dos auditores lleguen al mismo número:

```
referencia = el CPA de la concordancia más estricta que tenga ≥ 5 conversiones
exceso     = Σ  conversiones(bloque) × ( CPA(bloque) − CPA(referencia) )
             sobre los bloques cuyo CPA supere el de referencia
```

Se declara siempre junto con **cuántas conversiones lo sostienen**: un exceso apoyado en n = 3 no es
un hallazgo, es ruido caro de escribir. Y es un **excedente frente a la mejor práctica de la propia
cuenta**, no un ahorro garantizado: bajar la concordancia amplia también baja volumen, y eso hay que
decirlo en la misma frase.

### 5.3 — Auto-competencia entre campañas
El mismo término servido por varias campañas, comprado a precios distintos por ti mismo.
**[medido]** en la florería: **452 términos (48,4 % del gasto)** servidos por más de una campaña, con
CPC de 67 a 1.607 para la misma consulta (**24×**), y hasta 56× en otra. Sobrecosto contra el CPC más
barato que **tu propia cuenta** ya consigue: **266.105 CLP = 18,2 %** — nueve veces más que todo lo que
el auditor recomendaba tocar.

⚠️ Este hallazgo **se destruye si deduplicas antes de buscarlo**. Por eso la Fase 1 manda guardar la
vista sin sumar.

### 5.4 — Concentración de valor por zona o segmento
**[medido]** en la florería: 538.859 CLP en la capital a ROAS 5,88 contra 142.117 CLP en tres regiones
a ROAS 16,7–20,1. El movimiento de dinero más grande del archivo, y no aparecía en ningún bloque de la
salida porque todos los portones contaban conversiones sin pesarlas.

---

## 9. Fase 6 — Simulación de daño (obligatoria antes de emitir una negativa)

Toda negativa propuesta se aplica **en simulación** contra el archivo completo:

> Si el match captura **cualquier** término con conversiones > 0, la negativa se descarta y se reporta
> como «daño evitado».

**[medido]** una negativa `flores` en concordancia de frase mataba `flores a domicilio rancagua`:
172 clics, 22,97 conversiones.

La negativa se propone siempre **exacta sobre el término**, nunca amplia, nunca sobre un token suelto.
Y antes de emitirla, se contrasta con el export de negativas existentes (pedido nº 4): para no repetir
una que ya está, y para encontrar la negativa vieja que hoy está matando un término bueno.

---

## 9 bis. Fase 7 — Dos períodos: qué cambió, y dónde

Un solo archivo dice **cómo está** la cuenta. Dos archivos dicen **qué pasó**, que es la pregunta por
la que alguien paga una auditoría. Pide el mismo informe de términos, mismo formato, con la ventana
anterior de **igual duración** (90 días contra 90 días, nunca 90 contra 30).

### La regla que ordena todo: descomponer ANTES de comparar

> **Nunca compares dos promedios de cuenta y saques una conclusión.** Un promedio se mueve por dos
> razones distintas — porque algo empeoró, o porque cambió el peso de las partes — y desde arriba las
> dos se ven idénticas.

Baja siempre en este orden, y **detente en el primer nivel donde la diferencia se explique**:

```
cuenta  →  tipo de campaña  →  campaña  →  grupo de anuncios  →  familia de token
```

En cada nivel, para cada parte, mira **tres cosas juntas**: su métrica, su **participación en el
gasto**, y si existía en las dos ventanas.

- Si las participaciones se movieron mucho y las métricas de cada parte casi no → **es mezcla**. La
  cuenta no empeoró: cambió de forma. Decirlo así vale más que cualquier lista.
- Si las participaciones se mantuvieron y una parte se derrumbó → **es esa parte**. Ahí está el
  informe entero.

### Un caso real, medido

Misma cuenta, dos ventanas contiguas de 90 días, gasto casi idéntico (6,19 M contra 6,43 M):

| | ventana A | ventana B |
|---|---|---|
| clics | 12.938 | 20.833 |
| conversiones | 487,0 | 335,2 |
| **CVR de la cuenta** | **3,76 %** | **1,61 %** |

Leído desde arriba: «la cuenta se derrumbó a la mitad». Verdadero, y **inútil**. Al bajar un nivel, la
mezcla resulta ser casi idéntica — Búsqueda 74,3 % → 74,1 %, Performance Max 24,5 % → 25,0 % — así que
no es mezcla. Y al bajar al nivel de campaña aparece el informe de verdad:

| campaña | CVR A | CVR B |
|---|---|---|
| campaña principal de servicio | 3,58 % | **0,00 %** |
| Performance Max | 1,42 % | **0,02 %** |
| campaña hermana, mismo período | 10,19 % | **15,21 %** |

**Dos campañas fueron exactamente a cero mientras una hermana mejoró.** Eso no es mercado, no es
estacionalidad y no son las palabras: en el mismo período, con la misma cuenta y el mismo negocio, una
parte siguió funcionando mejor que antes. Dos campañas cayendo a **cero exacto** mientras la vecina
sube es la firma de una **medición rota acotada a esas campañas** — su acción de conversión, su
etiqueta, su página de destino o su teléfono.

Y fíjate en lo que el promedio de la cuenta escondía: **había una campaña mejorando 50 %.**

### Las trampas de comparar dos ventanas

| trampa | qué hacer |
|---|---|
| **Ventanas de distinta duración** | rechaza la comparación. 90 contra 30 no se compara ni normalizando: la estacionalidad no es lineal |
| **Estacionalidad** | compara contra el **mismo período del año anterior** cuando el negocio la tenga (flores, regalos, climatización). Si sólo tienes el trimestre anterior, dilo |
| **Conversiones que aún no maduraron** | la ventana más reciente siempre subestima: hay conversiones que se atribuyen días después del clic. Nunca declares una caída basándote en los últimos 7–14 días |
| **La cuenta cambió de columna de conversión** | si las dos ventanas usan definiciones distintas, no estás comparando lo mismo. Revisa la divergencia entre columnas **en cada ventana por separado** |
| **Partes que nacen o mueren** | campaña que no existía en A infla o desinfla B sin que nada haya «cambiado». Sepáralas y repórtalas aparte |

---

## 9 ter. Fase 8 — El historial de cambios: relacionar lo que pasó con lo que alguien hizo

Hasta aquí el informe dice *qué* cambió. Esto dice *por qué*, y es lo único que convierte
«tu cuenta empeoró» en **«tu cuenta empeoró cuando se hizo esto, el 14 de julio»**.

> Herramientas y configuración → **Historial de cambios** → el mismo rango de las dos ventanas →
> Descargar.

No necesita API ni permisos especiales: cualquiera con acceso a la cuenta lo descarga.

### Lo que trae, y la trampa de contarlo mal

Cada fila trae **cuándo · quién (correo) · desde dónde (interfaz web o una herramienta/API) · qué tipo
de cosa · qué operación (crear/editar/quitar) · qué campos cambiaron · en qué campaña y grupo**.

🚨 **Una decisión humana produce muchas filas. Colapsa antes de contar.** **[medido]** en una cuenta
real, **80 filas eran 10 acciones** — una razón de **8 filas por decisión**, y una sola edición de
horarios de anuncios generó **47 filas**. Un informe que dice «hubo 80 cambios» está describiendo
diez.

Colapsa agrupando por **(mismo minuto + mismo usuario + mismo tipo de recurso + misma operación +
mismos campos)**. Cada grupo es una acción; el tamaño del grupo es su alcance, no su frecuencia.

**Y mira la columna de origen.** Distingue a una persona en la interfaz de una herramienta
automática: en la cuenta medida, **61 de 80 filas venían de una API** y 19 de la interfaz web. «Tu
agencia tocó la cuenta 80 veces» y «una herramienta aplicó una regla automática» son diagnósticos
opuestos, y la columna lo dice sin ambigüedad.

### Cómo se relaciona con la métrica — y dónde está el precipicio

1. Pon en una línea de tiempo las **acciones colapsadas** y las **quiebras de métrica** por campaña.
2. Quédate sólo con las acciones que ocurren **en la misma campaña** donde la métrica se movió, y
   **antes** del movimiento. Una acción posterior no puede ser la causa.
3. Reporta **coincidencia, nunca causa**: *«el CVR de esta campaña cae a cero la semana siguiente a
   que se editara su acción de conversión»*. Es una hipótesis con fecha, y es enormemente más útil que
   una lista de palabras — pero sigue siendo una hipótesis.

🚨 **Las tres trampas, y son fáciles de pisar:**

- **Una cuenta activa se toca todas las semanas.** Siempre habrá algún cambio cerca de cualquier
  quiebre. Que exista un cambio antes **no es evidencia**: exígete que sea en la **misma campaña** y
  del **tipo capaz** de producir ese efecto.
- **Lo que más rompe la medición no aparece en este historial.** Cambiar el sitio, el formulario, el
  número de WhatsApp o una etiqueta pasa **fuera** de Google Ads. Si el historial no explica el
  quiebre, la respuesta más probable es esa — y es exactamente la pregunta P5 de la entrevista.
- **Ausencia de cambios no prueba inocencia**, prueba que nadie tocó *este* panel.

### 🚨 Antes de leer una sola fila: ¿el archivo cubre el período que te importa?

Un historial vacío tiene **dos significados opuestos**, y confundirlos es fácil porque los dos se ven
igual: un archivo sin filas.

| lo que pasa | qué significa | qué escribes |
|---|---|---|
| 0 filas, y el rango del archivo **sí cubre** las dos ventanas | evidencia real de que **nadie tocó esta cuenta** en ese período. Es un hallazgo | *«nadie modificó la cuenta en el período; lo que cambió, cambió afuera»* |
| 0 filas, y el rango del archivo **no cubre** las ventanas | el archivo **no sirve para esta pregunta**. No es evidencia de nada | *«el historial que tengo cubre <rango>, y el quiebre está en <fecha>. Necesito el historial de ese período»* — y vuelves a pedirlo |
| hay filas, pero el rango no cubre el quiebre | igual que arriba: no puedes relacionar nada | lo mismo |

**Lo primero que haces con este archivo es leer su rango** —está en la segunda línea del preámbulo— y
compararlo con las ventanas. Si no se superponen, la Fase 8 no corre y lo dices; no la corras «con lo
que hay».

⚠️ **Este archivo es la única razón por la que descargar de la interfaz gana.** La API de Google Ads
sólo devuelve el historial de los **últimos 30 días** — está medido: pedir más devuelve
*«The requested start date is too old»*. La interfaz cubre un rango mucho mayor. Para esta pregunta,
el que baja CSV ve más que el que consulta la API.

---

## 10. Las trabas — lo que este skill NUNCA hace

1. Negativar la marca propia, una variante mal escrita, el dominio o una consulta navegacional.
2. Proteger como «navegacional» el teléfono, el dominio o la dirección de **otra empresa**.
3. Negativar por substring sin frontera de palabra.
4. Negativar un término con cero clics.
5. Negativar cuando las conversiones esperadas son menos de 3. En 63.000 términos medidos, eso
   significa: casi nunca.
6. Negativar cualquier miembro de un grupo en el que **alguna** variante convirtió.
7. Negativar dentro de un contenedor muerto o enfermo: ahí no se está juzgando la palabra.
8. Negativar un balde completo (bricolaje, competencia, geografía) que tenga ≥ 1 conversión.
9. Negativar marca de competencia por defecto. **[medido]** en una cuenta era el **44 % de las
   conversiones**, con CVR superior a la genérica; en otra, el 0,1 % del gasto. Es una decisión de
   inversión con números, nunca una limpieza.
10. Tratar `--` como cero.
11. Tratar una conversión fraccionaria como cero.
12. Contar una conversión de 1 peso igual que una venta: si hay columna de valor, se pesa. Si no la
    hay, se dice que no se pudo pesar.
13. Sumar «gasto desperdiciado» y presentarlo como número de la cuenta.
14. Decir «estos son los términos que gastaron» en vez de «los que Google deja ver».
15. Deducir el rubro del nombre de la cuenta o del dominio.
16. Usar la línea base de la cuenta cuando la dispersión entre grupos supera 3×.
17. Recomendar bajar la puja de un término cuya CVR o ROAS iguala o supera su línea base.
18. Recomendar **pausar una campaña**, mover un presupuesto o tocar la puja de una cuenta que no
    midió. El skill describe la acción; quien la ejecuta eres tú.
19. Presentar «0» y «no pude medirlo» como el mismo valor.
20. Ordenar la salida por costo. Se ordena por **palanca** (§11), y «costo con cero conversiones» ni
    siquiera es un campo de salida.
21. Contar las filas `Total:` como si fueran términos. Son ocho, no una, y meterlas infla la cuenta
    entera **7,18×**.
22. Dar por bueno un archivo que se leyó en **una sola columna**. No es un archivo vacío ni una
    cuenta sin datos: es el delimitador equivocado. «No pude leerlo» y «no hay nada» son cosas
    distintas, y confundirlas es el modo de fallo más caro de todos.
23. Comparar dos ventanas de **distinta duración**, o comparar dos promedios de cuenta sin bajar
    antes por tipo de campaña y por campaña. Un promedio se mueve porque algo empeoró **o** porque
    cambió el peso de las partes, y desde arriba se ven iguales.
24. Declarar una caída usando los **últimos días** de la ventana reciente: las conversiones se
    atribuyen con retraso y esa cola siempre parece peor de lo que es.
25. Decir que un cambio **causó** un resultado. El historial da coincidencia con fecha —
    *«cayó la semana siguiente a esta edición, en esta misma campaña»* — y eso ya es mucho. En una
    cuenta activa siempre hay algún cambio cerca de cualquier quiebre.
26. Contar filas del historial de cambios como si fueran decisiones. Son **8 filas por decisión**
    medidas en una cuenta real, y una sola edición generó 47.
27. Concluir que «nadie tocó nada» porque el historial está vacío. Lo que más rompe la medición —el
    sitio, el formulario, el WhatsApp, una etiqueta— **pasa fuera de Google Ads y no aparece ahí**.

---

## 11. La salida

**Encabezado de honestidad, obligatorio, antes de cualquier hallazgo:**

```
Período · clics de la cuenta · cobertura real sobre el costo TOTAL
Qué columna de conversión se usó y por qué
Qué quedó invisible (PMax, Shopping, términos bajo el umbral de privacidad)
Nivel de confianza y qué export lo subiría
```

**Si hay dos ventanas, el encabezado las declara así** — y el informe abre por lo que cambió, no por
el estado, porque es lo que la persona vino a saber:

```
Ventana A: <fechas> · Ventana B: <fechas> · misma duración: sí/no
La misma columna de conversión en las dos: sí/no  (si no, la comparación no es válida)
Partes que existen en una ventana y no en la otra
Historial de cambios: presente / ausente  → si está ausente, el informe dice QUÉ cambió, nunca POR QUÉ
```

### 🚨 El dinero de los hallazgos se superpone. Nunca lo sumes.

Un mismo peso puede estar dentro de dos hallazgos a la vez: el grupo de anuncios roto y la
concordancia cara suelen ser **el mismo gasto mirado por dos ejes distintos**.

**[medido]** en una cuenta real: contenedor enfermo = 49,6 % del gasto visible; concordancia cara =
59,9 %. Sumados dan **109,5 %**, que es un número imposible y le dice al lector que el informe está
roto. La intersección era 36,4 %: **el 61 % del dinero del segundo hallazgo estaba dentro del
primero.** La unión real era 73,1 %.

**Reglas:**

1. Cada hallazgo declara su dinero **por separado**, y el informe dice, con esas palabras, que **las
   cifras se superponen y no se suman**.
2. Si imprimes un total, imprime la **unión** — el gasto tocado por al menos un hallazgo — y di que es
   una unión.
3. Cuando dos hallazgos comparten más de la mitad del dinero, dilo: *«estos dos son en buena parte el
   mismo gasto visto de dos maneras; arregla primero el de arriba y vuelve a medir»*.

### «No encontré nada» y «no pude mirar» van en líneas distintas

Al cerrar, el informe lista por separado:

- **Evaluado, sin hallazgo** — corriste la prueba, tenía poder, y no había nada. Esto sí es un
  resultado, y es el resultado normal del portón de rendimiento.
- **NO EVALUABLE** — la prueba no pudo correr, y por qué en una frase (un solo grupo de anuncios, una
  sola campaña, falta la columna de valor, ventana demasiado corta).

**Y la frase de cierre tiene que respetar esa diferencia.** «Ninguno de tus términos tiene evidencia
para ser negativado» sólo se puede escribir si el portón de rendimiento **corrió de verdad**. Si tres
de los ejes salieron `NO EVALUABLE`, lo honesto es: *«de los ejes que este archivo permite evaluar,
ninguno produce una negativa defendible; otros tres no pude evaluarlos, y esto es lo que haría falta
para hacerlo»*. La conclusión más fuerte de este documento es también la más fácil de exagerar.

### Si te detuviste en un portón, el informe igual se escribe

Cuando la cobertura o la medición detienen el análisis, la salida **no** es un mensaje de error. Es:
el encabezado de honestidad completo, los hallazgos que no dependen del portón (medición y cobertura
siempre lo son), y una línea explícita: **«Recomendaciones sobre términos: ninguna»**, con la razón en
una frase. Un informe que se detiene sin decir qué sí sabe es indistinguible de uno que falló.

### Qué es «palanca», exactamente

Es el criterio que ordena **toda** la salida, así que no puede quedar a la intuición:

```
palanca = (dinero que mueve × confianza) ÷ (esfuerzo × riesgo de aplicarlo)
```

- **dinero que mueve** — sobre el gasto que el archivo sí ve, no sobre la cuenta entera.
- **confianza** — Alta 1,0 · Media 0,6 · Baja 0,3.
- **esfuerzo** — minutos 1 · horas 2 · días 4.
- **riesgo de aplicarlo** — ninguno 1 · reversible 1,5 · puede romper algo vivo 3.

Por eso arreglar la medición encabeza casi siempre: mueve la cuenta entera, cuesta una hora y no
rompe nada. Y por eso una lista de negativas queda al final aunque sea lo más fácil de escribir: mueve
centésimas, y su riesgo de aplicarla es el más alto de todos.

⚠️ **El resultado es un orden, no una cifra. Nunca lo muestres al cliente como número.** Mezcla pesos
con multiplicadores sin unidad, así que «palanca 2.433.026» no significa nada fuera de esta cuenta y
no se compara con nada. Sirve para decidir qué va primero en el informe — y ahí se acaba. Lo que el
cliente ve es el orden y las cuatro columnas que lo justifican, jamás el número.

### Los hallazgos, ordenados por palanca — no por tamaño. Cada uno con:

| campo | qué dice |
|---|---|
| Hallazgo | qué pasa, en una frase, con el número |
| Dinero | cuánto mueve, y **sobre qué porcentaje del gasto que sí veo** |
| Esfuerzo | minutos, horas o días |
| Riesgo de aplicarlo | qué se puede romper |
| Confianza | Alta / Media / Baja, con la razón |
| Qué NO sé | el pedido de dato que subiría la confianza |

**«No sé» es una respuesta válida y a menudo la correcta.** Se declara cuándo:

| situación | qué haces |
|---|---|
| ventana < 30 días | te niegas a juzgar rendimiento; sólo hallazgos estructurales |
| < 100 clics en el período | ninguna recomendación sobre términos |
| sólo se exportó la columna «Conversiones» | avisas que puedes estar leyendo 1/20 de la realidad |
| ninguna conversión configurada | **paras**: el primer problema es la medición |
| PMax > 50 % del gasto | lo declaras en el encabezado |
| sin período anterior para comparar | todo hallazgo sale marcado *«no distingo término malo de algo que se rompió hace poco»* — **y pide el segundo archivo**: es el export nº 2 y desbloquea la Fase 7, que suele valer más que todo lo demás junto |
| con dos ventanas pero **sin historial de cambios** | puedes decir *qué* cambió y *dónde*, nunca *por qué*. Dilo con esas palabras y pide el export nº 3 |
| **una sola ventana larga** (más de ~120 días) | avisa que puede contener un **cambio de régimen** y estar promediando dos cuentas distintas. Una ventana larga no reemplaza dos ventanas: las suaviza. Pide el archivo partido en dos mitades — es el mismo export, dos veces, y convierte «está roto» en «se rompió tal mes», que es la mitad de la respuesta |

---

## 12. Lo que este skill NO resuelve

Esto no es falsa modestia; es la diferencia entre un diagnóstico y el trabajo.

- **No ejecuta nada.** No toca tu cuenta. Toda acción la aplicas tú, y varias de ellas (separar
  campañas, rehacer la estructura de concordancias, arreglar la medición) son horas de trabajo con
  riesgo real mientras se hacen.
- **No ve el 60–90 % de tu dinero** si tienes Performance Max o Shopping. Ahí no hay términos que
  auditar; hay feed, señales de audiencia, creatividades y estructura de campaña — otro oficio.
- **No arregla tu página.** Cuando el diagnóstico dice «el problema está después del clic» — que es lo
  más frecuente — lo que sigue es rehacer una oferta, una ficha o un formulario. Eso no lo hace un
  auditor, ni un chat.
- **No sabe si contestas el teléfono.** En servicios locales, la mitad de las «no conversiones» es
  atención, no publicidad.
- **No reemplaza tener a alguien mirando la cuenta cada semana.** Un archivo es una foto; una cuenta
  se mueve todos los días.

Si al correrlo descubres que el problema no era ninguna palabra sino la medición, la estructura o lo
que pasa después del clic — y eso es lo que encontramos en las ocho cuentas donde lo calibramos — lo
que necesitas ya no es un auditor. Es alguien que lo ejecute.

---

*Publicado por [herihe.digital](https://herihe.digital) · Agencia Google Partner · Valparaíso, Chile.
Uso libre. Sin credenciales, sin registro, sin enviarnos tus datos: este skill corre dentro de tu
propio Claude o ChatGPT y tu archivo no sale de ahí.*
