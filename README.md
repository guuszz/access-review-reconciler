# Access Review Reconciler

Pequeno utilitário local para apoiar revisões periódicas de acesso: compara uma lista fictícia de pessoas ativas com um inventário de contas e produz uma fila de itens para revisão humana.

## Problema que aborda

O NIST SP 800-53 Rev. 5, controle AC-2(j), prevê revisão periódica de contas ([fonte NIST](https://csrc.nist.gov/CSRC/media/Projects/risk-management/800-53%20Downloads/800-53r5/SP_800-53_v5_1-derived-OSCAL.pdf)). A CISA recomenda que proprietários de aplicações e dados revisem e reconciliem periodicamente contas e privilégios ([guia CISA de IAM](https://www.cisa.gov/sites/default/files/2023-12/ESF%20IDENTITY%20AND%20ACCESS%20MANAGEMENT%20RECOMMENDED%20BEST%20PRACTICES%20FOR%20ADMINISTRATORS%20PP-23-0248_508C.pdf)). Isso fundamenta a existência da atividade de gestão de acesso, não a demanda pelo formato deste protótipo: ele apenas reconcilia duas exportações fictícias e não comprova conformidade. Entrevistas com pessoas que executam revisões ainda são necessárias para validar o fluxo operacional e as regras de uma solução real.

## MVP

- Recebe dois CSVs locais: pessoas (`email,name,status`) e contas (`email,system,account_type`).
- Compara e-mails sem diferenciar maiúsculas/minúsculas e remove espaços externos.
- Distingue inventários repetidos do mesmo sistema/tipo de conta de contas válidas em sistemas diferentes; endereço de e-mail sozinho não define uma conta única.
- Sinaliza conta sem pessoa ativa correspondente, correspondência ambígua e e-mail vazio.
- Não recomenda revogação automática; a saída é uma fila para revisão humana.
- Usa dados sintéticos de exemplo e não envia dados pela rede.

## Executar

Requer Python 3.11+ e biblioteca padrão. Instalar localmente:

```powershell
python -m pip install --editable .
```

Depois executar:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m access_review.cli examples/people.csv examples/accounts.csv --exceptions examples/exceptions.csv
```

Saída esperada para os exemplos: JSON com `review_required: 1` e `exceptions_documented: 1`; o bot de CI é uma exceção documentada, enquanto a conta do CRM continua para revisão. A CLI retorna status `1` quando há itens que exigem revisão, `0` quando a fila está vazia e `2` em caso de entrada inválida.

## Formato dos CSVs

Pessoas: `email,name,status` — somente `active` conta como ativa.

Contas: `email,system,account_type` — `account_type` é informativo. Exceções opcionais: `email,reason`; uma exceção só evita a pendência quando há justificativa não vazia e a identidade corresponde a uma conta ainda sem pessoa ativa. Exceções inválidas ou sem correspondência também viram pendência.

## Limitações

- E-mail é apenas chave de demonstração. Sistemas reais precisam de um identificador estável e regras para aliases, contas técnicas, licenças, prestadores e fontes de dados incompletas.
- Uma conta órfã é uma pendência, não prova de acesso indevido ou de desligamento.
- Não conecta a diretórios, RH, nuvem ou aplicações; não altera nem desativa contas.
- Validar regras e utilidade com pessoas que executem revisão de acessos antes de ampliar.
