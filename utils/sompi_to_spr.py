def sompis_to_spr(sompis, round_amount=None):
    if round:
        return round(sompis / 100000000, round_amount)
    return sompis / 100000000
