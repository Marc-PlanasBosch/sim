# Lab05 — Gemell Digital de la Pesquera Schaefer-Smith · Grup 11C

**Full de ruta i estat del projecte** · Simulació 2025-26 · UPC

> Objectiu: convertir el model del Lab03 (pesquera Schaefer-Smith) en un **Gemell Digital**
> automatitzable: controlar-lo remotament des de Snap! via MQTT, llançar escenaris en
> bucle i enviar els resultats a Google Sheets.

---

## 1. Arquitectura

```
Snap! (control) ──[MQTT: imrun]──► Insight Maker (simulació)
      ▲                                   │
      └──────[MQTT: imresp]───────────────┘  (retorna N, E, Captura)
      │
      └──[HTTP GET]──► Google Sheets G11C (visualització)
```

| Component | Funció | Accés |
|---|---|---|
| Insight Maker | Model Schaefer-Smith. Botó "Activate" (MQTT). | insightmaker.com/insight/5nQg4Lnd5zfvCGgeyfZhuN |
| Snap! | Orquestra escenaris: canvia params, simula, escriu a Sheets. | snap.berkeley.edu (projecte importat) |
| Google Sheets | Rep resultats i fa gràfics. Full **G11C**. | GoogleSheet compartit |
| MQTT Broker | Bus de missatgeria. | wss://broker.emqx.io:8084/mqtt |

- **Canal MQTT del grup:** `g11c`
- **Variables del model (noms exactes):** `N` (biomassa), `E` (esforç), `Captura` (flux)
- **Paràmetres:** `r`, `K`, `q`, `p`, `c`, `alpha`, `A`, `f`, `Q_max`
- **Equilibri teòric base:** N* = c/(p·q) · E* = (r/q)(1−N*/K) · Captura* = q·E*·N*
  - (al model carregat `SIM-lab3-q6` el cas base actual convergeix a **N* ≈ 600**)

---

## 2. Estat actual (què hem fet)

### Fet ✅
- [x] **Pas 0** — Bloc de Google Sheets adaptat al full `G11C` (`docu/lab05.xml`)
- [x] Carregat el projecte base del professor (`InsightMaker.xml`) a Snap!
- [x] **Canal** `upc` → `g11c` a tots els blocs `connect …` (punt 1)
- [x] **URL del model** (`insightmaker model url`) → model de pesca (punt 2)
- [x] **Nom del full** `Full-1` → `G11C` als blocs de l'sprite GSheet (punt 4)
- [x] Botó **"Activate"** (MQTT) al model d'InsightMaker → connecta pel canal `g11c`
- [x] Snap! connecta: `state insight = Connected`
- [x] `run model silent` executa la simulació remotament
- [x] `get [N] values` retorna la sèrie temporal (convergeix a ~600)
- [x] Extracció de l'últim valor: `item (last) of (split (get [N] values) by ,)` → 600
- [x] Confirmats els noms reals de variables i paràmetres del model

### En curs ⏳
- [x] **Control remot de paràmetres VALIDAT** — sintaxi correcta:
      `InsightMaker run ( setValue(findName('q'), 0.005) )` → `run model silent` → esperar → llegir N.
      ⚠️ **`setVar(...)` NO funciona** en aquest model; cal **`setValue(findName('nom'), valor)`**.
- [x] **Escriptura a Sheets VALIDADA** — `set sheet url (url sheet call) name [G11C] column A row 1 value [prova]`.
      ⚠️ Cal usar la variable **`url sheet call`** (la URL `/exec` de l'Apps Script),
      **NO** `url sheet document` (la URL de docs.google.com no escriu res).

### Pendent ⬜
- [ ] Muntar el **bucle d'escenaris** (vegeu secció 3)
- [ ] Executar tots els escenaris i omplir el full G11C
- [x] Visualització: gràfics a Sheets i/o dashboard HTML (implementat via dashboard HTML)
- [ ] **Exportar** el projecte Snap! definitiu → `SIM_LAB05_G11C.xml`
- [ ] Redactar el **document breu** amb captures de pantalla
- [ ] Empaquetar el lliurament en `.zip` (xml + doc + extres)

---

## 3. Bucle d'escenaris — GUIA PAS A PAS

> ✅ La cadena està 100% validada (connexió MQTT, control remot de paràmetres i
> escriptura a Sheets funcionen). Aquí teniu com muntar i executar el bucle.
> Es construeix a l'sprite **`Sim`**.

### Requisits previs (cada sessió de treball)
1. Obrir el projecte Snap!: **File → Import** del nostre `SIM_LAB05_G11C.xml`
   (⚠️ NO obrir el link del professor, que carrega l'original i perd els canvis).
2. Obrir el model d'Insight Maker en una altra pestanya i clicar el botó **"Activate"**
   → confirmar canal `g11c` → ha de sortir "Campana digital habilitada".
3. Comprovar que la variable **`url sheet call`** conté la URL `/exec` de l'Apps Script
   (`https://script.google.com/macros/s/AKfycby8.../exec`).

### Pas 1 — Variables ja creades
Les variables del bucle ja estan creades al Snap: `fila`, `Nstar`, `Estar`, `Cstar`, `escenaris`, `nom_param` i `llista_valors`.

- `escenaris`: llista dels escenaris a executar
- `nom_param`: nom del paràmetre actiu dins de cada escenari
- `llista_valors`: valors del paràmetre que es recorreran al bucle

### Pas 2 — Muntar el bucle

```
connect insight channel [g11c]
set [fila] to (2)
for each (nom_param) in (escenaris)
      set [llista_valors] to (...)          ← assigna aquí la llista de valors de l'escenari actual
      for each (v) in (llista_valors)
            InsightMaker run ( join [setValue(findName(] (nom_param) [), ] (v) [)] )
            run model silent
            wait (3) secs
            set [Nstar] to ( item (last) of ( split (get [N] values) by , ) )
            set [Estar] to ( item (last) of ( split (get [E] values) by , ) )
            set [Cstar] to ( item (last) of ( split (get [Captura] values) by , ) )
            set sheet url (url sheet call) name [G11C] column [A] row num (fila) value (nom_param)
            set sheet url (url sheet call) name [G11C] column [B] row num (fila) value (v)
            set sheet url (url sheet call) name [G11C] column [C] row num (fila) value (Nstar)
            set sheet url (url sheet call) name [G11C] column [D] row num (fila) value (Estar)
            set sheet url (url sheet call) name [G11C] column [E] row num (fila) value (Cstar)
            change [fila] by (1)
```

**Notes de muntatge (on és cada bloc):**
- `for each (item) in ( )` → **Control**. Fes servir el primer per recórrer `escenaris` i el segon per recórrer `llista_valors`.
- `list` → **Variables** o blocs d'inicialització equivalents, segons com tinguis guardades les llistes.
- `join` → **Operators**, amb **3 trossos**: text `setValue(findName(` · variable `nom_param` · text `), ` i després el valor `v`.
- `split … by ,` → **Operators** (escriu la coma a la 2a ranura).
- `item (1) of` → **Variables**; posa el desplegable a **`last`**.
- `connect insight channel`, `run model silent`, `get … values`, `InsightMaker run`
  → categoria **"Cicle de l'aigua"**.
- `set sheet url …` → categoria **"Google Sheets"**. ⚠️ USAR SEMPRE `url sheet call`
  (NO `url sheet document`, que no escriu res).

### Pas 3 — Provar amb 2 valors i COMPROVAR
Amb el model actiu, clica el bloc sencer (a partir de `connect…`). Espera ~10 s.
Al full **G11C** han d'aparèixer 2 files:

| fila | A | B | C (N*) | D (E*) | E (Captura*) |
|---|---|---|---|---|---|
| 2 | q | 0.005 | ~800 | … | … |
| 3 | q | 0.01 | ~600 | … | … |

✔️ Si surten les 2 files amb números coherents → el bucle funciona.
✖️ Si una fila surt buida → augmenta el `wait` (la simulació no havia acabat de respondre).

### Pas 4 — Escenari complet (q)
Canvia la `list` als 5 valors reals: `0.003 0.006 0.01 0.02 0.05` i torna a executar.

### Pas 5 — Resta d'escenaris
Per a cada escenari, canvia NOMÉS dues coses: el nom dins de `findName('...')` i la `list`.
(Opcional: ajusta `set [fila] to (...)` perquè cada escenari escrigui en files diferents,
o afegeix una columna amb el nom del paràmetre.)

| Escenari | `findName('…')` | `list` de valors |
|---|---|---|
| Sensibilitat α | `alpha` | 0.01 0.1 0.5 1.0 |
| Sensibilitat c | `c` | 10 30 50 80 |
| Sensibilitat q | `q` | 0.003 0.006 0.01 0.02 0.05 |
| Regulació TAC | `Q_max` | 80 100 125 200 |
| Reserva marina | `f` | 0 0.3 0.4 0.5 |
| Efecte Allee | `A` | 0 100 200 350 |

> 💡 Capçalera (opcional, un cop): escriure a la fila 1 els títols
> `Parametre | Valor | N* | E* | Captura*` amb 5 blocs `set sheet … row num [1]`.

---

## 3b. Visualització / Dashboard (PENDENT — apuntat per fer)

Un cop el full G11C tingui dades dels escenaris, muntar la capa de visualització.
Estat actual: **Opció C implementada** amb el fitxer autònom [dashboard.html](dashboard.html).

Opcions (de menys a més vistosa):

- [x] **Opció A — Gràfics natius de Sheets** (ràpid): Inserir → Gràfic → seleccionar
      el rang de cada escenari. Suficient per al lliurament mínim.
- [x] **Opció B — Apps Script** (automàtic): script que crea/actualitza els gràfics
      automàticament quan arriben dades noves al full. Es pot generar amb IA.
- [x] **Opció C — Dashboard HTML/React** (el més vistós): pàgina amb gràfics dinàmics
      (Recharts o Chart.js) que llegeix del full via la URL de l'Apps Script.
      Gràfics suggerits: N* vs paràmetre, Captura* vs paràmetre, comparativa d'escenaris.

Implementació actual:
- Dashboard autònom integrat a [dashboard.html](dashboard.html)
- KPI clau i gràfics dinàmics amb Chart.js
- Pestanyes per escenaris de sensibilitat
- Estructura preparada per connectar-se a dades del full G11C via GET si es vol automatitzar

> Idea: demanar a una IA que generi el dashboard HTML o l'Apps Script a partir de
> l'estructura del full (columnes: Parametre · Valor · N* · E* · Captura*).
> L'enunciat permet explícitament usar eines d'IA per crear aquests entorns.

---

## 4. Recursos

- Model Base (Insight Maker): https://insightmaker.com/insight/5nQg4Lnd5zfvCGgeyfZhuN
- Exemple MQTT (codi botó): https://insightmaker.com/insight/3HpQnor3q1sLXbwOGvNskL
- Projecte Snap! base: https://snap.berkeley.edu/snap/snap.html#open:https://xavierpi.com/proto/InsightMaker.xml
- API JavaScript Insight Maker: https://insightmaker.com/sites/default/files/api/files/API-js.html
- Broker MQTT: wss://broker.emqx.io:8084/mqtt

---

## 5. Notes de treball

- El link del projecte del professor **sempre carrega l'original**: per continuar, fer
  `File → Import` del nostre `SIM_LAB05_G11C.xml`, no obrir el link.
- El model d'Insight Maker ha d'estar **obert en una pestanya amb "Activate" clicat**
  mentre Snap! envia ordres (Insight Maker no és un servidor).
- Després de `setVar` cal **tornar a fer `run model silent`** i esperar abans de llegir.
