# Riflessioni sulle scelte progettuali e sulle evoluzioni future

> Bozza da rivedere e personalizzare a cura dell'autore prima della consegna. Le considerazioni si basano sul codice presente; non descrivono esperienze personali o prove svolte dall'autore.

## Scelte progettuali

Ritengo utile mantenere una copia locale degli eventi perché permette di separare la consultazione dalla disponibilità momentanea della sorgente NASA. Questo richiede però di gestire l'aggiornamento e di comunicare la freschezza dei dati: un servizio disponibile può comunque mostrare informazioni non aggiornate.

Considero coerente l'uso di un database relazionale per rappresentare eventi, categorie, fonti e rilevazioni. Le tabelle associative evitano di duplicare categorie e fonti per ogni evento. La scelta di conservare le coordinate in JSON facilita la gestione di forme diverse, ma rende meno immediata l'introduzione di ricerche geografiche avanzate.

La separazione tra endpoint e query rende il progetto leggibile senza introdurre molti livelli. Per le dimensioni attuali considero questa semplicità un vantaggio; con più funzionalità valuterei una separazione ulteriore tra acquisizione, accesso ai dati e regole applicative.

La transazione unica protegge dalla presenza di aggiornamenti parziali. La sostituzione delle relazioni e delle geometrie semplifica la sincronizzazione, ma rinuncia alla conservazione delle versioni precedenti e può comportare molte scritture. Considero questo un compromesso accettabile per un prototipo, da rivalutare se il volume dei dati aumenta.

Docker Compose rende riproducibile la configurazione dei servizi. La dashboard PHP con JavaScript permette di consultare i dati in modo diretto, ma caricare tutto nel browser limita la scalabilità. Inoltre, l'uso della prima categoria semplifica i grafici a costo di perdere parte dell'informazione disponibile.

## Evoluzioni future

La prima priorità sarebbe migliorare la completezza dell'acquisizione e mostrare chiaramente l'ultimo aggiornamento riuscito nella dashboard. Il limite di 500 eventi richiede una strategia di importazione più ampia; aggiungerei anche tentativi con attesa progressiva per gli errori temporanei e controlli sulla qualità dei dati ricevuti.

Successivamente sposterei filtri e aggregazioni verso l'API, riducendo il trasferimento di dati e il numero di query. Introdurrei una paginazione stabile e valuterei indici geografici soltanto in presenza di ricerche spaziali concrete. Per una distribuzione con più processi separerei la sincronizzazione in un servizio dedicato.

Per rendere più affidabile la manutenzione aggiungerei migrazioni versionate e test automatici su rollback, aggiornamenti ripetuti e geometrie non valide. Uno storico delle revisioni consentirebbe di studiare l'evoluzione degli eventi nel tempo. Funzioni come preferiti o notifiche richiederebbero invece account, autenticazione e autorizzazione.

## Aspetti da personalizzare

Prima della consegna aggiungere un esempio concreto di difficoltà incontrata, spiegare quale alternativa è stata realmente valutata e indicare quale evoluzione si vorrebbe implementare per prima e perché. Questi elementi devono riflettere l'esperienza effettiva dell'autore.
