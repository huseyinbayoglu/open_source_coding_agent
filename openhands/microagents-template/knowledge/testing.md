---
triggers:
  - test
  - pytest
  - coverage
---

# Testing skill (anahtar kelimeyle tetiklenir)

<!--
  Bu bir "knowledge microagent" ornegidir. repo.md'den farki:
  - knowledge/ alt klasorunde durur
  - frontmatter'daki "triggers" kelimelerinden biri kullanicinin mesajinda gecince yuklenir
    (her zaman degil) -> Claude Code'daki "skill" mantigi.
  Projene gore cogalt: deploy.md, db-migrations.md, frontend.md ...
  Yeri: <projen>/.openhands/microagents/knowledge/testing.md
-->

Test ile ilgili bir görev geldiğinde:

- Yeni davranış eklediğinde mutlaka test de ekle/güncelle.
- Testleri çalıştır: `pytest -q`. Hepsi yeşil olana kadar düzelt.
- Bir bug düzeltiyorsan, önce bug'ı yakalayan başarısız bir test yaz, sonra düzelt (regresyon).
- Dış servisleri (HTTP, DB, LLM çağrıları) mock'la; testler ağ/gerçek kaynak gerektirmemeli.
- Test isimleri davranışı anlatsın: `test_login_rejects_expired_token` gibi.
