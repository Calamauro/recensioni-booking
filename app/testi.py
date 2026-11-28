"""Testi dell'interfaccia in italiano, inglese e russo.

Uso:  t("chiave", lingua, valore=...)   ->  testo con i segnaposto {valore} sostituiti.
I valori interni dell'app (stagioni, metodi, sezioni) restano in italiano: qui si traduce solo ciò che si vede.
"""

from __future__ import annotations

LINGUE = {"it": "🇮🇹 Italiano", "en": "🇬🇧 English", "ru": "🇷🇺 Русский"}

MESI = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль",
           "август", "сентябрь", "октябрь", "ноябрь", "декабрь"],
}
MESI_BREVI = {
    "it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ru": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
}

T: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------ generale
    "lingua": {"it": "Lingua", "en": "Language", "ru": "Язык"},
    "esci": {"it": "Esci", "en": "Log out", "ru": "Выйти"},
    "demo_badge": {"it": "DEMO · dati fittizi", "en": "DEMO · sample data", "ru": "ДЕМО · тестовые данные"},
    "nessuna_struttura": {"it": "nessuna struttura", "en": "no properties", "ru": "нет объектов"},
    "altra_struttura": {"it": "Altra struttura", "en": "Other property", "ru": "Другой объект"},

    # ------------------------------------------------------------------ demo e login
    "demo_sotto": {"it": "Recensioni e bonus a scaglioni, a colpo d'occhio",
                   "en": "Guest reviews and tiered bonus at a glance",
                   "ru": "Отзывы гостей и ступенчатый бонус — наглядно"},
    "demo_testo": {
        "it": "Monitoraggio delle recensioni e del **bonus a scaglioni stagionali** degli operatori di "
              "strutture ricettive: contagiri, andamento mensile, esclusioni e simulatore di voti.",
        "en": "Monitoring of guest reviews and the **seasonal tiered bonus** for short-term rental "
              "property managers: bonus gauge, monthly trend, review exclusions and score simulator.",
        "ru": "Мониторинг отзывов гостей и **сезонного ступенчатого бонуса** менеджеров объектов "
              "размещения: шкала бонуса, помесячная динамика, исключение отзывов и симулятор оценок."},
    "demo_info": {
        "it": "**Versione dimostrativa** con dati completamente fittizi: strutture, ospiti e recensioni sono "
              "inventati. Nessuna credenziale richiesta.",
        "en": "**Demo version** with entirely fictitious data: properties, guests and reviews are made up. "
              "No login required.",
        "ru": "**Демо-версия** с полностью вымышленными данными: объекты, гости и отзывы не настоящие. "
              "Вход без учётной записи."},
    "entra_operatrice": {"it": "👩 Entra come operatrice", "en": "👩 Sign in as property manager",
                         "ru": "👩 Войти как менеджер"},
    "entra_admin": {"it": "🛠️ Entra come amministratore", "en": "🛠️ Sign in as administrator",
                    "ru": "🛠️ Войти как администратор"},
    "demo_ruoli": {
        "it": "L'operatrice vede solo le sue strutture; l'amministratore può aprire la dashboard di ogni operatore.",
        "en": "The property manager sees only their own properties; the administrator can open any manager's dashboard.",
        "ru": "Менеджер видит только свои объекты; администратор может открыть панель любого менеджера."},
    "login_sotto": {"it": "Accedi con le credenziali che ti sono state fornite.",
                    "en": "Sign in with the credentials you have been given.",
                    "ru": "Войдите, используя выданные вам учётные данные."},
    "password": {"it": "Password", "en": "Password", "ru": "Пароль"},
    "accedi": {"it": "Accedi", "en": "Sign in", "ru": "Войти"},
    "login_errato": {"it": "Email o password non corretti.", "en": "Incorrect email or password.",
                     "ru": "Неверный email или пароль."},
    "servizio_ko": {"it": "Servizio non raggiungibile, riprova tra poco.",
                    "en": "Service unavailable, please try again shortly.",
                    "ru": "Сервис недоступен, повторите попытку позже."},
    "sessione_scaduta": {"it": "Sessione scaduta: accedi di nuovo.", "en": "Session expired: please sign in again.",
                         "ru": "Сеанс истёк: войдите снова."},

    # ------------------------------------------------------------------ dashboard
    "dashboard_di": {"it": "👤 Dashboard di", "en": "👤 Dashboard of", "ru": "👤 Панель пользователя"},
    "no_strutture": {
        "it": "Nessuna struttura assegnata a questo utente. Aggiungila nella tabella 'assegnazioni' su Supabase.",
        "en": "No properties assigned to this user. Add them to the 'assegnazioni' table in Supabase.",
        "ru": "За этим пользователем не закреплены объекты. Добавьте их в таблицу 'assegnazioni' в Supabase."},
    "no_scaglioni": {
        "it": "Nessuno scaglione bonus configurato per questo utente (tabella 'scaglioni').",
        "en": "No bonus tiers configured for this user ('scaglioni' table).",
        "ru": "Для этого пользователя не настроены пороги бонуса (таблица 'scaglioni')."},

    # ------------------------------------------------------------------ filtri
    "filtri": {"it": "⚙️ Filtri", "en": "⚙️ Filters", "ru": "⚙️ Фильтры"},
    "periodo": {"it": "Periodo", "en": "Period", "ru": "Период"},
    "p_Dall'inizio": {"it": "Dall'inizio", "en": "Since start", "ru": "С начала"},
    "p_Mese corrente": {"it": "Mese corrente", "en": "Current month", "ru": "Текущий месяц"},
    "p_Mese a scelta": {"it": "Mese a scelta", "en": "Select month", "ru": "Выбрать месяц"},
    "p_Intervallo personalizzato": {"it": "Intervallo personalizzato", "en": "Custom range",
                                    "ru": "Произвольный период"},
    "mese": {"it": "Mese", "en": "Month", "ru": "Месяц"},
    "dal": {"it": "Dal", "en": "From", "ru": "С"},
    "al": {"it": "Al", "en": "To", "ru": "По"},
    "calcolato_su": {"it": "Periodo calcolato su", "en": "Period based on", "ru": "Период по"},
    "c_Data recensione": {"it": "Data recensione", "en": "Review date", "ru": "Дата отзыва"},
    "c_Mese soggiorno": {"it": "Mese soggiorno", "en": "Stay month", "ru": "Месяц проживания"},
    "calcolato_help": {
        "it": "Data recensione = giorno in cui l'ospite ha scritto. Mese soggiorno = mese in cui ha dormito "
              "({piattaforme} mostra solo mese e anno).",
        "en": "Review date = day the guest wrote the review. Stay month = month of the stay "
              "({piattaforme} only shows month and year).",
        "ru": "Дата отзыва — день, когда гость написал отзыв. Месяц проживания — месяц пребывания "
              "({piattaforme} показывает только месяц и год)."},
    "piattaforme_demo": {"it": "la piattaforma", "en": "the platform", "ru": "платформа"},
    "media_bonus_label": {"it": "Media per il bonus", "en": "Average for bonus", "ru": "Средняя для бонуса"},
    "m_Media delle strutture": {"it": "Media delle strutture", "en": "Average of properties",
                                "ru": "Среднее по объектам"},
    "m_Tutte le recensioni insieme": {"it": "Tutte le recensioni insieme", "en": "All reviews combined",
                                      "ru": "Все отзывы вместе"},
    "metodo_help": {
        "it": "Media delle strutture = media delle medie di ogni struttura. Tutte le recensioni insieme = media "
              "di tutti i voti.",
        "en": "Average of properties = mean of each property's average. All reviews combined = mean of all scores.",
        "ru": "Среднее по объектам — среднее из средних оценок каждого объекта. Все отзывы вместе — среднее "
              "всех оценок."},
    "scaglioni": {"it": "Scaglioni", "en": "Bonus tiers", "ru": "Шкала бонуса"},
    "s_Automatica": {"it": "Automatica", "en": "Automatic", "ru": "Автоматически"},
    "s_Inverno": {"it": "Inverno", "en": "Winter", "ru": "Зима"},
    "s_Estate": {"it": "Estate", "en": "Summer", "ru": "Лето"},
    "stag_help": {
        "it": "Automatica = stagione della fine del periodo. Inverno = 1 nov – 31 mar, Estate = 1 apr – 31 ott.",
        "en": "Automatic = season of the period end date. Winter = 1 Nov – 31 Mar, Summer = 1 Apr – 31 Oct.",
        "ru": "Автоматически — сезон по дате окончания периода. Зима — 1 ноя – 31 мар, лето — 1 апр – 31 окт."},
    "recensioni_n": {"it": "{n} recensioni", "en": "{n} reviews", "ru": "отзывов: {n}"},
    "escluse_n": {"it": "{n} escluse dal calcolo", "en": "{n} excluded from calculation",
                  "ru": "исключено из расчёта: {n}"},

    # ------------------------------------------------------------------ sezioni
    "sez_pan": {"it": "📊 Panoramica", "en": "📊 Overview", "ru": "📊 Обзор"},
    "sez_mesi": {"it": "📅 Mesi", "en": "📅 Months", "ru": "📅 Месяцы"},
    "sez_sim": {"it": "🧪 Simulatore", "en": "🧪 Simulator", "ru": "🧪 Симулятор"},
    "sez_rec": {"it": "📝 Recensioni", "en": "📝 Reviews", "ru": "📝 Отзывы"},
    "sez_stip": {"it": "💶 Stipendio", "en": "💶 Earnings", "ru": "💶 Доход"},

    # ------------------------------------------------------------------ card e contagiri
    "prossimo": {"it": "Prossimo scaglione", "en": "Next tier", "ru": "Следующий порог"},
    "mancano": {"it": "mancano {x}", "en": "{x} to go", "ru": "осталось {x}"},
    "massimo": {"it": "Massimo raggiunto ✓", "en": "Top tier reached ✓", "ru": "Максимум достигнут ✓"},
    "bonus_stag": {"it": "Bonus {stag}", "en": "{stag} bonus", "ru": "Бонус ({stag})"},
    "sim_avviso": {
        "it": "🧪 <b>Dati con simulazione</b>: {n} voti ipotetici inclusi. Senza simulazione: media {m} · bonus {b}.",
        "en": "🧪 <b>Simulated data</b>: {n} hypothetical scores included. Without simulation: "
              "average {m} · bonus {b}.",
        "ru": "🧪 <b>Данные с симуляцией</b>: учтено гипотетических оценок — {n}. Без симуляции: "
              "средняя {m} · бонус {b}."},
    "media_con_sim": {"it": "Media per il bonus con simulazione", "en": "Average for bonus (simulated)",
                      "ru": "Средняя для бонуса (симуляция)"},
    "bonus_con_sim": {"it": "Bonus {stag} con simulazione", "en": "{stag} bonus (simulated)",
                      "ru": "Бонус ({stag}), симуляция"},
    "gauge_nota": {
        "it": "La barra oro è la media {quale}, la linea blu la soglia del prossimo scaglione.",
        "en": "The gold bar is the {quale} average; the blue line is the next tier threshold.",
        "ru": "Золотая полоса — {quale} средняя оценка, синяя линия — порог следующей ступени."},
    "quale_attuale": {"it": "attuale", "en": "current", "ru": "текущая"},
    "quale_simulata": {"it": "simulata", "en": "simulated", "ru": "смоделированная"},
    "gauge_nota_sim": {
        "it": " I voti simulati si modificano o azzerano nella sezione **🧪 Simulatore**.",
        "en": " Simulated scores can be edited or cleared in the **🧪 Simulator** section.",
        "ru": " Смоделированные оценки можно изменить или сбросить в разделе **🧪 Симулятор**."},

    # ------------------------------------------------------------------ simulatore
    "sim_titolo": {"it": "Simulatore di voti", "en": "Score simulator", "ru": "Симулятор оценок"},
    "sim_testo": {
        "it": "Aggiungi fino a 10 voti ipotetici, poi tocca **Salva e simula**. Usa **{altra}** per i voti presi "
              "in strutture non tue (es. coprendo una collega). {salva} e si vedono anche in **📊 Panoramica**; "
              "non toccano i dati reali.",
        "en": "Add up to 10 hypothetical scores, then tap **Save & simulate**. Use **{altra}** for scores received "
              "at properties you don't manage (e.g. covering for a colleague). {salva} and are also reflected in "
              "**📊 Overview**; real data is never affected.",
        "ru": "Добавьте до 10 гипотетических оценок и нажмите **Сохранить и рассчитать**. Используйте "
              "**{altra}** для оценок, полученных на чужих объектах (например, при замене коллеги). {salva} и "
              "отображаются в разделе **📊 Обзор**; реальные данные не меняются."},
    "sim_salvati": {"it": "Restano salvati anche quando chiudi l'app", "en": "They are kept after you close the app",
                    "ru": "Они сохраняются после закрытия приложения"},
    "sim_non_salvati": {"it": "Non vengono salvati", "en": "They are not saved", "ru": "Они не сохраняются"},
    "struttura": {"it": "Struttura", "en": "Property", "ru": "Объект"},
    "voto": {"it": "Voto", "en": "Score", "ru": "Оценка"},
    "salva_simula": {"it": "💾 Salva e simula", "en": "💾 Save & simulate", "ru": "💾 Сохранить и рассчитать"},
    "nessuna_modifica": {"it": "Nessuna modifica da salvare", "en": "No changes to save",
                         "ru": "Нет изменений для сохранения"},
    "azzera_sim": {"it": "🗑️ Azzera simulazione", "en": "🗑️ Clear simulation", "ru": "🗑️ Сбросить симуляцию"},
    "invariato": {"it": "invariato", "en": "unchanged", "ru": "без изменений"},
    "punti_perc": {"it": "{x} punti %", "en": "{x} percentage points", "ru": "{x} п.п."},
    "media_simulata": {"it": "Media simulata", "en": "Simulated average", "ru": "Смоделированная средняя"},
    "bonus_simulato": {"it": "Bonus simulato", "en": "Simulated bonus", "ru": "Смоделированный бонус"},
    "rispetto_oggi": {"it": "{d} rispetto a oggi · {n} recensioni (+{k})",
                      "en": "{d} vs today · {n} reviews (+{k})",
                      "ru": "{d} к текущей · отзывов: {n} (+{k})"},
    "max_sim": {"it": "Massimo 10 voti simulati.", "en": "Maximum 10 simulated scores.",
                "ru": "Не более 10 смоделированных оценок."},
    "media_attuale": {"it": "Media attuale", "en": "Current average", "ru": "Текущая средняя"},
    "bonus_attuale": {"it": "Bonus attuale", "en": "Current bonus", "ru": "Текущий бонус"},
    "sim_vuoto": {"it": "Aggiungi un voto qui sopra e tocca Salva e simula",
                  "en": "Add a score above and tap Save & simulate",
                  "ru": "Добавьте оценку выше и нажмите «Сохранить и рассчитать»"},
    "sim_non_salvata": {"it": "Simulazione non salvata: resterà solo fino alla chiusura dell'app.",
                        "en": "Simulation not saved: it will only last until you close the app.",
                        "ru": "Симуляция не сохранена: она будет доступна только до закрытия приложения."},

    # ------------------------------------------------------------------ panoramica: tabelle
    "tab_scaglioni": {"it": "📋 Tabella scaglioni ({stag})", "en": "📋 Bonus tiers ({stag})",
                      "ru": "📋 Шкала бонуса ({stag})"},
    "media_da": {"it": "Media da", "en": "Average from", "ru": "Средняя от"},
    "bonus": {"it": "Bonus", "en": "Bonus", "ru": "Бонус"},
    "attuale_freccia": {"it": "◀ attuale", "en": "◀ current", "ru": "◀ текущий"},
    "per_struttura": {"it": "Per struttura", "en": "By property", "ru": "По объектам"},
    "recensioni": {"it": "Recensioni", "en": "Reviews", "ru": "Отзывы"},
    "media": {"it": "Media", "en": "Average", "ru": "Средняя"},
    "voti_9": {"it": "% voti ≥ 9", "en": "% scores ≥ 9", "ru": "% оценок ≥ 9"},
    "voti_7": {"it": "Voti < 7", "en": "Scores < 7", "ru": "Оценок < 7"},

    # ------------------------------------------------------------------ mesi
    "andamento": {"it": "Andamento mensile ({da} – {a})", "en": "Monthly trend ({da} – {a})",
                  "ru": "Помесячная динамика ({da} – {a})"},
    "media_per_bonus_leg": {"it": "Media per il bonus", "en": "Average for bonus", "ru": "Средняя для бонуса"},
    "mesi_nota": {
        "it": "In **oro** la media che conta per il bonus. Le recensioni di ogni mese sono nella sezione "
              "**📝 Recensioni**.",
        "en": "The **gold** bar is the average that counts towards the bonus. Each month's reviews are in the "
              "**📝 Reviews** section.",
        "ru": "**Золотым** показана средняя, учитываемая для бонуса. Отзывы за каждый месяц — в разделе "
              "**📝 Отзывы**."},
    "stagione": {"it": "Stagione", "en": "Season", "ru": "Сезон"},
    "nessuna_rec_mesi": {"it": "Ancora nessuna recensione nei mesi conteggiati.",
                         "en": "No reviews yet in the months counted.",
                         "ru": "В учитываемых месяцах отзывов пока нет."},

    # ------------------------------------------------------------------ recensioni
    "mese_per_mese": {"it": "Mese per mese", "en": "Month by month", "ru": "По месяцам"},
    "mese_per_mese_nota": {
        "it": "Tocca un mese per vedere le sue recensioni. Spunta **Escludi** per togliere una recensione dal "
              "calcolo (es. giorni di ferie o riposo), poi **Applica e ricalcola**.",
        "en": "Tap a month to see its reviews. Tick **Exclude** to remove a review from the calculation "
              "(e.g. holidays or days off), then tap **Apply & recalculate**.",
        "ru": "Нажмите на месяц, чтобы увидеть его отзывы. Отметьте **Исключить**, чтобы убрать отзыв из "
              "расчёта (например, отпуск или выходные), затем нажмите **Применить и пересчитать**."},
    "esclusa_n": {"it": "{n} esclusa", "en": "{n} excluded", "ru": "исключено: {n}"},
    "escluse_n_breve": {"it": "{n} escluse", "en": "{n} excluded", "ru": "исключено: {n}"},
    "mese_riga": {"it": "**{mese}** · {parti} · media **{m}** · bonus **{b}** ({stag}){escl}",
                  "en": "**{mese}** · {parti} · average **{m}** · bonus **{b}** ({stag}){escl}",
                  "ru": "**{mese}** · {parti} · средняя **{m}** · бонус **{b}** ({stag}){escl}"},
    "tutte_escluse": {"it": "{mese} · tutte escluse ({stag})", "en": "{mese} · all excluded ({stag})",
                      "ru": "{mese} · все исключены ({stag})"},
    "nessuna_rec_mese": {"it": "{mese} · nessuna recensione ({stag})", "en": "{mese} · no reviews ({stag})",
                         "ru": "{mese} · нет отзывов ({stag})"},
    "nessuna_rec_ancora": {"it": "Ancora nessuna recensione in questo mese.", "en": "No reviews this month yet.",
                           "ru": "В этом месяце отзывов пока нет."},
    "escludi": {"it": "Escludi", "en": "Exclude", "ru": "Исключить"},
    "escludi_help": {"it": "Non conta in medie e bonus", "en": "Not counted in averages and bonus",
                     "ru": "Не учитывается в средних и бонусе"},
    "data": {"it": "Data", "en": "Date", "ru": "Дата"},
    "soggiorno": {"it": "Soggiorno", "en": "Stay", "ru": "Проживание"},
    "ospite": {"it": "Ospite", "en": "Guest", "ru": "Гость"},
    "paese": {"it": "Paese", "en": "Country", "ru": "Страна"},
    "titolo": {"it": "Titolo", "en": "Title", "ru": "Заголовок"},
    "tipo": {"it": "Tipo", "en": "Traveller type", "ru": "Тип гостя"},
    "esclusa": {"it": "Esclusa", "en": "Excluded", "ru": "Исключён"},
    "applica": {"it": "✅ Applica e ricalcola", "en": "✅ Apply & recalculate", "ru": "✅ Применить и пересчитать"},
    "escl_salvate": {"it": "Salvato: {a} escluse, {b} riammesse. Medie e bonus ricalcolati.",
                     "en": "Saved: {a} excluded, {b} restored. Averages and bonus recalculated.",
                     "ru": "Сохранено: исключено {a}, возвращено {b}. Средние и бонус пересчитаны."},
    "escl_errore": {"it": "Impossibile salvare le esclusioni. Dettaglio tecnico: {d}",
                    "en": "Unable to save exclusions. Technical details: {d}",
                    "ru": "Не удалось сохранить исключения. Технические детали: {d}"},
    "tutte_periodo": {"it": "Tutte le recensioni del periodo ({n})", "en": "All reviews in the period ({n})",
                      "ru": "Все отзывы за период ({n})"},
    "periodo_filtri": {"it": "Il periodo si cambia dai **⚙️ Filtri** in alto.",
                       "en": "Change the period from **⚙️ Filters** at the top.",
                       "ru": "Период меняется в разделе **⚙️ Фильтры** вверху."},
    "nessuna_rec_periodo": {"it": "Nessuna recensione nel periodo scelto.", "en": "No reviews in the selected period.",
                            "ru": "За выбранный период отзывов нет."},
    "scarica_csv": {"it": "⬇️ Scarica CSV", "en": "⬇️ Download CSV", "ru": "⬇️ Скачать CSV"},

    # ------------------------------------------------------------------ stipendio
    "stip_titolo": {"it": "Calcolatore stipendio", "en": "Earnings calculator", "ru": "Калькулятор дохода"},
    "stip_testo": {
        "it": "Stima del compenso lordo del mese e di quanto resta dopo imposta e contributi (regime forfettario). "
              "Inserisci i dati e tocca **Calcola**{salva}",
        "en": "Estimate of the month's gross earnings and of the net amount after tax and social security "
              "contributions (Italian flat-rate scheme, *regime forfettario*). Enter your data and tap "
              "**Calculate**{salva}",
        "ru": "Оценка валового дохода за месяц и суммы после налога и взносов (итальянский упрощённый режим "
              "налогообложения, *regime forfettario*). Введите данные и нажмите **Рассчитать**{salva}"},
    "stip_salvati": {"it": ": restano salvati anche quando chiudi l'app.",
                     "en": ": your data is kept after you close the app.",
                     "ru": ": данные сохраняются после закрытия приложения."},
    "fissi_titolo": {
        "it": "**Compensi fissi** · una riga per ogni fisso (es. settimana e weekend). Spunta **Con bonus** solo "
              "sui fissi a cui si applica il bonus.",
        "en": "**Fixed pay** · one row per fixed fee (e.g. weekdays and weekend). Tick **Bonus applies** only for "
              "the fixed fees the bonus is applied to.",
        "ru": "**Фиксированная оплата** · одна строка на каждую ставку (например, будни и выходные). Отметьте "
              "**С бонусом** только для ставок, на которые начисляется бонус."},
    "voce": {"it": "Voce", "en": "Item", "ru": "Статья"},
    "fisso": {"it": "Fisso", "en": "Fixed fee", "ru": "Фикс. ставка"},
    "importo": {"it": "Importo €", "en": "Amount €", "ru": "Сумма €"},
    "con_bonus": {"it": "Con bonus", "en": "Bonus applies", "ru": "С бонусом"},
    "checkin_mese": {"it": "Check-in del mese", "en": "Check-ins this month", "ru": "Заселений за месяц"},
    "euro_checkin": {"it": "€ per check-in", "en": "€ per check-in", "ru": "€ за заселение"},
    "usa_bonus_app": {"it": "Usa il bonus calcolato dall'app ({b}{sim})",
                      "en": "Use the bonus calculated by the app ({b}{sim})",
                      "ru": "Использовать бонус, рассчитанный приложением ({b}{sim})"},
    "con_simulazione": {"it": ", con simulazione", "en": ", simulated", "ru": ", с симуляцией"},
    "usa_bonus_help": {
        "it": "Il bonus del periodo scelto nei filtri. Togli la spunta per inserire un bonus a mano.",
        "en": "The bonus for the period selected in the filters. Untick to enter a bonus manually.",
        "ru": "Бонус за период, выбранный в фильтрах. Снимите отметку, чтобы ввести бонус вручную."},
    "bonus_mano": {"it": "Bonus a mano (%) · usato solo senza la spunta qui sopra",
                   "en": "Manual bonus (%) · used only when the box above is unticked",
                   "ru": "Бонус вручную (%) · применяется, только если отметка выше снята"},
    "param_fiscali": {"it": "⚙️ Parametri fiscali (regime forfettario)",
                      "en": "⚙️ Tax parameters (flat-rate scheme)",
                      "ru": "⚙️ Налоговые параметры (упрощённый режим)"},
    "coeff": {"it": "Coeff. redditività %", "en": "Profitability coefficient %", "ru": "Коэф. доходности %"},
    "coeff_help": {
        "it": "Percentuale del lordo che diventa reddito imponibile; dipende dal codice ATECO.",
        "en": "Share of gross revenue treated as taxable income; it depends on the ATECO activity code.",
        "ru": "Доля валового дохода, признаваемая налогооблагаемой; зависит от кода деятельности ATECO."},
    "imposta": {"it": "Imposta %", "en": "Substitute tax %", "ru": "Замещающий налог %"},
    "imposta_help": {
        "it": "5% nei primi 5 anni di attività (se ne hai i requisiti), poi 15%.",
        "en": "5% for the first 5 years of business (if eligible), then 15%.",
        "ru": "5% в первые 5 лет деятельности (при соблюдении условий), затем 15%."},
    "inps": {"it": "INPS %", "en": "INPS contributions %", "ru": "Взносы INPS %"},
    "inps_help": {"it": "Aliquota contributiva applicata al reddito imponibile.",
                  "en": "Social security contribution rate applied to taxable income.",
                  "ru": "Ставка социальных взносов, применяемая к налогооблагаемому доходу."},
    "calcola": {"it": "🧮 Calcola", "en": "🧮 Calculate", "ru": "🧮 Рассчитать"},
    "lordo_mese": {"it": "Lordo del mese", "en": "Monthly gross earnings", "ru": "Валовой доход за месяц"},
    "lordo_nota": {
        "it": "Bonus calcolato su {f} di fissi con bonus + {c} di check-in (prima colonna) oppure solo sui "
              "check-in (seconda colonna).",
        "en": "Bonus calculated on {f} of bonus-eligible fixed pay + {c} of check-ins (first column) or on "
              "check-ins only (second column).",
        "ru": "Бонус рассчитан на {f} фиксированной оплаты с бонусом + {c} за заселения (первый столбец) или "
              "только на заселения (второй столбец)."},
    "compensi_fissi": {"it": "Compensi fissi", "en": "Fixed pay", "ru": "Фиксированная оплата"},
    "checkin_riga": {"it": "Check-in ({n} × {t})", "en": "Check-ins ({n} × {t})", "ru": "Заселения ({n} × {t})"},
    "prima_bonus": {"it": "Totale prima del bonus", "en": "Total before bonus", "ru": "Итого до бонуса"},
    "bonus_riga": {"it": "Bonus {p}%", "en": "Bonus {p}%", "ru": "Бонус {p}%"},
    "totale_lordo": {"it": "Totale lordo", "en": "Total gross", "ru": "Итого брутто"},
    "col_fisso_ci": {"it": "Bonus fisso + check-in", "en": "Bonus on fixed pay + check-ins",
                     "ru": "Бонус на фикс. + заселения"},
    "col_solo_ci": {"it": "Bonus solo check-in", "en": "Bonus on check-ins only", "ru": "Бонус только на заселения"},
    "dopo_tasse": {"it": "Dopo imposta e contributi", "en": "After tax and contributions",
                   "ru": "После налога и взносов"},
    "imponibile_riga": {"it": "Reddito imponibile ({p}% del lordo)", "en": "Taxable income ({p}% of gross)",
                        "ru": "Налогооблагаемый доход ({p}% от брутто)"},
    "inps_riga": {"it": "INPS {p}%", "en": "INPS contributions {p}%", "ru": "Взносы INPS {p}%"},
    "imposta_riga": {"it": "Imposta sostitutiva {p}%", "en": "Substitute tax {p}%", "ru": "Замещающий налог {p}%"},
    "netto_stimato": {"it": "Netto stimato", "en": "Estimated net", "ru": "Расчётный доход нетто"},
    "netto_fisso_ci": {"it": "Netto · bonus fisso + check-in", "en": "Net · bonus on fixed + check-ins",
                       "ru": "Нетто · бонус на фикс. + заселения"},
    "netto_solo_ci": {"it": "Netto · bonus solo check-in", "en": "Net · bonus on check-ins only",
                      "ru": "Нетто · бонус только на заселения"},
    "lordo_x": {"it": "lordo {x}", "en": "gross {x}", "ru": "брутто {x}"},
    "stip_nota": {
        "it": "Stima indicativa su base mensile: nella realtà imposta e contributi si versano a saldo e acconto e i "
              "contributi si deducono nell'anno in cui sono pagati. Per i valori esatti fa fede il commercialista.",
        "en": "Indicative monthly estimate: in practice tax and contributions are paid as balance and advance "
              "payments, and contributions are deductible in the year they are paid. Your accountant's figures "
              "prevail.",
        "ru": "Ориентировочный месячный расчёт: на практике налог и взносы уплачиваются в виде окончательного "
              "платежа и авансов, а взносы вычитаются в году их уплаты. Точные суммы определяет бухгалтер."},
    "stip_non_salvato": {"it": "Dati dello stipendio non salvati: restano solo fino alla chiusura dell'app.",
                         "en": "Earnings data not saved: it will only last until you close the app.",
                         "ru": "Данные о доходе не сохранены: они будут доступны только до закрытия приложения."},

    # ------------------------------------------------------------------ piè di pagina
    "ultimo_agg": {"it": "Ultimo aggiornamento dati: {quando} · {n} recensioni nuove",
                   "en": "Last data update: {quando} · {n} new reviews",
                   "ru": "Последнее обновление данных: {quando} · новых отзывов: {n}"},
    "nota_media": {
        "it": "La media qui è la media semplice delle recensioni nel periodo: il punteggio mostrato da {p} usa un "
              "calcolo diverso (ultimi 36 mesi).",
        "en": "The average shown here is the simple mean of the reviews in the period: the score displayed by {p} "
              "uses a different calculation (last 36 months).",
        "ru": "Здесь показано простое среднее отзывов за период: рейтинг на {p} рассчитывается иначе "
              "(за последние 36 месяцев)."},
    "le_piattaforme": {"it": "le piattaforme", "en": "the platforms", "ru": "платформах"},
}


def t(chiave: str, lingua: str, **valori) -> str:
    voce = T.get(chiave)
    if voce is None:
        return chiave
    testo = voce.get(lingua) or voce["it"]
    return testo.format(**valori) if valori else testo
