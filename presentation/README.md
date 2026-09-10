# Apresentação de defesa

Duas versões do mesmo conteúdo, com a mesma sequência argumentativa e os mesmos
dados:

| Arquivo | Formato | Origem |
|---|---|---|
| `defesa-dissertacao.pptx` | PowerPoint/Keynote, 54 slides | `build_defesa.py` (python-pptx) |
| `defesa.pdf` | Beamer clássico, 53 quadros | `defesa.tex` (XeLaTeX) |

A versão Beamer usa tema `miniframes` + blocos arredondados, tipografia serifada
(Times New Roman, como a dissertação) e rodapé de três caixas no estilo Madrid.
Os anexos ficam fora da contagem de quadros (`4/37`, não `4/53`).

## Estrutura

| Bloco | Slides | Conteúdo | Tempo alvo |
|---|---|---|---|
| — | 1–2 | Capa e roteiro | 1 min |
| I | 3–6 | Motivação, pergunta, objetivos e hipóteses | 3 min |
| II | 7–10 | Referencial teórico (Cap. 1) | 3 min |
| III | 11–15 | Base empírica: fontes, indicadores e fatos estilizados (Cap. 2) | 3 min |
| IV | 16–19 | Estratégia empírica: shift-share, datação e exposição *ex-ante* | 3 min |
| V | 20–26 | Resultados: event study, DiD, heterogeneidade, SLX, mediação, quantílica, robustez | 7 min |
| VI | 27–30 | Estudos de caso territoriais em Minas Gerais | 3 min |
| VII | 31–37 | Contrafactuais, implicações, balanço das hipóteses e conclusões | 3 min |
| Anexos | 38–54 | Séries complementares e trajetórias dos quatro casos | sob demanda |

**Total: ~25 minutos.** Cada slide traz notas do apresentador com o roteiro de fala
e o tempo estimado (visíveis no modo apresentador).

## Identidade visual

- Fundo branco; laranja `#FF693A` e azul `#353F56` (CEDEPLAR).
- Logo institucional de `assets/logo/logo-cedeplar.png`; nos divisores de seção
  usa-se uma variante com o texto em branco, gerada automaticamente.
- Tipografia **Arial**, presente em macOS, Windows, Keynote, PowerPoint e Google
  Slides. A escolha é deliberada: Calibri não está registrada no sistema em todas
  as máquinas e a substituição de fonte quebraria o alinhamento dos blocos.
- Índices matemáticos ($E_i$, $Y_{it}$) usam subscrito real, não caracteres
  Unicode — Arial não cobre o bloco de extensões fonéticas.

## Regenerar

Ambas as versões consomem as figuras produzidas pela renderização da dissertação:

```bash
quarto render thesis/index.qmd          # → thesis/index_files/figure-pdf/*.pdf
```

### PPTX

```bash
pip install python-pptx pymupdf pillow
python presentation/build_defesa.py     # → presentation/defesa-dissertacao.pptx
```

O script rasteriza `thesis/index_files/figure-pdf/*.pdf` para PNG em 4× e guarda o
resultado em `presentation/.cache-figuras/` (ignorado pelo git, reconstruído se o
PDF de origem for mais recente).

### Beamer

```bash
xelatex -output-directory=presentation presentation/defesa.tex
xelatex -output-directory=presentation presentation/defesa.tex   # 2ª passada: sumário
```

O Beamer inclui os PDFs das figuras diretamente, sem rasterização. Requer apenas
o que já vem no TinyTeX do projeto — a internacionalização usa `polyglossia`
(não `babel-portuges`), e a numeração de anexos é feita com um contador manual
(não `appendixnumberbeamer`), para dispensar instalações adicionais.

Para 4:3 clássico, troque `aspectratio=169` por `aspectratio=43` na primeira linha
de `defesa.tex`.
