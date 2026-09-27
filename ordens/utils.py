from django.core.exceptions import ValidationError


def apenas_digitos(valor):
    """Retorna somente os dígitos de um valor informado pelo usuário."""
    return ''.join(filter(str.isdigit, str(valor or '')))


def primeiro_nome(nome_completo):
    """Extrai o primeiro nome de forma segura, sem quebrar com strings vazias."""
    partes = str(nome_completo or '').strip().split()
    return partes[0].capitalize() if partes else ''


def validar_cpf(cpf):
    """Valida CPF brasileiro e retorna o CPF limpo, apenas com números."""
    cpf = apenas_digitos(cpf)

    if len(cpf) != 11:
        raise ValidationError('O CPF deve conter exatamente 11 números.')

    if cpf == cpf[0] * 11:
        raise ValidationError('Este CPF é inválido.')

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito_1 = (soma * 10) % 11
    digito_1 = 0 if digito_1 == 10 else digito_1

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito_2 = (soma * 10) % 11
    digito_2 = 0 if digito_2 == 10 else digito_2

    if int(cpf[9]) != digito_1 or int(cpf[10]) != digito_2:
        raise ValidationError('CPF inválido! Por favor, confira os números digitados.')

    return cpf
