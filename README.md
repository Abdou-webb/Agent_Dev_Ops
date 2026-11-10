# Agent_Dev_Ops

Projet Agent IA de diagnostic des échecs CI/CD et de déploiement, conçu pour des actions graduées, auditables et validées par un humain.

## État initial

On a commence le projet par presenter une dataset reelle  : [la fiche de données](DATASET_CARD.md) et `data/processed/observability_v0.1.jsonl`. Le dataset traité est versionné. Pour le reconstruire depuis Loghub :

```powershell
./scripts/fetch_sources.ps1
python scripts/build_dataset.py
```

Vérifier le dataset déjà versionné :

```powershell
python scripts/validate_dataset.py
```

## Collecte CI/CD réelle

Le collecteur GitHub Actions importe les jobs réellement exécutés, y compris les échecs, dans un dataset distinct. Il ne fabrique pas de cause racine ni de correctif.

```powershell
$env:GITHUB_TOKEN = "votre-token-fine-grained-actions-read"
python scripts/collect_github_actions.py --repo Abdou-webb/Agent_Dev_Ops
```

Les données sont ajoutées dans `data/processed/cicd_v1.0.jsonl`. Pour un dépôt privé, le token doit avoir uniquement les permissions de lecture Actions et Contents nécessaires ; ne le placez jamais dans le fichier ou les logs.

## Feuille de route

1. **Dataset v0.1 — terminé** : logs publics réels et traitement reproductible.
2. **Dataset CI/CD v1.0** : collecteur GitHub Actions/Jenkins, masquage des secrets, annotation humaine des causes et correctifs.
3. **Triage** : règles + recherche sémantique pour identifier le job et l'étape fautive.
4. **Évaluation** : jeux de test séparés par dépôt et période ; métriques de diagnostic, utilité et sécurité.
5. **Actions contrôlées** : lecture seule, relance idempotente hors production, puis PR brouillon ; rollback uniquement avec validation explicite.

## Politique de sécurité

Les secrets ne sont pas envoyés au modèle. Toute action est journalisée avec preuve, politique appliquée, approbateur et résultat. Les opérations de production et les rollbacks exigent une approbation humaine.
