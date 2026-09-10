# Roteiro de fala — defesa de dissertação

**Flávio Hugo Pangracio Silva · CEDEPLAR/UFMG**

Alvo: 20 minutos. São 2.750 palavras faladas: 20min20 a 135 palavras por minuto,
que é um ritmo de defesa confortável, mais as pausas nos gráficos.

Convenções: `[ ]` é indicação de cena, não texto falado. **/** = respire.
*Itálico* = ênfase na palavra. `(0:00)` = tempo acumulado ao **iniciar** o trecho.

---

## Abertura — capa `(0:00 · 1min10)`

[Capa no telão. Olhe para a banca antes de começar.]

Boa tarde a todos.

Antes de começar, gostaria de agradecer à banca por ter aceitado o convite e pelo
tempo dedicado à leitura do trabalho. Professor Igor Tupy, professor Frederico
Jayme, obrigado pela disponibilidade. **/**

Ao professor Marco Aurélio Crocco, meu orientador, agradeço pela orientação ao
longo destes dois anos e, principalmente, pela paciência com as várias versões
deste trabalho que não deram certo antes desta aqui. **/**

Agradeço também ao CEDEPLAR, aos professores e aos colegas de turma, e à minha
família, que aguentou os fins de semana em que eu estive fisicamente presente e
mentalmente dentro de uma regressão. **/**

Dito isso: a dissertação se chama *Digitalização Bancária e Assimetrias Regionais
no Brasil*, e trata da reconfiguração das redes de agências, da qualidade do
crédito e do deslocamento espacial desse crédito entre 2009 e 2023.

Vou apresentar em cerca de vinte minutos e, ao final, fico à disposição para as
arguições.

---

## Roteiro `(1:10 · 25s)`

[Slide do sumário.]

A apresentação tem sete blocos. Os dois primeiros são curtos: problema e
referencial. O terceiro e o quarto explicam de onde vêm os dados e como eu
identifico o efeito. O quinto é o núcleo, com os resultados. Depois desço ao
território, com quatro casos em Minas, e fecho com as implicações.

---

## Bloco I — Motivação e problema `(1:35 · 2min)`

### Moeda, território e o duplo movimento

[Slide da citação de Crocco et al.]

Começo pelo incômodo que originou o trabalho.

A digitalização financeira é vendida como mecanismo democratizante. Se o banco cabe
no celular, a agência deixa de importar, e o município pequeno passa a ter o mesmo
acesso que a capital. **/**

Só que o que se observa no território é um movimento duplo. Nas periferias, a rede
física recua *e*, ao mesmo tempo, a exclusão digital persiste. Os dois processos
acontecem no mesmo lugar, nas mesmas pessoas.

Em 2022, quarenta e quatro por cento dos municípios brasileiros não tinham uma única
agência. E dez cidades concentravam um quarto de todas as agências do país e mais da
metade do saldo de crédito. **/**

A pergunta que me interessa não é *se* a digitalização chegou ao território, porque
de algum modo ela chegou a quase todo lugar. É o que ela fez com a *natureza* do
crédito que circula ali.

### Pergunta, objetivo e hipóteses

[Slide da pergunta. Depois, avance para as hipóteses sem parar muito.]

Formalmente: em que medida a digitalização do sistema bancário, ao mudar a
geografia da prestação de serviços financeiros, redefine, atenua ou aprofunda as
desigualdades regionais brasileiras?

Isso se desdobra em três eixos, cada um com um desfecho mensurável: a rede física, o
viés metropolitano e a *qualidade* do crédito, que é a parte mais original do
trabalho.

[Slide das hipóteses. Não leia as cinco.]

Cinco hipóteses guiam o texto, e eu volto a elas no final com o balanço. A primeira
é de datação. Da segunda à quarta, uma para cada eixo. E a quinta testa o
mecanismo: a ideia de que o efeito sobre o crédito periférico viaja *através* do
fechamento de agências. Guardem essa última, porque é a que mais apanhou dos dados.

---

## Bloco II — Referencial teórico `(3:35 · 1min45)`

[Slide da cadeia teórica.]

A base é pós-keynesiana, e se articula em quatro elos que eu resumo rápido.

O ponto de partida é Keynes: a moeda não é neutra. Sob incerteza, o agente prefere
reter riqueza líquida a imobilizá-la na produção. **/**

Dow, Chick e, no Brasil, Crocco e Amado regionalizam esse argumento. Na periferia a
incerteza informacional é maior, e a resposta racional do banco é reter ativos
líquidos e encurtar o crédito. Não é má vontade da agência: é preferência pela
liquidez operando no espaço.

Somem a isso a teoria dos lugares centrais, em que o serviço simples se dispersa e
o complexo se concentra, e o circuito fecha: a poupança periférica migra para os
centros e volta, quando volta, em piores condições.

[Slide da promessa e da contrapartida.]

A evidência internacional é convergente. Leyshon encontra, no Reino Unido,
fechamento de vinte e cinco por cento em áreas pobres contra dezessete em áreas
ricas. Nguyen mostra que cada agência fechada reduz o crédito a pequenas empresas em
quase meio milhão de dólares por ano. **/**

E aqui está a lacuna. A tradição pós-keynesiana brasileira documentou bem o peso da
concentração espacial sobre a preferência pela liquidez, mas não incorporou a
digitalização como variável capaz de mudar a natureza da intermediação. E a
evidência internacional sobre substituição de canais nunca tinha sido testada em
escala municipal no Brasil, com indicadores que separassem *volume* de *qualidade*.

É aí que o trabalho se coloca.

---

## Bloco III — Base empírica `(5:20 · 2min05)`

[Slide das fontes.]

Sobre os dados, rapidamente.

O painel integra seis fontes que na literatura nacional costumam aparecer separadas.
A principal é a ESTBAN do Banco Central, a estatística bancária mensal por município;
somam-se o PIB do IBGE, as pesquisas da FEBRABAN e a RAIS. **/**

O resultado é um painel censitário: cinco mil quinhentos e setenta municípios,
quinze anos, cerca de oitenta e três mil observações município-ano e doze
indicadores construídos por mim. Tudo roda em R, com código público. Uma ressalva
que eu assumo desde já: o estoque de agências de 2023 está subnotificado, então a
análise de cobertura física é truncada em 2022.

[Slide dos indicadores. Foque só no IRF/IRE.]

Dos doze indicadores, peço licença para destacar um, porque é ele que sustenta a
contribuição original: a razão IRF sobre IRE. Financiamentos de longo prazo
divididos por empréstimos de curto prazo, direto das contas 161 e 162 da ESTBAN.

Por que ela importa? Duas cidades podem ter o mesmo volume de crédito por unidade de
PIB e carteiras completamente diferentes: numa o crédito é longo e relacional, na
outra é rotativo e padronizado. O volume não distingue as duas. Essa razão
distingue.

[Gráfico de transações.]

Dois fatos antes da estratégia. O primeiro é que o salto digital é recente e
abrupto: o mobile banking ultrapassa o internet banking em 2015, mas o volume de
transações por habitante só dispara em 2020, com a pandemia e o Pix. **/**

E reparem numa coisa nesse gráfico, porque ela define tudo o que vem depois: a série
é *nacional*. Tem variação no tempo e nenhuma variação no espaço.

[Mapa do Brasil.]

O segundo fato é a desigualdade da geografia bancária. Cada área cinza é um
município sem agência; no Nordeste são sessenta por cento deles. A maior parte do
território recebe menos crédito do que produz, e o excedente se acumula em meia dúzia
de nós metropolitanos.

---

## Bloco IV — Estratégia empírica `(7:25 · 2min)`

[Slide do shift-share.]

Isso me leva ao problema central de identificação.

O tratamento varia no tempo, mas é idêntico para todos os municípios. Não existe
município que tenha ficado de fora do Pix. Sem variação entre unidades, não há grupo
de controle. **/**

A saída é um desenho *shift-share*, à la Bartik, na formulação de Borusyak e
coautores: eu multiplico o choque nacional, comum a todos, por uma medida de
exposição *ex-ante* que varia entre municípios. A uniformidade espacial, que era o
obstáculo, vira a vantagem analítica: se o choque é o mesmo para todos, a variação do
efeito só pode vir da estrutura prévia de cada lugar.

A especificação é um diferenças-em-diferenças com tratamento contínuo, efeitos fixos
de município e de ano e erros clusterizados.

[Slide dos testes de quebra.]

Para comparar antes e depois eu preciso saber quando é o depois, e não quis escolher
a data no olho. Rodei Bai-Perron, Quandt-Andrews e testes de Chow sobre sete séries
da FEBRABAN.

O resultado é 2020. É a única data que aparece ao mesmo tempo em penetração e em
utilização, é quebra dominante em cinco das seis séries, e coincide com marcos
institucionais conhecidos. A janela é 2014 a 2019 antes, 2020 a 2023 depois. **/**

Assumo a ressalva: o Bai-Perron também acusa quebras em 2014-2016 e 2018-2019.
Volto a isso nas limitações.

[Mapa de exposição.]

A exposição é a primeira componente principal de cinco variáveis, todas anteriores a
2014, para evitar contaminação por antecipação. Ela absorve quarenta e cinco por
cento da variância, e todos os pesos têm o mesmo sinal. É isso que me autoriza a ler
o score como um gradiente unidimensional de vulnerabilidade à substituição digital.

E o mapa mostra que esse gradiente tem geografia: a mediana do semiárido é positiva
em quase nove décimos de desvio-padrão; a do Sudeste é negativa.

---

## Bloco V — Resultados `(9:25 · 5min50)`

### Event study

[Gráfico do event study. Este slide exige precisão: não corra.]

Chego aos resultados, começando pela dinâmica. É o slide que mais exige cuidado de
leitura.

O desfecho é o log do número de agências. Olhem os coeficientes *antes* de 2020: são
positivos e caem monotonicamente rumo a zero. Depois de 2020 estabilizam perto de
zero. **/**

Coeficientes pré-tratamento positivos significam que as tendências paralelas
estritas são *rejeitadas*. Eu não escondo isso, porque é justamente aí que está a
interpretação correta. O que eles dizem é que entre 2014 e 2019 havia convergência:
os municípios mais expostos vinham *ganhando* cobertura relativa. A partir de 2020
isso cessa e o gap congela. **/**

Portanto o coeficiente negativo do próximo slide não mede redução absoluta do
estoque. Mede o efeito contrafactual sobre a *continuidade* dessa convergência. É
leitura mais modesta que a usual, e é a que os dados sustentam.

### DiD — efeitos médios

[Tabela do DiD.]

Esta é a tabela central. Três resultados.

Cada desvio-padrão de exposição está associado a menos um vírgula seis por cento no
log do estoque de agências, significativo a um por cento. O portfólio de crédito
local ficou mais concentrado, com menos modalidades disponíveis no município.

E o mais importante: a razão IRF sobre IRE cai dois vírgula um por cento por
desvio-padrão. O crédito que sobrou nesses municípios é mais curto e mais
padronizado. **/**

Agora reparem no que *não* deu resultado: a centralidade creditícia tem efeito médio
indistinguível de zero. Guardem esse zero.

### Heterogeneidade

[Tabela por faixa de porte.]

Quando eu abro por porte, a hipótese inicial precisa ser corrigida.

Eu esperava um gradiente linear: quanto mais o município dependia da agência física,
mais ele perderia. Não é isso que aparece. A retração se concentra nas *duas
pontas*: nas metrópoles, por substituição ativa; nas pequenas, por inviabilidade
econômica. A faixa médio-grande preservou melhor a rede, pelo papel de hub
regional. **/**

Já na qualidade do crédito o gradiente é inequívoco: a razão IRF sobre IRE cai
dezessete pontos percentuais a mais na faixa de cem a quinhentos milhões do que nas
metrópoles.

O que decide o desfecho não é o quanto o município dependia da agência. É a *função*
que aquela agência cumpria no território.

### Spillovers espaciais

[Slide do SLX-DiD.]

Este é, para mim, o resultado mais forte do trabalho.

Eu acrescento ao modelo o efeito da exposição *dos vizinhos*, com uma matriz de
contiguidade. E aparece o padrão que organiza toda a interpretação: nos quatro
desfechos, efeito direto e spillover têm *sinais opostos*. **/**

O município perde dois vírgula dois por cento das agências; a vizinhança ganha dois
vírgula sete. A centralidade sai de um lugar e reaparece nos polos adjacentes. O
portfólio local se estreita, o dos vizinhos se diversifica. O crédito longo sai da
periferia e ressurge no entorno.

A digitalização não *eliminou* agências, centralidade ou crédito longo do
território. Ela os reorganizou no espaço. **/**

E isso resolve o zero que eu pedi para vocês guardarem. O spillover tem magnitude
da mesma ordem do efeito direto, às vezes maior. O coeficiente médio do DiD não
espacial é uma mistura de dois efeitos contrários que se cancelavam. O zero não era
ausência de efeito. Era soma de efeitos opostos.

### Mediação

[Diagrama da mediação.]

Aqui é onde a hipótese cinco apanhou dos dados, e eu prefiro apresentar isso de
frente.

A hipótese era que o efeito sobre o crédito longo viajava *pelo* fechamento de
agências. O elo estrutural se confirma, e com força: onde tem agência, tem mais
financiamento longo. **/**

Só que o efeito direto, o canal que *não* passa pela agência, é negativo e
significativo. Os dois canais empurram em direções opostas e quase se anulam. É o que
MacKinnon chama de mediação inconsistente, um *suppression effect*. Na prática: nessa
subamostra o canal dominante é tecnológico, não mecânico. A carteira piora *mesmo com
a agência aberta*.

E preciso ser honesto sobre o alcance disso. A mediação exige municípios com agência
nos dois períodos, o que exclui justamente as periferias mais frágeis. A hipótese
cinco provavelmente vale lá. Eu só não consigo testá-la lá.

### Quantílica

[Gráfico da regressão quantílica.]

A média responde o que acontece no município típico. Não responde se o efeito é o
mesmo em toda a distribuição.

Na razão IRF sobre IRE o perfil é um U assimétrico: o coeficiente mais negativo está
no décimo percentil, justamente onde o crédito longo já era escasso. Onde faltava, a
digitalização aprofundou a falta. O único ponto que escapou foi o terceiro quartil, e
minha hipótese, ainda não testada, é a presença de cooperativas e bancos públicos.

### Robustez

[Tabela de robustez. Vá rápido, mas não pule a ressalva.]

Robustez, bem rápido. Controles reais e matrizes espaciais alternativas sustentam os
resultados. No placebo com data falsa em 2014 o coeficiente fica dez vezes menor e
perde significância. **/**

O que exige cautela é o DiD sintético, que diverge. Ele exige binarizar o tratamento,
e o tercil de menor exposição concentra as metrópoles, que *também* perderam
agências: o estimador acaba comparando perda na periferia com perda no centro. Por
isso o cerne da inferência é o gradiente contínuo, e os estimadores que exigem
binarização entram como apoio, não como substitutos.

---

## Bloco VI — Estudos de caso `(15:15 · 1min45)`

[Mapa de Minas.]

Tudo o que eu mostrei até aqui é média de milhares de municípios. A camada
qualitativa existe para testar se essa média descreve algum lugar concreto.
Selecionei quatro municípios mineiros em quatro níveis de centralidade financeira,
no mesmo estado, para manter banco de fomento e regulação estadual constantes.

[Tabela comparativa dos quatro casos.]

Belo Horizonte perde um terço da rede física e ainda assim *ganha* centralidade: o
IRC sobe de um vírgula oito para dois vírgula seis. Não porque BH melhorou, mas
porque o entorno piorou mais. **/**

Juiz de Fora perde vinte e um por cento, a menor perda relativa entre as maiores, e
mantém o IRC estável. A leitura que eu proponho é que âncoras institucionais, a
universidade, a base de serviços, sustentam a função bancária local.

Betim é o contraexemplo mais eloquente. PIB acima de vinte bilhões, região
metropolitana, acesso digital pleno. Perdeu trinta e seis por cento das agências e
setenta por cento da centralidade. Tinha PIB, não tinha base financeira própria. **/**

E Almenara, no Baixo Jequitinhonha, quarenta mil habitantes, não fechou *nenhuma*
agência no período todo, graças aos bancos públicos. Ainda assim a razão IRF sobre
IRE caiu quarenta e três por cento.

Almenara sintetiza o argumento: manter a agência aberta não garantiu manter a função
financeira.

Quatro municípios do mesmo estado, o mesmo coeficiente de regressão, trajetórias
opostas. Uma recomendação de política baseada na média agregada falharia em três
destes quatro territórios.

---

## Bloco VII — Implicações e conclusões `(17:00 · 2min30)`

[Tabela do balanço das hipóteses.]

O balanço das cinco hipóteses. Três se sustentam, e a terceira sai mais forte do que
entrou, porque o SLX mostrou que não é só declínio diferenciado: é transferência
territorial identificável. **/**

Duas foram reformuladas pelos dados: a hipótese dois estava certa na direção e errada
na forma, e a cinco virou um *suppression effect*. E eu faço questão de dizer que o
aprendizado está menos nas hipóteses que se sustentaram e mais nesses dois pontos em
que a evidência me obrigou a abandonar a linearidade.

[Slide das implicações. Priorize a primeira.]

Daí saem três implicações, e eu me concentro na primeira, que decorre diretamente da
mediação.

A regulação precisa migrar de *quantidade de agências* para *funções financeiras
mantidas no território*. Se a carteira se deteriora mesmo com a agência aberta,
contar agências é contar a coisa errada. Os modelos de obrigação de serviço universal
dos setores postal e de telecomunicações são uma referência adaptável, desde que
calibrados por vulnerabilidade, não por quilômetro em linha reta. **/**

As outras duas, rapidamente: calibrar os instrumentos de crédito pela heterogeneidade
espacial, porque uma política uniforme produz efeitos diferentes em Almenara e em
Betim; e coordenar regulação bancária, infraestrutura digital e política regional,
que hoje operam em silos.

[Slide de contribuições e limitações.]

Assumo quatro limitações, e cito as duas mais sérias. A série de digitalização é
nacional; com desagregação municipal, o desenho de identificação seria melhor. E as
quebras de 2014-2016 e 2018-2019 coincidem com rupturas institucionais que uma data
única não separa do choque digital.

[Slide final de conteúdo.]

Fecho onde comecei.

Moeda e crédito não são variáveis exógenas ao desenvolvimento regional. São forças
que estruturam a geografia das oportunidades. A digitalização financeira não
suspendeu essa dinâmica: reorganizou-a. **/**

A rede física recuou seletivamente e a convergência entre municípios congelou. A
qualidade do crédito se descolou do volume. O efeito é deslocamento, não
desaparecimento: o que sai da periferia reaparece nos polos vizinhos. E o canal
dominante é tecnológico, o que significa que a carteira se transforma mesmo com a
agência aberta.

Nada disso é argumento contra a digitalização. É argumento a favor de olhar para onde
o crédito vai parar, e não só para quantos canais existem, para que a promessa de
inclusão não vire, na prática, mais um vetor de desigualdade.

---

## Encerramento `(19:30 · 20s)`

[Slide de agradecimento.]

Era isso.

Muito obrigado pela atenção, e coloco-me à disposição da banca para as arguições.

---

## Notas de execução

**Tempo.** 2.750 palavras faladas. A 135 por minuto dá 20min20 corridos; com as
pausas nos gráficos, conte 21 a 22 reais, então tenha a lista de cortes abaixo na
cabeça. Cronometre em casa lendo em voz alta, não mentalmente: a diferença costuma
ser de dois minutos.

**Se estiver atrasado**, corte nesta ordem:

1. A quantílica inteira, dizendo só "a regressão quantílica mostra que o efeito é
   mais forte onde o crédito longo já era escasso" (`-45s`).
2. A robustez, reduzida a "placebo e controles reais sustentam; o DiD sintético
   diverge, e eu explico a razão nos anexos" (`-40s`).
3. Os dois primeiros parágrafos do Bloco II (`-40s`).

**Se sobrar tempo**, volte ao event study e ao SLX. São os dois slides em que a
banca vai querer precisão.

**Ritmo.** Os trechos numéricos tendem a acelerar. Force a desaceleração em três
pontos: a leitura dos coeficientes pré-tratamento, os sinais opostos do SLX e o
*suppression effect*.

**Números falados.** Os poucos decimais que sobraram estão por extenso de propósito.
Dizer "menos um vírgula seis por cento" sai melhor do que tentar converter na hora, e
a maior parte dos coeficientes eu troquei por percentuais redondos, que a banca
acompanha melhor de ouvido do que casas decimais.

**Postura defensiva.** Três pontos em que a banca provavelmente vai puxar, e em
todos o roteiro já antecipa a fragilidade em vez de esperar a pergunta: tendências
paralelas rejeitadas, restrição amostral da mediação, e divergência do DiD
sintético. Antecipar é mais forte do que ser pego.

**Data.** A capa está com 10 de agosto de 2026. Confirme antes de imprimir.
