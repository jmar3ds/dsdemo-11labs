# Magalu Probable Production Stack

Public-source-grounded reference for stack-aware Python integration code in the ElevenLabs FDE Strategist pilot artifact (WhatsApp da Lu voice deployment). Compiled 2026-05-20 by Lode (Ranging trio).

Conventions: HIGH = directly disclosed by Magalu/Luizalabs in a primary source. MEDIUM = strongly implied by aggregated signals (job postings, multiple secondary sources, repo evidence). LOW = inferred default for a Brazilian retailer of Magalu's size where nothing is publicly disclosed.

---

## TL;DR for the Python demo

Assume Magalu runs **Python (FastAPI) and Go services on Kubernetes (their own Teresa-style PaaS, now portable to Magalu Cloud Kubernetes and GKE)**, with **PostgreSQL/MySQL OLTP, BigQuery for analytics, Kafka and Google Pub/Sub for events, and Twilio Flex on top of the Meta WhatsApp Business API for the operator-facing surface**. The Lu AI brain is **Google Gemini Flash + Pro orchestrated by an in-house agentic system, with lighter open models on Magalu Cloud**. Build integration code that plugs into a `POST /webhook` Meta WhatsApp Cloud API receiver, fans out via a `MagaluPlatformClient` that wraps internal REST + Kafka publish, and explicitly labels every assumed boundary.

---

## 1. Languages

| Language | Confidence | Evidence |
|---|---|---|
| **Python** | HIGH | Luizalabs runs a recurring Python backend bootcamp (2024-2025) teaching FastAPI + SQLAlchemy. Public OSS: `tutorial-python-brasil` (356 stars), `shared-memory-dict`, `lasier` (circuit breaker), `django-toolkit`, `correios`. |
| **Go** | HIGH | `teresa` (557 stars) is Luizalabs' open-source Kubernetes deployment PaaS, written in Go. Job postings consistently list Go alongside Python. |
| **Java** | MEDIUM | Older Magalu monolith was Java; QCon SP 2017 and InfoQ Brasil talks describe migration from Java-based legacy to microservices. Still likely present in legacy edges. |
| **Node.js** | MEDIUM | Listed alongside Python/Java in backend job specs from the `backend-br/vagas` repo. |
| **TypeScript** | MEDIUM | `noahjs` (Next.js starter, updated Feb 2026) signals a modern TS frontend stack. |
| **Kotlin / Swift** | MEDIUM | InfoQ Brasil presentation by Ubiratan Soares (Magalu mobile engineer) describes reactive Android/iOS architecture for the consumer app. |

Sources: [Luizalabs GitHub](https://github.com/luizalabs), [Luizalabs Python bootcamp coverage](https://casado.dev/curso-gratuito-bootcamp-luizalabs-back-end-python), [InfoQ Brasil mobile reactive talk](https://www.infoq.com/br/presentations/arquiteturas-reativas-e-a-experiencia-mobile-no-magazine-luiza/).

For the pilot artifact: **lead with Python (FastAPI)**. It is the most defensible language choice and matches Luizalabs' own bootcamp curriculum exactly.

---

## 2. Web frameworks

| Framework | Confidence | Evidence |
|---|---|---|
| **FastAPI** | HIGH | Luizalabs bootcamp explicitly teaches "creating RESTful APIs with FastAPI, SQLAlchemy, tests and security" (2024-2025 cohorts). |
| **Django** | MEDIUM | `django-toolkit` repo exists; Django remains common in older Python services. |
| **Flask** | LOW-MEDIUM | Plausible in legacy webhook handlers; not directly cited. |

Recommendation: pin the demo on **FastAPI** with Pydantic models. It matches Luizalabs' stated teaching stack and is the right async profile for webhook + Kafka producer code.

---

## 3. Databases

| Layer | Most likely choice | Confidence | Evidence |
|---|---|---|---|
| **OLTP** | PostgreSQL (primary) + MySQL (legacy/order systems) | MEDIUM | Magalu Cloud GA (Dec 2024) shipped self-managed MySQL first and PostgreSQL-compatible offerings, signaling those are the workloads they themselves run internally. Both are standard Brazilian-retail defaults. |
| **Caching** | Redis | MEDIUM | Industry default. `shared-memory-dict` Luizalabs repo signals an active interest in low-latency cache primitives; pairs naturally with Redis in production. |
| **Analytics warehouse** | BigQuery | HIGH | Google Cloud case study (2018, updated since) confirms Magalu migrated big-data workloads from Hadoop to managed GCP services. GCP is the disclosed primary analytics cloud. |
| **Search** | Elasticsearch / OpenSearch | LOW | Inferred default for a 4.3M-SKU catalog. Not directly disclosed. |
| **Document / NoSQL** | Firestore or MongoDB | LOW-MEDIUM | Firestore via the disclosed Firebase relationship; MongoDB is a common Brazilian-retail default. |

Sources: [Google Cloud Magazine Luiza case study](https://cloud.google.com/customers/magazine-luiza), [BNamericas on Magalu Cloud GA](https://www.bnamericas.com/en/news/magalu-cloud-expands-portfolio-and-launches-cloud-infrastructure-products).

Default for the demo: **PostgreSQL on Magalu Cloud (PostgreSQL-compatible managed service) for the order/customer store, Redis for session and idempotency keys.**

---

## 4. Cloud and Infrastructure

| Component | Choice | Confidence | Evidence |
|---|---|---|---|
| **Primary public cloud** | Google Cloud Platform | HIGH | 2018 GCP case study; pre-Black-Friday migration of 113 apps in <60 days; Vertex AI / Gemini relationship for Lu. |
| **Own cloud** | Magalu Cloud (operational since Apr 2024, GA Dec 2024) | HIGH | Self-built, runs on **proprietary data centers in São Paulo and Fortaleza**. Earlier reporting that called it "AWS-backed" was inaccurate. The platform offers AWS-compatible APIs such as S3-compatible object storage but runs on Magalu's own physical infrastructure. |
| **AWS** | Partial / legacy | MEDIUM | Job postings still list AWS as a required skill alongside GCP. Likely runs in parallel for some workloads. |
| **Container orchestration** | Kubernetes everywhere | HIGH | Confirmed on GKE (case study); Magalu Cloud's own Kubernetes service (Dec 2024 GA) scales to 2,000 nodes; `teresa` is their open-source K8s PaaS. |
| **Internal PaaS** | Teresa (open source, Go) | HIGH | 557-star Luizalabs repo. Used to deploy apps to K8s clusters. |
| **Infrastructure-as-code** | Terraform | HIGH | `terraform-modules` repo, updated Jun 2025. |
| **API management** | Apigee | HIGH | Google Cloud case study cites Apigee decoupling the 150K-line legacy monolith. May have been replaced or supplemented since 2018 but pattern is established. |
| **Identity** | ID Magalu (Turia IAM) | HIGH | Launched at Web Summit Rio 2024. Public CLI exists (`id-magalu-cli`). |

Sources: [Google Cloud Magazine Luiza case study](https://cloud.google.com/customers/magazine-luiza), [Folha Vitória on Magalu Cloud](https://www.folhavitoria.com.br/tecnologia/a-primeira-cloud-brasileira-com-escala-global/), [IT Forum Magalu Cloud anniversary](https://itforum.com.br/noticias/magalu-cloud-completa-um-ano-provocar-mercado/), [TecMundo on Magalu Cloud launch](https://www.tecmundo.com.br/mercado/274838-magalu-anuncia-magalu-cloud-primeiro-servico-nuvem-totalmente-brasileiro.htm).

For the demo: **assume containerized FastAPI service deployed via Teresa to a K8s cluster on Magalu Cloud, with cross-cloud egress to GCP services (Vertex AI, BigQuery) and the Meta WhatsApp Cloud API.**

---

## 5. Messaging and queueing

| System | Confidence | Evidence |
|---|---|---|
| **Apache Kafka** | HIGH | Backend job postings consistently require Kafka experience for Luizalabs senior backend roles. |
| **Google Pub/Sub** | MEDIUM-HIGH | Same job postings list "Kafka and Google Pub/Sub" together. Pairs naturally with the disclosed GCP footprint. |
| **AWS SQS** | LOW-MEDIUM | Possible in legacy or AWS-resident workloads. Not directly cited. |
| **RabbitMQ** | LOW | Standard Brazilian-retail option; no specific Magalu evidence. |

Source: aggregated [Luizalabs job post on backend-br/vagas](https://github.com/backend-br/vagas/issues/2832).

For the demo: **publish order-status events to Kafka (`magalu.orders.events.v1`), consume from Pub/Sub for cross-cloud Vertex AI signals.**

---

## 6. WhatsApp surface (CRITICAL for the pilot)

This is the most important section because the pilot lives here.

**Two distinct WhatsApp deployments are publicly disclosed:**

### 6a. Seller-facing onboarding flow (since ~2022): Twilio Flex

| Detail | Source |
|---|---|
| Platform: **Twilio Flex + WhatsApp Business API** | [Twilio Magalu case study](https://customers.twilio.com/en-us/magalu) |
| Scale: 200,000 sellers; 2x onboarding conversion (21% → 46%); 20% sales lift via WhatsApp | Twilio case study |
| Implementation: 2 months, end-to-end communication framework overhaul | Twilio case study |
| Pattern: Click-to-WhatsApp ads → chatbot routing → live agent escalation in Flex | Twilio case study |

**Confidence: HIGH.** Twilio is the disclosed BSP for the seller surface.

### 6b. Consumer-facing "WhatsApp da Lu" AI Commerce (launched Nov 2025): Meta direct + Google + Magalu Cloud

| Detail | Source |
|---|---|
| Partnership: **Luizalabs + Meta + Google** (no third-party BSP cited) | [Exame on "Cérebro da Lu"](https://exame.com/inteligencia-artificial/lu-do-magalu-ganha-cerebro-com-ia-e-vira-vendedora-dentro-do-whatsapp/), [Martech Magalu AI Commerce](https://martech.com.br/2025/11/magalu-inaugura-o-ai-commerce-e-permite-compras-completas-pelo-whatsapp/) |
| Models: **Gemini Flash + Pro (5B and 12B params) for vision + heavier comparisons**, lighter open-source models on Magalu Cloud for FAQ, larger LLMs for deeper reasoning | Exame, Nov 2025 |
| Architecture: **agentic orchestrator** selects per-turn which specialist agent acts (product search, spec comparison, cart management, small talk) | Exame, Nov 2025 |
| Voice: Lu understands slang, regionalisms, pauses, casual audio explanations | [IT Forum Magalu WhatsApp Lu](https://itforum.com.br/noticias/magalu-whatsapp-lu/) |
| Scale: launched to 1M recurring customers pre-Black Friday 2025; full rollout to 30M+ active consumers by end-2025 | Multiple sources |
| Conversion: 3x vs traditional in-app search | Exame, Nov 2025 |

**Confidence: HIGH** that for the consumer voice surface (the one ElevenLabs would replace or complement), Magalu integrates **directly with the Meta WhatsApp Cloud API** (no Twilio BSP layer), built by Luizalabs in partnership with Meta and Google.

For the demo: **write the webhook receiver against the Meta WhatsApp Cloud API directly** (`graph.facebook.com/v18.0/{phone_number_id}/messages`), and explicitly comment that the seller surface uses Twilio Flex while the consumer surface (the pilot target) goes Meta-direct.

---

## 7. AI / ML infrastructure

| Layer | Disclosed choice | Confidence |
|---|---|---|
| **LLM (primary)** | Google Gemini Flash + Gemini Pro via Vertex AI | HIGH |
| **LLM (secondary)** | Lighter open-source models hosted on Magalu Cloud | HIGH |
| **Conversation framework** | In-house agentic orchestrator (per-turn agent selection); earlier Lu generations used Dialogflow CX | HIGH for orchestrator, MEDIUM for residual Dialogflow |
| **Vector store** | Not disclosed; Vertex AI Vector Search is the natural default | LOW |
| **GPU infrastructure** | Magalu Cloud GPU-as-a-service roadmap announced for 2025, including inference + RAG offerings | HIGH |
| **Experimentation** | Multi-model A/B testing referenced ("they test different LLMs to understand which fits which situation") | MEDIUM |

Sources: [Exame, "Cérebro da Lu" Nov 2025](https://exame.com/inteligencia-artificial/lu-do-magalu-ganha-cerebro-com-ia-e-vira-vendedora-dentro-do-whatsapp/), [Convergência Digital on Lu IA](https://convergenciadigital.com.br/mercado/lu-do-magalu-quer-ser-a-protagonista-da-ia-no-varejo/), [BNamericas on Magalu Cloud GPU roadmap](https://www.bnamericas.com/en/news/magalu-cloud-expands-portfolio-and-launches-cloud-infrastructure-products).

For the demo: **the ElevenAgents integration plugs in as a new specialist agent inside Magalu's existing orchestrator.** This is the credible framing.

---

## 8. Observability

Not directly disclosed in any primary source surfaced in this research.

| Tool | Confidence | Reasoning |
|---|---|---|
| **Datadog** | LOW-MEDIUM | Dominant in commercial APM market in Brazil; common in retail of Magalu's size. |
| **Prometheus + Grafana** | MEDIUM | Standard with their Kubernetes-heavy stack; Magalu Cloud's K8s offering implies operators familiar with the Prom ecosystem. |
| **New Relic** | LOW | Possible, no signal. |
| **Firebase Crashlytics** | HIGH | Disclosed in the GCP case study for mobile app stability monitoring. |

For the demo: **assume Prometheus + Grafana for backend metrics, Crashlytics for mobile** when discussing instrumentation hooks. Mark as inferred.

---

## 9. Payments

| Component | Disclosed |
|---|---|
| **MagaluPay** (digital wallet) | HIGH |
| **PIX integration** | HIGH (primary funding rail) |
| **Hub Pagamentos** (acquired Dec 2020, R$290M): full SPB + PIX integration | HIGH |
| **Boleto** | Being phased out per CNN Brasil interview |

Sources: [MagaluPay site](https://especiais.magazineluiza.com.br/magalupay/), [Electronic Payments International on Hub acquisition](https://www.electronicpaymentsinternational.com/news/brazilian-retailer-magazine-luiza-inks-56m-deal-to-acquire-payments-firm-hub/).

For the demo: **integrate payment via MagaluPay/PIX**; do not invent a Stelo or Cielo integration.

---

## 10. Confidence summary for the artifact

Anchor the Python demo on the **HIGH-confidence pieces** so a Magalu engineer reads it and nods:

1. FastAPI service in Python
2. Deployed via Teresa onto Kubernetes on Magalu Cloud
3. Webhook receiver speaking Meta WhatsApp Cloud API directly
4. PostgreSQL for orders (managed on Magalu Cloud)
5. Kafka for event fan-out
6. Vertex AI / Gemini as the existing Lu brain (we plug ElevenLabs in as a voice specialist agent that joins the orchestrator)
7. MagaluPay + PIX for transaction flow
8. Apigee at the API edge (legacy but plausibly still in front)

For the **MEDIUM/LOW** pieces (Redis, Pub/Sub, Datadog vs Prometheus, vector store), include them as **commented assumptions** in the code: `# Assumed: Redis for idempotency keys. Magalu has not publicly disclosed their caching layer; Redis is the most likely default given their K8s + microservices pattern.`

That single line of intellectual honesty is what makes the artifact credible instead of presumptuous.

---

## Sources (consolidated)

Primary:
- [Luizalabs GitHub organization](https://github.com/luizalabs)
- [Teresa: Luizalabs K8s deployment PaaS](https://github.com/luizalabs/teresa)
- [Google Cloud: Magazine Luiza case study](https://cloud.google.com/customers/magazine-luiza)
- [Twilio: Magalu Flex + WhatsApp case study](https://customers.twilio.com/en-us/magalu)
- [Exame, "Cérebro da Lu" with IA on WhatsApp (Nov 2025)](https://exame.com/inteligencia-artificial/lu-do-magalu-ganha-cerebro-com-ia-e-vira-vendedora-dentro-do-whatsapp/)
- [Martech, Magalu AI Commerce launch (Nov 2025)](https://martech.com.br/2025/11/magalu-inaugura-o-ai-commerce-e-permite-compras-completas-pelo-whatsapp/)
- [IT Forum, WhatsApp da Lu launch](https://itforum.com.br/noticias/magalu-whatsapp-lu/)
- [IT Forum, Magalu Cloud one-year retrospective](https://itforum.com.br/noticias/magalu-cloud-completa-um-ano-provocar-mercado/)
- [BNamericas, Magalu Cloud product launches Dec 2024](https://www.bnamericas.com/en/news/magalu-cloud-expands-portfolio-and-launches-cloud-infrastructure-products)
- [TecMundo, Magalu Cloud launch](https://www.tecmundo.com.br/mercado/274838-magalu-anuncia-magalu-cloud-primeiro-servico-nuvem-totalmente-brasileiro.htm)
- [Folha Vitória, Magalu Cloud first Brazilian cloud at global scale](https://www.folhavitoria.com.br/tecnologia/a-primeira-cloud-brasileira-com-escala-global/)
- [Convergência Digital, Lu IA protagonist coverage](https://convergenciadigital.com.br/mercado/lu-do-magalu-quer-ser-a-protagonista-da-ia-no-varejo/)

Secondary / corroborating:
- [Luizalabs Python bootcamp coverage (Casa do Dev)](https://casado.dev/curso-gratuito-bootcamp-luizalabs-back-end-python)
- [Luizalabs backend job spec on backend-br/vagas](https://github.com/backend-br/vagas/issues/2832)
- [InfoQ Brasil, Reactive Mobile at Magazine Luiza](https://www.infoq.com/br/presentations/arquiteturas-reativas-e-a-experiencia-mobile-no-magazine-luiza/)
- [QCon SP 2017, Ubiratan Soares (Magazine Luiza)](https://qconsp.com/sp2017/speaker/ubiratan-soares.html)
- [Electronic Payments International, Hub Pagamentos acquisition](https://www.electronicpaymentsinternational.com/news/brazilian-retailer-magazine-luiza-inks-56m-deal-to-acquire-payments-firm-hub/)
- [MagaluPay official site](https://especiais.magazineluiza.com.br/magalupay/)
- [Luizalabs Medium publication root](https://medium.com/luizalabs)
