# ZSTiB Plan Monitor

Monitoruje:

https://zstib.edu.pl/plan-lekcji

GitHub Actions uruchamia skrypt co 5 minut. Gdy wykryje zmianę w planie,
wysyła wiadomość na Discord webhook.

## Uruchomienie

1. Utwórz nowe repozytorium na GitHubie, np. `zstib-plan-monitor`.
2. Wrzuć do niego całą zawartość tego folderu **razem z folderem `.github`**.
3. Na Discordzie wejdź:
   `Ustawienia kanału -> Integracje -> Webhooki -> Nowy webhook`.
4. Skopiuj URL webhooka.
5. Na GitHubie wejdź:
   `Settings -> Secrets and variables -> Actions -> New repository secret`.
6. Nazwa:
   `DISCORD_WEBHOOK`
7. Wartość:
   URL webhooka z Discorda.
8. Wejdź w `Actions -> Monitor planu ZSTiB -> Run workflow`, żeby zrobić
   pierwsze uruchomienie.

Pierwszy run tylko zapamiętuje aktualny plan i nie wysyła alarmu.
Każda późniejsza wykryta zmiana wyśle powiadomienie.

## Ważne

GitHub Actions nie gwarantuje uruchomienia dokładnie co 5 minut. Przy dużym
obciążeniu GitHuba scheduled workflow może wystartować z opóźnieniem.

Plik `state.json` jest automatycznie aktualizowany przez GitHub Actions.
