# Modelo de Liderança Feminina

Modelo que classifica o sexo do indivíduo com base no primeiro nome.

Para construir o modelo utilizamos uma base do IBGE que já tem classificação de 100.000 nomes (https://brasil.io/dataset/genero-nomes/nomes/).

Para o funcionamento do projeto, deve-se instalar as seguintes bibliotecas no Python3:

```
matplotlib
fuzzywuzzy
numpy
flask
flask-cors
```

Após a instalação das bibliotecas, o funcionamento do projeto é simples. As requisições são processadas via [Flask](https://github.com/pallets/flask) e este é encarregado de devolver o modelo em formato JSONO modelo de lideranças femininas fornece as saídas:

femLeadership -> que tem valores 'Yes' ou 'No', e significa se dentre os sócios existe alguma mulher.

percFeminine -> devolve a porcentagem de mulheres dentre os sócios.

As entradas são:

legName -> nome da empresa ou dono (legalName no Mongo)

legRep -> nome dos sócios (legalRepresentatives no Mongo). Caso não haja não precisa ser fornecido.

O link para requisição é:

https://dataservices.gyramais.com.br/lidfem?legName=< Nome da Empresa ou dono >&legRep=<Nome dos sócios>