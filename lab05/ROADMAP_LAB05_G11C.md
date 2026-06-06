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
- [ ] **Validar control remot de paràmetres** — provar ordre estricte:
      `InsightMaker run (setVar('q', …))` → `run model silent` (esperar 2-3 s) → llegir N.
      *(si `setVar` no funciona, revisar el codi del botó "Activate" per la sintaxi correcta)*
- [ ] **Validar escriptura a Sheets** — `set sheet … name G11C column A row 1 value [prova]`
      i comprovar que apareix a la cel·la A1 del full G11C.

### Pendent ⬜
- [ ] Muntar el **bucle d'escenaris** (vegeu secció 3)
- [ ] Executar tots els escenaris i omplir el full G11C
- [ ] Visualització: gràfics a Sheets i/o dashboard HTML (opcional però recomanat)
- [ ] **Exportar** el projecte Snap! definitiu → `SIM_LAB05_G11C.xml`
- [ ] Redactar el **document breu** amb captures de pantalla
- [ ] Empaquetar el lliurament en `.zip` (xml + doc + extres)

---

## 3. Bucle d'escenaris (versió inicial)

Pseudocodi de blocs d'Snap!. Cal crear abans les variables: `fila`, `Nstar`, `Estar`, `Cstar`.

```
connect insight channel [g11c]

// capçalera (un cop)
set sheet url (url sheet call) name [G11C] column [A] row num [1] value [Parametre]
set sheet url (url sheet call) name [G11C] column [B] row num [1] value [Valor]
set sheet url (url sheet call) name [G11C] column [C] row num [1] value [N*]
set sheet url (url sheet call) name [G11C] column [D] row num [1] value [E*]
set sheet url (url sheet call) name [G11C] column [E] row num [1] value [Captura*]

set [fila] to (2)
for each (v) in (list 0.003 0.006 0.01 0.02 0.05)        // valors de q
    InsightMaker run ( join [setVar('q', ] (v) [)] )      // canvia paràmetre
    run model silent                                      // simula
    wait 2 secs                                           // espera resposta MQTT
    set [Nstar] to ( item (last) of ( split (get [N] values) by , ) )
    set [Estar] to ( item (last) of ( split (get [E] values) by , ) )
    set [Cstar] to ( item (last) of ( split (get [Captura] values) by , ) )
    set sheet url (url sheet call) name [G11C] column [A] row num (fila) value [q]
    set sheet url (url sheet call) name [G11C] column [B] row num (fila) value (v)
    set sheet url (url sheet call) name [G11C] column [C] row num (fila) value (Nstar)
    set sheet url (url sheet call) name [G11C] column [D] row num (fila) value (Estar)
    set sheet url (url sheet call) name [G11C] column [E] row num (fila) value (Cstar)
    change [fila] by (1)
```

Per als altres escenaris, només cal canviar la `list` de valors i el nom del paràmetre dins de `setVar`:

| Escenari | Paràmetre | Valors a provar |
|---|---|---|
| Sensibilitat α | `alpha` | 0.01, 0.1, 0.5, 1.0 |
| Sensibilitat c | `c` | 10, 30, 50, 80 |
| Sensibilitat q | `q` | 0.003, 0.006, 0.01, 0.02, 0.05 |
| Regulació TAC | `Q_max` | 80, 100, 125, 200 |
| Reserva marina | `f` | 0, 0.3, 0.4, 0.5 |
| Efecte Allee | `A` | 0, 100, 200, 350 |

---

## 3b. Visualització / Dashboard (PENDENT — apuntat per fer)

Un cop el full G11C tingui dades dels escenaris, muntar la capa de visualització.
Opcions (de menys a més vistosa):

- [ ] **Opció A — Gràfics natius de Sheets** (ràpid): Inserir → Gràfic → seleccionar
      el rang de cada escenari. Suficient per al lliurament mínim.
- [ ] **Opció B — Apps Script** (automàtic): script que crea/actualitza els gràfics
      automàticament quan arriben dades noves al full. Es pot generar amb IA.
- [ ] **Opció C — Dashboard HTML/React** (el més vistós): pàgina amb gràfics dinàmics
      (Recharts o Chart.js) que llegeix del full via la URL de l'Apps Script.
      Gràfics suggerits: N* vs paràmetre, Captura* vs paràmetre, comparativa d'escenaris.

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
