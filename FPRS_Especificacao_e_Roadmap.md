# FPRS — Especificação de Regras de Negócio e Roadmap de Implementação

**Functional Pharmacotherapy Risk Score (FPRS) — Modelo 3 (sem interações medicamentosas)**

Documento de referência para a construção do webapp (backend Python + SQLite, hospedagem Railway, frontend a definir).
Baseado na planilha `FPRS_Modelo3_sem_interacoes_v13.xlsx`.

---

## 1. Objetivo da ferramenta

A partir da lista de medicamentos de um paciente (até 25, um por linha), a ferramenta calcula um escore de risco farmacoterapêutico funcional (FPRS) e classifica o paciente em **alto** ou **baixo risco**, sinalizando quando há indicação de revisão da farmacoterapia.

O escore combina três componentes:

1. **Polifarmácia** — número de medicamentos em uso.
2. **Sobrecarga anticolinérgica/sedativa** — pelo fator de afinidade de cada medicamento.
3. **MPI / Beers** — medicamento potencialmente inapropriado, como rede de captura subordinada à sobrecarga (ver hierarquia em RN-05).

Esta versão **não** considera interações medicamentosas (ver Seção 7).

---

## 2. Modelo de dados

### 2.1 Tabela `medicamentos_base` (origem: aba `Base_Fixa`, 599 registros)

| Campo | Tipo | Origem (coluna na planilha) | Observação |
|---|---|---|---|
| `nome_normalizado` | texto (PK) | 1 | Chave de busca, sempre em minúsculas |
| `classe_observacao` | texto | 2 | Classe / observação clínica |
| `pim_beers` | inteiro (0/1) | 3 | Flag de MPI pelos critérios de Beers 2023 |
| `afinidade_ac` | texto | 5 | `No` / `Low` / `Moderate` / `High` |
| `afinidade_sedativa` | texto | 7 | `No` / `Low` / `Moderate` / `High` |
| `peso_afinidade` | inteiro (0–3) | 8 | Máximo entre afinidade AC e sedativa |
| `fonte` | texto | 9 | Referência/justificativa |

> As colunas 4 (`AC`) e 6 (`Sedativo`) da planilha são flags 0/1 que **não entram no cálculo** — podem ser descartadas na migração.

### 2.2 Tabela `aliases` (origem: aba `Alias_Map`, 650 registros)

| Campo | Tipo | Observação |
|---|---|---|
| `entrada_aceita` | texto (PK) | Grafia/sinônimo aceito, em minúsculas |
| `nome_normalizado` | texto (FK) | Nome canônico correspondente |

57 entradas remapeiam para um nome canônico diferente (ex.: `acetylsalicylic acid` → `aspirin`).

### 2.3 Tabela `parametros` (origem: aba `Parameters`)

Valores configuráveis do escore — ver Seção 6.

---

## 3. Normalização do nome do medicamento

**RN-01 — Normalização**
Para cada entrada não vazia do paciente:
1. Aplicar `lower(trim(entrada))`.
2. Buscar o resultado em `aliases.entrada_aceita`. Se houver correspondência, usar `nome_normalizado`.
3. Se não houver alias, usar o próprio `lower(trim(entrada))` como nome normalizado.

**RN-02 — Encontrado na base**
Buscar o nome normalizado em `medicamentos_base`.
- Se **não** existir: medicamento marcado como *não encontrado*, contribuição = 0, e gerar observação **"Revisar grafia/nome genérico ou inserir na Base_Fixa"**.
- Medicamento não encontrado **continua contando** para o número total de medicamentos (a contagem incide sobre a entrada do paciente, não sobre o match).

---

## 4. Regra hierárquica de contribuição por medicamento

**RN-03 — Sobrecarga pelo fator de afinidade**
O peso de cada medicamento é o **maior** entre afinidade AC e afinidade sedativa, segundo a escala:

| Afinidade | Peso |
|---|---|
| No | 0 |
| Low | 1 |
| Moderate | 2 |
| High | 3 |

Medicamento com dupla propriedade (AC **e** sedativa) conta **uma única vez**, com o maior peso. (Validado: `peso_afinidade = max(AC, sedativa)` em 599/599 registros da base.)

**RN-04 — Deduplicação**
Se o mesmo medicamento normalizado aparecer mais de uma vez na lista do paciente, **apenas a primeira ocorrência** contribui; repetições contam 0. (Implementação: manter um conjunto de nomes já pontuados ao iterar a lista.)

**RN-05 — MPI/Beers adicional (hierarquia afinidade > PIM)**
A afinidade tem prioridade sobre o PIM. O componente PIM funciona como rede de captura **subordinada**: um medicamento só soma **+0,5** (parâmetro `pim_beers_adicional`) se **todas** as condições forem verdadeiras:
- é PIM (`pim_beers = 1`), **e**
- o peso de afinidade é **0** (não foi pontuado pela sobrecarga AC/sedativa), **e**
- é a primeira ocorrência desse medicamento na lista (deduplicação de RN-04).

Se o medicamento já pontuou por afinidade, o PIM **não** acrescenta nada (evita dupla contagem).

**Regra consolidada de contribuição por medicamento** (ordem de avaliação):

```
1. Não encontrado na base         -> contribuição 0 (gera aviso)
2. Senão, se peso_afinidade > 0    -> contribuição = peso_afinidade (1, 2 ou 3)
3. Senão, se pim_beers = 1         -> contribuição = 0,5
4. Senão                           -> contribuição 0
(Em todos os casos: medicamento repetido só conta na primeira ocorrência.)
```

---

## 5. Agregação e classificação

**RN-06 — Polifarmácia**
Contar os medicamentos informados (entradas não vazias) e pontuar:

| Nº de medicamentos | Pontos |
|---|---|
| 0–4 | 0 |
| 5–9 | 0,5 |
| ≥10 | 1 |

**RN-07 — FPRS final**
```
FPRS = Σ (contribuição por medicamento)  +  pontos de polifarmácia
```
Onde a soma das contribuições já equivale a (sobrecarga por afinidade + PIM adicional), conforme a regra consolidada da Seção 4.

**RN-08 — Classificação e alerta**
- **FPRS > 1,5** → categoria **"Alto risco"** + alerta **"Necessidade de revisão da farmacoterapia"**.
- **FPRS ≤ 1,5** → categoria **"Baixo risco"** + mensagem **"Sem indicação prioritária de revisão pelo FPRS"**.

O ponto de corte 1,5 é o único limiar de decisão clínica.

---

## 6. Parâmetros configuráveis

| Parâmetro | Chave sugerida | Valor |
|---|---|---|
| Polifarmácia 0–4 | `poli_0_4` | 0 |
| Polifarmácia 5–9 | `poli_5_9` | 0,5 |
| Polifarmácia ≥10 | `poli_10_mais` | 1 |
| Afinidade baixa | `afinidade_low` | 1 |
| Afinidade moderada | `afinidade_moderate` | 2 |
| Afinidade alta | `afinidade_high` | 3 |
| MPI/Beers adicional | `pim_beers_adicional` | 0,5 |
| Capacidade máxima | `capacidade_max` | 25 medicamentos |
| Ponto de corte alto risco | `corte_alto_risco` | 1,5 |

Recomenda-se manter todos esses valores em tabela/configuração (não hardcoded), para facilitar ajustes durante a validação acadêmica.

---

## 7. Fora de escopo nesta versão

**Interações medicamentosas.** A planilha documenta uma lógica de interações (Moderada = 0,5; Grave/Alta/Major/Severe/Contraindicated = 1; apenas a interação de maior gravidade é incorporada; fonte prioritária DrugBank Non-Commercial), mas o **Modelo 3 não a aplica**. Fica registrada para uma versão futura.

---
## 8. Roadmap de implementação

### Fase 0 — Fundação (preparação)
- Definir repositório, estrutura de pastas (backend/, frontend/, data/) e controle de versão.
- Decidir framework de backend (sugestão: **FastAPI** — leve, tipado, documentação automática via OpenAPI, encaixa bem em prova de conceito acadêmica).
- Resolver as decisões pendentes da Seção 8 (especialmente o limiar ≥10) antes de codar.

### Fase 1 — Camada de dados
- Modelar o schema SQLite com as três tabelas (`medicamentos_base`, `aliases`, `parametros`).
- Escrever script de importação (ETL) que lê as abas da planilha e popula o banco — fonte única de verdade dos dados.
- Versionar a base como arquivo de seed, para reprodutibilidade científica.

### Fase 2 — Motor de cálculo (núcleo)
- Implementar como módulo puro e isolado (sem dependência de banco nem de web): entrada = lista de nomes; saída = detalhamento por medicamento + componentes + FPRS + classificação.
- Cobrir as regras RN-01 a RN-08.
- **Testes automatizados** validando contra o `Exemplo_teste` da planilha e contra casos de borda (lista vazia, duplicatas, não encontrado, dupla afinidade, exatamente 5 e exatamente 10 medicamentos, escore na fronteira de 1,5).

### Fase 3 — API
- Endpoints: cálculo do FPRS (recebe lista de medicamentos, devolve resultado detalhado), consulta de medicamento na base, e listagem de parâmetros.
- Validação de entrada (limite de 25 medicamentos, normalização) e tratamento de "não encontrado".
- Documentação automática da API.

### Fase 4 — Frontend
- Tela de entrada: lista de até 25 medicamentos + campos de identificação do paciente (ID, idade, data, observação).
- Tela de resultado: tabela por medicamento (normalizado, encontrado?, afinidade, contribuição, observação) + os três componentes + FPRS final + categoria + alerta clínico.
- Indicação visual clara de alto risco e dos medicamentos não encontrados.

### Fase 5 — Implantação
- Deploy do backend no Railway (banco SQLite como volume persistente ou seed embarcado).
- Deploy do frontend.
- Variáveis de ambiente e configuração de parâmetros sem necessidade de redeploy do código.

### Fase 6 — Validação e documentação acadêmica
- Conferência cruzada: rodar uma amostra de pacientes na ferramenta e na planilha e comparar resultados (devem bater 100%).
- Registrar limitações conhecidas (PIM dormente, ausência de interações).
- Documentar fontes e versão da base utilizada.

### Evolução futura (pós-dissertação)
- Incorporar o módulo de interações medicamentosas (Seção 7).
- Painel de administração da base de medicamentos.
- Histórico de avaliações por paciente.

---
