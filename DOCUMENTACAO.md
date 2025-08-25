# Documentação dos Arquivos de Tradução

## Formato CSV

Os arquivos de tradução estão no formato CSV (Comma-Separated Values) com as seguintes características:

### Codificação
- UTF-8 com BOM
- Separador: vírgula (,)
- Delimitador de texto: aspas duplas (")

### Campos

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Index | Número sequencial do registro | 0, 1, 2... |
| Key | Identificador único no jogo | ACHIEVEMENT_CATEGORY_1 |
| MsgJp | Texto original em japonês | 冒険 |
| MsgEn/MsgPt | Texto traduzido | Adventure/Aventura |
| GmdPath | Caminho do arquivo GMD | ui\00_message\achievement\achievement_category.gmd |
| ArcPath | Caminho do arquivo ARC | \ui\uGUIAchievement.arc |
| ArcName | Nome do arquivo ARC | uGUIAchievement.arc |
| ReadIndex | Índice de leitura no arquivo | 0 |

## Tipos de Conteúdo

### Conquistas (Achievements)
- **ACHIEVEMENT_CATEGORY_**: Categorias de conquistas
- **ACHIEVEMENT_INFO_**: Descrições de conquistas específicas

### Habilidades (Skills)
- **CUSTOM_SKILL_**: Habilidades customizáveis
- **ABILITY_**: Habilidades passivas

### Interface
- Mensagens de sistema
- Textos de menus
- Notificações

## Convenções de Tradução

### Português
- Manter consistência terminológica
- Adaptar termos específicos do jogo quando necessário
- Preservar formatação especial (tags HTML, códigos de cor)

### Formatação Especial
- `<COL ffdc78>`: Tags de cor
- `<PADM>`: Tags de controle/input
- `<KC>`: Códigos de tecla

## Exemplo de Registro

```csv
0,ACHIEVEMENT_CATEGORY_1,冒険,Aventura,ui\00_message\achievement\achievement_category.gmd,\ui\uGUIAchievement.arc,uGUIAchievement.arc,0
```

Este registro traduz a categoria de conquista "冒険" (aventura em japonês) para "Aventura" em português.