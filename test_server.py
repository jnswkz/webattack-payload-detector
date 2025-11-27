import httpx

# Normal request
normal = {
    'Method': 'GET', 
    'host': 'localhost:8080', 
    'cookie': 'JSESSIONID=1F767F17239C9B670A39E9B10C3825F4', 
    'connection': 'close', 
    'lenght': None, 
    'content': None, 
    'URL': 'http://localhost:8080/tienda1/index.jsp HTTP/1.1'
}
r1 = httpx.post('http://localhost:8000/predict/raw', json=normal)
print('Normal request:', r1.json())

# Attack request (SQL injection in URL)
attack = {
    'Method': 'GET', 
    'host': 'localhost:8080', 
    'cookie': 'JSESSIONID=B92A8B48B9008CD29F622A994E0F650D',
    'connection': 'close', 
    'lenght': None, 
    'content': None,
    'URL': "http://localhost:8080/tienda1/publico/anadir.jsp?id=2&nombre=Jam%F3n+Ib%E9rico&precio=85&cantidad=%27%3B+DROP+TABLE+usuarios%3B+SELECT+*+FROM+datos+WHERE+nombre+LIKE+%27%25&B1=A%F1adir+al+carrito HTTP/1.1"
}
r2 = httpx.post('http://localhost:8000/predict/raw', json=attack)
print('Attack request:', r2.json())
