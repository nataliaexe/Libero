# Governança e limites do Libero

O Libero é um protótipo de pesquisa para cuidado domiciliar. Os princípios abaixo orientam o projeto; não significam que o produto tenha certificação clínica, regulatória ou de segurança.

## Princípios de projeto

1. **Dignidade:** tratar a pessoa como alguém com preferências e história próprias.
2. **Autonomia:** apoiar cuidadores e preservar decisões humanas.
3. **Beneficência e não maleficência:** preferir respostas acolhedoras e evitar escalonamentos automáticos não verificados.
4. **Transparência:** distinguir registros, inferências e propostas de ações.
5. **Equidade:** avaliar falsos positivos e vieses antes de qualquer uso real.

## Controles que existem no protótipo

- O edge aplica regras heurísticas e cooldowns para limitar eventos repetidos.
- O orquestrador retorna explicitamente `acoes_externas_executadas: false`; o código não liga para o SAMU ou para a polícia.
- Rotas protegidas usam autenticação por papéis e verificações por idoso.
- As detecções não são probabilidades calibradas e não foram validadas clinicamente.

## Garantias que ainda não existem

- Ações e decisões não têm trilha de auditoria persistente, imutável ou com hash garantido.
- Não há detecção automática comprovada de viés ou certificação LGPD, GDPR, HIPAA ou ANVISA.
- Não há validação clínica, acordo de nível de serviço, disponibilidade 24/7 ou garantia de detecção.
- Não há integração ativa de chamadas para serviços de emergência nem confirmação de entrega de alertas à rede de cuidado.

Qualquer avaliação de saúde, segurança ou crise deve ser conduzida por pessoas qualificadas. Use dados fictícios em apresentações e não faça alegações médicas ou de prevenção garantida.
