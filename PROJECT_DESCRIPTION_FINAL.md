# Përshkrimi Final i Temës së Projektit

## Tema e Projektit

Tema e propozuar synon projektimin dhe implementimin e një platforme të avancuar për monitorimin dhe analizën inteligjente të konsumit të energjisë elektrike në kohë reale dhe historike, e ndërtuar mbi parimet e sistemeve moderne të procesimit të të dhënave dizajnuese dhe arkitekturave të shpërndara.

## Arkitektura dhe Teknologji

### Event-Driven Architecture
Platforma do të përdorë një arkitekturë të orientuar në ngjarje (event-driven architecture), ku të dhënat e konsumit do të gjenerohen nga pajisje inteligjente të matjes (smart meters të simuluara) dhe do të transmetohen përmes mekanizmave pub/sub duke përdorur **Apache Kafka**.

### Përpunimi i të Dhënave
Përpunimi i të dhënave do të realizohet si në kohë reale ashtu edhe në batch, përmes **Apache Spark Structured Streaming**, duke mundësuar:
- Analizë të vazhdueshme (real-time)
- Analizë historike të konsumit të energjisë

### Integrimi i Burimeve të të Dhënave
Platforma do të integrojë burime shtesë të të dhënave kontekstuale:
- **Të dhënat meteorologjike** - për analizimin e ndikimit të faktorëve të jashtëm në ndryshimet e konsumit
- **Korelacione** ndërmjet kushteve të motit dhe niveleve të konsumit të energjisë

## Mekanizmat Analitikë

Platforma do të implementojë mekanizma analitikë për:

1. **Identifikimin e orareve me konsum maksimal (peak hours)**
2. **Analizën e trendeve:**
   - Trende ditore
   - Trende mujore
   - Trende sezonale
3. **Krahasimet e konsumit:**
   - Krahasim ndërmjet viteve të ndryshme
   - Analizë e rritjes ose uljes së konsumit në periudha afatgjata
   - Krahasim i konsumit sipas zonave dhe intervaleve kohore
4. **Vlerësimi i ndikimit:**
   - Vlerësim i ndikimit të temperaturës dhe kushteve klimatike në konsum

## Arkitektura e Sistemit

### Mikrosherbime
Sistemi do të ndërtohet mbi parimet e **arkitekturës së bazuar në mikrosherbime**.

### Ruajtja e të Dhënave
- **Baza të dhënash relacione** - për të dhëna strukturuara
- **Data Lake** - për të dhëna historike
- **Ruajtje hibride** - kombinim i të dyja

### Karakteristikat e Platformës
- **Monitorim i vazhdueshëm** i performancës
- **Mekanizma bazë sigurie**
- **Dashboard-e interaktive** për vizualizimin:
  - Konsumit në kohë reale
  - Konsumit historik
- **Mbështetje konkrete për vendimmarrje**

## Përputhja me Kërkesat

Ky projekt është në përputhje të plotë me kërkesat teknike të lëndës dhe demonstron përdorimin e teknologjive moderne të procesimit të të dhënave për:
- Monitorim
- Analizë të avancuar
- Mbështetje të vendimmarrjes

në sistemet inteligjente të energjisë (smart grid).

## Teknologjitë Kryesore

- **Apache Kafka** - Event streaming dhe pub/sub messaging
- **Apache Spark Structured Streaming** - Real-time dhe batch processing
- **Smart Meters (simuluar)** - Gjenerimi i të dhënave
- **Mikrosherbime** - Arkitekturë e shpërndarë
- **Data Lake** - Ruajtje e të dhënave historike
- **Dashboard Interaktive** - Vizualizim në kohë reale dhe historik

## Objektivat e Projektit

1. ✅ Monitorim në kohë reale të konsumit të energjisë
2. ✅ Analizë historike e konsumit
3. ✅ Identifikim i peak hours
4. ✅ Analizë e trendeve (ditore, mujore, sezonale)
5. ✅ Krahasime të konsumit (vjetore, zonale, kohore)
6. ✅ Analizë e ndikimit të faktorëve të jashtëm (mot, temperaturë)
7. ✅ Dashboard interaktive për vizualizim
8. ✅ Mbështetje për vendimmarrje

