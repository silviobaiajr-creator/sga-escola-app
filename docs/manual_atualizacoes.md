# 🚀 Atualização: Avaliação Turbo & Inteligência BNCC

Implementei todas as funcionalidades solicitadas para transformar a experiência de uso do **SGA-H**.

## 1. Login Automático (Sessão Persistente)
*   **O que mudou:** Você não precisa mais fazer login toda vez que recarregar a página.
*   **Como funciona:** O sistema lembra de você (usando um arquivo seguro no servidor) até que você clique em **"Sair (Logout)"**.

## 2. Nova Aba: Avaliação (Refatorada)
A tela de lançamentos foi totalmente reconstruída para velocidade:
*   **Filtros no Topo:** Data, Bimestre e Turma agora ficam visíveis no topo para fácil acesso.
*   **Seleção Hierárquica:** Primeiro escolha a **Disciplina**, depois a **Habilidade (BNCC)** e por fim o **Objetivo Específico**.
*   **Tabela de Lançamento Rápido:** Adeus cards gigantes! Agora você tem uma **Tabela Editável**:
    *   Veja a lista de alunos da turma.
    *   Selecione o Nível (1-4) diretamente na tabela.
    *   Clique em **"💾 Salvar Avaliações"** para gravar as notas de uma vez só.
    *   **Alerta de Duplicidade:** O sistema avisa com um ícone ⚠️ se o aluno já possui nota naquele objetivo/bimestre.

## 3. Inteligência Artificial & BNCC (Fonte: Planilha)
*   **Planilha BNCC:** O sistema agora lê a aba `bncc_competencies` da sua planilha para entender o contexto pedagógico.
    *   **Transparência:** Clique em **"🧠 Explicação Pedagógica & Contexto"** para ver a justificativa da IA.
*   **Controle de Quantidade:** Você decide quantos objetivos (1 a 5) o "Sub-Chef" deve gerar.
*   **Custo Zero:** Usando a planilha, o custo é irrisório.

## 4. Nova Aba: Biblioteca (Mobile-First)
*   **Visualização em Cartões:** Projetada para o celular, agora suas rubricas aparecem em cartões fáceis de ler.
*   **Filtros:** Pesquise por Disciplina ou Código BNCC.

## 5. Relatórios Otimizados
*   **Heatmap Inteligente:**
    *   **Legenda Numérica:** O gráfico mostra códigos curtos ("Obj 1") e a legenda completa fica abaixo.
    *   **Filtro de Habilidade:** Foque em uma habilidade específica.
    *   **Modo Matriz:** No celular, arraste a tabela para o lado.

---
### 4. Refinamentos Finais (IA & UI)
- **Contexto Otimizado:** Substituímos o PDF pela Planilha (`bncc_competencies`) como fonte principal.
- **Explicação Inteligente:** Adicionado campo "Explicação Pedagógica".
- **Limpeza de UI:** Removido upload de PDF e corrigida a formatação da lista de objetivos.

---
## 6. Atualização v3.38 (14/02/2026): Refinamento de Fluxo e Correções

Nesta atualização, focamos em robustez e usabilidade para o planejamento pedagógico:

### ✨ Novidades
*   **Filtro de Série/Ano (Grade Filter):**
    *   Agora você pode filtrar as habilidades da BNCC por ano (ex: 6º Ano), facilitando encontrar o que precisa.
    *   **Blindagem:** Se uma turma não tiver habilidades cadastradas, o sistema avisa amigavelmente em vez de travar.

*   **Bloqueio Inteligente (Smart Lock):**
    *   **Segurança:** Se uma habilidade já foi **Aprovada**, ela é bloqueada para evitar edições acidentais.
    *   **Resgate de Rascunhos:** Se você começou um rascunho mas não terminou (régua vazia), o sistema **permite** que você entre para finalizar, mesmo se a habilidade já estiver aprovada por outros.

### 🐛 Correções Críticas
*   **Correção de "Sumiço" de Rascunhos:** Itens que estavam pendentes mas incompletos agora aparecem corretamente para edição.
*   **Proteção contra Crashes:** Corrigidos erros técnicos que ocorriam ao selecionar disciplinas vazias ou durante a filtragem de objetivos.
*   **Diferenciação Visual:** O sistema agora distingue claramente entre uma **Proposta Aguardando Aprovação** (já preenchida) e um **Rascunho** (ainda por fazer).

---
Estou à disposição para ajustes finais!
---
## 7. Atualização v3.41 (16/02/2026): Dashboards Avançados (Diagnóstico) 📊

Uma revolução na forma de visualizar o aprendizado! Focamos em mostrar **consistência** e **tendência**, não apenas notas soltas.

### 🎓 Para o Professor (Aba Relatórios)
*   **Trajetória de Aprendizagem (Scatter Plot):**
    *   **Tendência Real:** Veja se o aluno está evoluindo ou regredindo com a nova **Linha de Tendência**.
    *   **Meta Visual:** Uma linha verde mostra claramente quem atingiu o **Nível 3 (Proficiente)**.
    *   **Agrupamento BNCC:** Análise unificada pelo código da habilidade, ignorando variações de texto.
*   **Mapa da Turma (Heatmap):** 
    *   Uma matriz colorida (Vermelho a Verde) para identificar rapidamente alunos com dificuldades gerais.
*   **Saúde Acadêmica (Visão Aluno):**
    *   Gráfico duplo: Mostra a nota de cada dia (bolinha azul) e a **Média Acumulada** (linha laranja), revelando a estabilidade do aluno.

### 🏛️ Para a Coordenação (Visão Aluno)
*   **Diagnóstico Global:** 
    *   **Curva de Saúde Acadêmica:** Acompanhe a média geral do aluno acumulada ao longo do ano em TODAS as disciplinas.
    *   **Heatmap Temporal:** Identifique padrões de queda ou melhora por bimestre em cada matéria (ex: "Vai bem em História, mas caiu em Matemática no 2º Bimestre").

---
**Nota Técnica:** As visualizações agora utilizam `statsmodels` para cálculos estatísticos de tendência. Se vir algum erro de "ModuleNotFound", o sistema deve se corrigir automaticamente em instantes.

## 8. Atualização v3.42 (16/02/2026): Estabilidade dos Dashboards (Hotfix) 🔧
*   **Correção de Erros de Dados:**
    *   **KeyError (Objective/Level):** Corrigido bug onde o gráfico tentava acessar colunas que não existiam no resumo.
    *   **NameError (df_history):** Corrigida a referência à tabela de histórico para garantir que os gráficos de evolução funcionem perfeitamente.
    *   **Fallback Seguro:** Se a coluna "objetivo" não existir, o sistema cria uma padrão para evitar travamentos.

