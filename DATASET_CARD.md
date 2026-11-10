# Agent_Dev_Ops — Dataset Card (v0.1)

## Objectif

Ce premier jeu de données sert à construire et évaluer les briques de lecture de logs : normalisation, extraction de composants, détection d'événements rares et recherche d'incidents similaires. Il ne prétend pas représenter des exécutions CI/CD complètes.

## Données réelles et provenance

`data/processed/observability_v0.1.jsonl` est généré exclusivement à partir des fichiers publics `*_2k.log_structured.csv` de [Loghub](https://github.com/logpai/loghub), pour BGL, HDFS, Linux, OpenStack, Spark et Zookeeper. Chaque ligne conserve l'URL de sa source et l'identifiant de ligne d'origine. Les hachages SHA-256 des fichiers d'entrée sont dans `data/processed/manifest.json`.

Loghub autorise la recherche et l'usage académique sous réserve de conserver son avis de licence et de citer le dépôt ainsi que Zhu et al., *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics*, ISSRE 2023. Voir `sources/loghub/LICENSE`.

## Schéma

| Champ | Description |
|---|---|
| `record_id` | Identifiant stable dérivé de la source |
| `source_*` | Provenance et localisation dans le fichier original |
| `timestamp_raw`, `date_raw`, `time_raw` | Temps tel que fourni par la source |
| `component`, `level`, `node` | Contexte technique lorsqu'il existe |
| `event_id`, `event_template`, `log_message` | Événement et message de log |
| `native_label` | Étiquette fournie par Loghub, sinon `null` |
| `failure_category`, `root_cause`, `remediation` | Vides intentionnellement ; à annoter avec des incidents CI/CD réels |

## Transformations et limites

- Les adresses e-mail, IPv4 et chaînes ressemblant à des jetons sont remplacées par des marqueurs.
- Les étiquettes natives sont préservées ; le pipeline n'invente ni cause racine ni correctif.
- BGL est la seule source sélectionnée qui porte une colonne `Label` dans l'échantillon. Les autres corpus sont majoritairement non annotés pour le diagnostic.
- Ce jeu permet le prototypage observabilité/AIOps. Il ne doit pas entraîner seul l'agent à proposer ou exécuter des corrections CI/CD.

## Suite obligatoire : corpus CI/CD propriétaire anonymisé

Pour l'objectif final, ajouter des exécutions réelles de GitHub Actions, GitLab CI ou Jenkins avec : logs par étape, commit/diff minimal, environnement, issue/PR de résolution, résultat post-correctif et approbation humaine. Les secrets doivent être masqués avant toute persistance ou inférence.
