# Estante em Cartaz

Painel de acompanhamento diário de preços de livros na Amazon.com.br, com tema de cinema: cada livro é um "cartaz", com histórico de preço, termômetro de compra e estatísticas da lista.

**Ver o site:** https://zanitchy.github.io/estante-em-cartaz/

Este repositório guarda a **cópia pública** do painel. O original é um artefato privado no Claude, que recebe uma coleta de preços todo dia às 19h. A cópia daqui é uma fotografia dos dados e só muda quando é republicada.

| | |
|---|---|
| Livros acompanhados | 751 |
| Dias de histórico | 34 (06/10/2026 a 08/11/2026) |
| Capas | 751 miniaturas JPEG de 260 px |
| Última atualização desta cópia | 09/11/2026 |

---

## Relatório técnico

### 1. O que o painel faz

- Registra, uma vez por dia, o preço de cada livro da lista na Amazon.com.br.
- Mostra para cada livro o preço de hoje, o menor e o maior já vistos, o preço de capa, o preço do Kindle e a disponibilidade.
- Classifica o momento de compra (ótimo, bom, de costume, caro, estável) comparando o preço de hoje com o histórico do próprio livro.
- Agrupa edições diferentes do mesmo título, sugere preço-alvo, monta um carrinho que cabe num orçamento e exporta a lista para Excel.
- Reúne 31 análises num painel separado, "Padrões e estatísticas": preços e promoções, composição da lista, autores e autoras, editoras.

### 2. Arquitetura

O painel é uma página única, sem framework e sem etapa de build no navegador: HTML, CSS e JavaScript puro num só arquivo.

```
index.html          página inteira (estilos e código embutidos)
data/livros.json    cadastro: um objeto por livro
data/dias.json      histórico: um objeto por dia de coleta
capas/<ASIN>.jpg    miniatura da capa de cada livro
tools/build_site.py gera esta cópia a partir do artefato original
```

Dependências externas, carregadas só quando necessárias:

- Google Fonts (Bungee, Nunito, Literata, IBM Plex Mono).
- SheetJS 0.18.5 pelo cdnjs, apenas ao clicar em "Excel".

Os gráficos são SVG gerados à mão. A "biblioteca 3D" do topo usa só transformações CSS 3D, sem WebGL nem bibliotecas.

#### Diferenças entre o artefato original e esta cópia

| | Artefato (privado) | Cópia pública (este repositório) |
|---|---|---|
| Dados | banco do artefato, atualizado todo dia | arquivos JSON estáticos |
| Capas | arquivos anexos ao artefato | pasta `capas/` |
| Prioridade, carrinho, alvo, comprados, lidos | salvos no banco do dono | salvos no navegador de cada visitante (`localStorage`) |
| Adicionar livros | formulário que alimenta a fila da coleta | **removido** |
| Avisos no celular | notificação após a coleta | **removido** (depende do app do Claude) |
| Exportar Excel | recurso de download do artefato | download direto pelo navegador |

Nenhum dado pessoal do dono da lista é publicado: as marcações pessoais não fazem parte dos arquivos deste repositório.

### 3. Modelo de dados

**`data/livros.json`** — lista de livros. Campos principais:

| Campo | Significado |
|---|---|
| `asin` | código de 10 caracteres do produto na Amazon (o trecho depois de `/dp/` no link) |
| `titulo`, `autores[{nome, papel}]` | título e pessoas creditadas (autor, tradutor, ilustrador…) |
| `formato`, `idioma`, `paginas`, `editora`, `edicao`, `publicacao` | ficha técnica da edição |
| `isbn13`, `isbn10`, `dimensoes`, `peso`, `idade`, `ranking` | demais dados da ficha |
| `resumo` | sinopse da página do produto (`resumoAusente: true` quando a Amazon não tem descrição) |
| `precoLista` | preço de capa no dia da inclusão |
| `capa` | caminho da miniatura |
| `adicionado`, `origem` | data de entrada na lista e se veio pela fila de inclusão |

**`data/dias.json`** — uma entrada por coleta: `{data, coletadoEm, itens}`. Em `itens`, cada ASIN tem um registro compacto:

| Chave | Significado |
|---|---|
| `p` | preço do formato monitorado, em reais |
| `f` | `"o"` quando o preço é "a partir de", de vendedores parceiros |
| `l` | preço de capa (preço riscado) |
| `k` | preço do Kindle para compra |
| `ku`, `pr` | `1` se está no Kindle Unlimited / Prime Reading |
| `fs` | outros formatos à venda: `[nome, preço, marcas]` |
| `e`, `r` | estrelas e quantidade de avaliações |
| `d` | texto de disponibilidade ("Em estoque", "Somente 4 em estoque"…) |

Um livro sem registro num dia significa que não foi coletado naquele dia; sem `p` significa que estava indisponível.

### 4. Coleta de preços

A coleta roda como tarefa agendada do Claude, todo dia às 19h (horário de Brasília).

1. **Onde roda.** A Amazon bloqueia acessos vindos de servidores em nuvem, então a leitura das páginas é feita pelo navegador Chrome do dono da lista, com a extensão do Claude. A tarefa só lê páginas: não clica em botões nem compra nada.
2. **Como lê.** Um script na aba da Amazon busca cada página de produto (`/dp/<ASIN>`) na mesma origem, com três leituras em paralelo e pausas aleatórias, e extrai os campos do HTML.
3. **Regra de preço.** Vale o preço do formato selecionado no quadro de formatos da página. "A partir de" é marcado como oferta de parceiro. Preços de carrosséis, de usados e de Pix são ignorados.
4. **Checagem de qualidade.** Antes de gravar, cada livro é comparado com a coleta anterior. Se os formatos sumirem, se as avaliações variarem mais de 35% ou se o preço vier zerado, o livro é buscado de novo, até duas vezes.
5. **Livros novos.** Os livros da fila entram com ficha completa, sinopse e capa. As capas são baixadas do servidor de imagens da Amazon, reduzidas para 260 px de largura e gravadas em JPEG.
6. **Revisão final.** A tarefa confere se a fila ficou vazia, se todo livro tem título, capa e sinopse e se todos estão na coleta do dia, e relata o que ficou pendente.

### 5. Cálculos

**Preço de costume.** Mediana de todos os preços já registrados do livro. É a referência para "promoção" e para o índice da estante.

**Termômetro de compra.** Exige pelo menos 5 coletas com preço.

| Nível | Regra |
|---|---|
| Estável | diferença entre maior e menor preço abaixo de R$ 1 ou de 3% do maior |
| Ótimo | preço de hoje até 2% acima do menor já visto |
| Bom | mais de 2% abaixo do preço de costume |
| Caro | mais de 5% acima do preço de costume |
| De costume | os demais casos |

**Preço-alvo sugerido.** O menor preço já visto, para livros que não são estáveis.

**Índice da estante.** Para cada dia, a média de `preço do dia ÷ preço de costume` de todos os livros, com cada razão limitada entre 0,5 e 2 para um livro isolado não distorcer a média. Abaixo de zero, a lista como um todo está em promoção.

**Melhor dia da semana.** Média, por dia da semana, de quanto cada preço ficou acima ou abaixo do preço de costume do livro. Só entram livros cujo preço varia.

**Duração das promoções.** Sequências de dias seguidos com preço mais de 2% abaixo do preço de costume. Contam só as sequências já encerradas.

**Carrinho com orçamento.** Problema da mochila resolvido por programação dinâmica, com preços arredondados para o real acima. Cada livro do carrinho recebe uma pontuação (base fixa, mais bônus por prioridade, por momento de compra e por desconto), e o painel escolhe o conjunto de maior pontuação que cabe no orçamento.

**Edições do mesmo livro.** Dois cadastros são tratados como edições do mesmo título quando têm o mesmo título principal, os mesmos números no título e o mesmo autor.

**Marcas de qualidade no histórico.** Um dia é marcado com `?` quando os outros formatos somem naquele dia mas existem antes e depois, e com `⚠` quando o número de avaliações foge mais de 35% da referência e depois volta. Indicam página incompleta servida pela Amazon, não mudança real.

### 6. Gênero dos autores

A Amazon não informa o gênero de quem escreve. A classificação usada nas estatísticas de autoras e autores foi feita assim:

- Só conta quem está creditado como autor. Tradutores, ilustradores e organizadores ficam de fora.
- Os nomes presentes na lista em 08/11/2026 foram classificados manualmente, um a um.
- Coletâneas, editoras creditadas como autor e nomes que não permitem identificação ficam como "não identificado".
- Para nomes que entrarem depois, o gênero é estimado pelo primeiro nome, com base nos nomes já classificados. Essa estimativa pode errar.
- Um livro conta como "misto" quando tem pelo menos uma autora e um autor.
- Grafias diferentes do mesmo nome são unidas na contagem (por exemplo, "Lev Tolstói" e "Liev Tolstói").

### 7. Limitações conhecidas

- **Um preço por dia.** A coleta é feita uma vez, às 19h. Promoções-relâmpago que começam e terminam entre duas coletas não aparecem.
- **Histórico curto.** Com 34 dias, padrões como "melhor dia da semana" ainda são frágeis. O painel avisa quando a base é pequena.
- **Dependência do computador.** A coleta só acontece se o computador e o Chrome do dono da lista estiverem ligados no horário.
- **Páginas incompletas.** A Amazon às vezes serve a página sem o quadro de formatos ou com avaliações de uma só edição. A checagem de qualidade reduz o problema, e o que escapa fica marcado no histórico.
- **Preço de capa.** É o preço riscado informado pela Amazon, que nem sempre coincide com o preço sugerido pela editora.
- **Ranking de vendas.** É o do dia em que o livro entrou na lista, não é atualizado.
- **Cópia estática.** Os dados deste repositório não se atualizam sozinhos.

### 8. Como atualizar esta cópia

```
python3 tools/build_site.py <artefato.html> <pasta_do_banco> <pasta_do_site>
```

O script recebe o HTML do artefato e uma exportação do banco (`livros/*.json` e `dias/*.json`), remove o formulário de adição e os avisos, troca a leitura do banco pelos arquivos JSON e grava `index.html`, `data/livros.json` e `data/dias.json`. As capas ficam em `capas/<ASIN>.jpg`.

### 9. Créditos e avisos

- Preços, capas, sinopses e fichas vêm das páginas públicas de produto da Amazon.com.br e pertencem aos respectivos titulares. Aparecem aqui só para identificar cada livro e acompanhar seu preço.
- Este projeto é pessoal, sem vínculo com a Amazon e sem links de afiliado.
- Os preços mostrados são os do dia da coleta. Confira sempre o valor atual na página do produto antes de comprar.
- Painel construído com o Claude, da Anthropic.
