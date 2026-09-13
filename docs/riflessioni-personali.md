# Riflessioni sulle scelte progettuali e sulle evoluzioni future

## Scelte progettuali

Ritengo utile mantenere una copia locale degli eventi perché permette di separare la consultazione dalla disponibilità momentanea della sorgente NASA. Questo richiede però di gestire l'aggiornamento e di comunicare la freschezza dei dati: un servizio disponibile può comunque mostrare informazioni non aggiornate.

Considero appropriato l’uso di un database relazionale per rappresentare eventi, categorie, fonti e rilevazioni, così da ridurre il numero di richieste effettuate direttamente alla sorgente NASA. L’utilizzo di tabelle associative permette inoltre di evitare la duplicazione di categorie e fonti per ogni evento. La scelta di memorizzare le coordinate in formato JSON rende più semplice la gestione di geometrie differenti, anche se può rendere più complessa l’implementazione di ricerche geografiche avanzate.


La separazione tra endpoint e query rende il progetto leggibile senza introdurre molti livelli. Per le dimensioni attuali considero questa semplicità un vantaggio; con più funzionalità valuterei una separazione ulteriore tra acquisizione, accesso ai dati e regole applicative.

La transazione unica protegge dalla presenza di aggiornamenti parziali. La sostituzione delle relazioni e delle geometrie semplifica la sincronizzazione, ma rinuncia alla conservazione delle versioni precedenti e può comportare molte scritture. Considero questo un compromesso accettabile per un prototipo, da rivalutare se il volume dei dati aumenta.

## Evoluzioni future

La prima priorità sarebbe migliorare la completezza dell'acquisizione e mostrare chiaramente l'ultimo aggiornamento riuscito nella dashboard. Il limite di 500 eventi richiede una strategia di importazione più ampia; aggiungerei anche tentativi con attesa progressiva per gli errori temporanei e controlli sulla qualità dei dati ricevuti.

Successivamente sposterei filtri e aggregazioni verso l'API, riducendo il trasferimento di dati e il numero di query. Introdurrei una paginazione stabile e valuterei indici geografici soltanto in presenza di ricerche spaziali concrete. Per una distribuzione con più processi separerei la sincronizzazione in un servizio dedicato.

Per rendere più affidabile la manutenzione aggiungerei migrazioni versionate e test automatici su rollback, aggiornamenti ripetuti e geometrie non valide. Uno storico delle revisioni consentirebbe di studiare l'evoluzione degli eventi nel tempo. Funzioni come preferiti o notifiche richiederebbero invece account, autenticazione e autorizzazione.

## Difficoltà incontrate

La difficoltà maggiore è stata creare un sistema di caching, perché non avevo mai studiato questo argomento in precedenza. Ho dovuto quindi comprendere come conservare localmente i dati provenienti dall'API NASA e come aggiornarli senza mostrare informazioni incoerenti o troppo vecchie.

Un altro punto di rallentamento rilevante è stata l'implementazione della mappa. La visualizzazione dei punti ha richiesto attenzione nella gestione delle coordinate, ma la parte più complessa è stata rappresentare correttamente le aree associate agli eventi e adattarle alla struttura dei dati ricevuti.
