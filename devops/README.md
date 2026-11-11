# FogoCerto · Secure DevOps Tools & Cloud Computing

Dockerfile, Terraform, pipeline GitHub Actions (build, Gitleaks, Semgrep, Trivy, deploy) e observabilidade.

> Terraform: `state` e `.tfvars` nunca entram no repositório (já bloqueados no `.gitignore`).

# Ficha Técnica - DevOps FogoCerto

- **Diagrama:** Github Actions ➔ Docker (Non-root) ➔ CloudFront ➔ PWA.
- **Responsabilidade:** Nuvem cuida de CDN/Infra; Equipe cuida de App, Segurança (Gitleaks/Trivy) e Deploy.
- **LGPD:** Nenhuma coleta de dados pessoais sensíveis; apenas município no `localStorage`.
- **Custo:** R$ 0,00 (Free Tier de armazenamento estático).
- **URL Pública:** [INSERIR O LINK GERADO AQUI]
