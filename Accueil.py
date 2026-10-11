# Exemple de logique dynamique pour la colonne Profil & Stratégie
def definir_strategie(note):
  note_str = str(note).strip().upper()
  if note_str in ['F', 'G']:
    return '🚨 Urgence Réglementaire (Passoire F/G)'
  else:
    return f'📈 Arbitrage Patrimonial (Classe {note_str})'


# Application sur votre DataFrame

