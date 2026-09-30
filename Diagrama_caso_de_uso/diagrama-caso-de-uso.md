# Diagrama de caso de uso

## Atores

| Ator | Descrição | Casos de uso |
|------|-----------|--------------|
| Gestores | Professores e Secretaria | Enviar, Editar, Atualizar, Excluir |
| Alunos | Usuários finais | Visualizar, Enviar, Receber |
| Coordenação | Acompanhamento e supervisão | Visualizar, Enviar, Receber |

## Diagrama

```mermaid
flowchart LR
    G["Gestores<br/>(Professores, Secretaria)"]
    A["Alunos"]
    C["Coordenação"]

    subgraph S["Sistema"]
        direction TB
        UC1([Editar])
        UC2([Atualizar])
        UC3([Excluir])
        UC4([Enviar])
        UC5([Visualizar])
        UC6([Receber])
    end

    G --- UC1
    G --- UC2
    G --- UC3
    G --- UC4

    A --- UC4
    A --- UC5
    A --- UC6

    C --- UC4
    C --- UC5
    C --- UC6
```

## Matriz ator x caso de uso

| Caso de uso | Gestores | Alunos | Coordenação |
|-------------|:--------:|:------:|:-----------:|
| Enviar      | X | X | X |
| Editar      | X |   |   |
| Atualizar   | X |   |   |
| Excluir     | X |   |   |
| Visualizar  |   | X | X |
| Receber     |   | X | X |

## Observações

- Editar, Atualizar e Excluir são exclusivos dos gestores.
- Enviar é o único caso de uso compartilhado por todos os atores.
- Os casos de uso estão apenas com verbos; podem ser detalhados conforme o objeto gerenciado (ex.: Enviar aviso, Editar nota, Receber material).
