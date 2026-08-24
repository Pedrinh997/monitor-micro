from prometheus_client import Counter

# Métrica personalizada: conta quantas vezes o preço baixou abaixo da meta
price_drop_counter = Counter('price_drops_total', 'Total de vezes que o preço baixou abaixo da meta')
