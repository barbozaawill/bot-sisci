from enum import Enum

class Setor(str, Enum):
    financeiro  = "Financeiro"
    gestao      = "Gestão"
    folha       = "Folha"
    fiscal      = "Fiscal"
    contabil    = "Contabil"
    geral       = "Geral"