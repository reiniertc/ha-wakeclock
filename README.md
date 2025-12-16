# WakeClock – Home Assistant custom integration

WakeClock is een eenvoudige, scriptbare wekker-integratie voor Home Assistant.
Geen UI, geen helpers: alles is aan te sturen via services en automations.

De integratie maakt **twee entiteiten** aan:

- `switch.wakeclock` – aan/uit + configuratie via attributen
- `sensor.wakeclock_nextalarm` – timestamp van het volgende alarm (altijd beschikbaar)

---

## Functionaliteit

- Wekker met **weekschema** (`ma` t/m `zo`)
- Eén centrale **next alarm**-tijd
- **Snooze** (stapelbaar, vaste minuten)
- Volledig te bedienen via **services**
- Sensor met `device_class: timestamp` → ideaal voor automations

---

## Installatie (via HACS)

1. Zorg dat de repository **public** is op GitHub  
   ```
   https://github.com/reiniertc/ha-wakeclock
   ```

2. In Home Assistant:
   - HACS → Integraties → **Aangepaste repositories**
   - URL: `https://github.com/reiniertc/ha-wakeclock`
   - Categorie: **Integratie**
   - Branch: `main`

3. Installeer **WakeClock**
4. **Herstart Home Assistant**
5. Ga naar:
   - Instellingen → Apparaten & diensten → **Integratie toevoegen**
   - Zoek **WakeClock**
   - Toevoegen (geen configuratie nodig)

---

## Entiteiten

### `switch.wakeclock`

Gebruik:
- Aan = wekker actief
- Uit = wekker uit (planning blijft behouden)

**Attributen:**

| Attribuut | Betekenis |
|---------|-----------|
| `snoozetime` | Snooze in minuten |
| `nextalarm` | ISO datetime string |
| `ma`..`zo` | Wektijd per dag (`HH:MM` of leeg) |

---

### `sensor.wakeclock_nextalarm`

- `device_class: timestamp`
- **State** = volgende alarmtijd (UTC)
- Blijft gevuld, ook als de switch uit staat

**Extra attribuut:**

| Attribuut | Voorbeeld |
|---------|-----------|
| `nextalarm_label` | `za 08:30` |

---

## Services

Alle services hebben domein: `wakeclock`

### `wakeclock.set_schedule`

```yaml
service: wakeclock.set_schedule
data:
  schedule:
    ma: "07:00"
    di: "07:00"
    wo: "08:30"
    do: ""
    vr: "07:15"
    za: "09:00"
    zo: "09:30"
```

---

### `wakeclock.set_day_time`

```yaml
service: wakeclock.set_day_time
data:
  day: za
  time: "08:30"
```

---

### `wakeclock.set_snooze`

```yaml
service: wakeclock.set_snooze
data:
  minutes: 9
```

---

### `wakeclock.snooze`

```yaml
service: wakeclock.snooze
```

---

### `wakeclock.dismiss`

```yaml
service: wakeclock.dismiss
```

---

### `wakeclock.recalc_next`

```yaml
service: wakeclock.recalc_next
```

---

## Automation voorbeeld

```yaml
automation:
  - alias: WakeClock afgaan
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.wakeclock_nextalarm') not in
             ['unknown','unavailable',''] and
             now().replace(second=0, microsecond=0)
             ==
             as_datetime(states('sensor.wakeclock_nextalarm'))
             .replace(second=0, microsecond=0) }}
    condition:
      - condition: state
        entity_id: switch.wakeclock
        state: "on"
    action:
      - service: notify.notify
        data:
          message: "Wekker!"
```

---

## Licentie

MIT
