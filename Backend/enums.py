from enum import Enum


class Setor(str, Enum):
    financeiro = "Financeiro"
    gestao = "Gestao"
    folha = "Folha"
    fiscal = "Fiscal"
    contabil = "Contabil"
    geral = "Geral"