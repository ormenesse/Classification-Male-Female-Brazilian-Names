from fuzzywuzzy import fuzz
import pandas as pd
from unidecode import unidecode


def lid_fem(nome,ibgenomespath = 'nomes.csv'):

    # Importando base de dados com nomes classificados

    df = pd.read_csv(ibgenomespath)
    names_ibge = df['first_name'].values
    fem_names = df.loc[df['classification']=='F','first_name'].values

    u = unidecode(nome).upper()

    if u in names_ibge:
        if u in fem_names:
            return 'Yes'
        else:
            return 'No'
    else:
        h = [fuzz.ratio(u,r) for r in names_ibge]
        hm = max(h)
        n = h.index(hm)
        fuzz_name = names_ibge[n]
        if hm>=80:
            if fuzz_name in fem_names:
                return 'Yes'
            else:
                return 'No'
        else:
            indices = [i for i, x in enumerate(h) if x == hm]
            lista = [names_ibge[n] for n in indices]
            for k in lista:
                lista_nomes = df.loc[df['first_name']==k,'alternative_names'].values
                for s in lista_nomes:
                    if s==s:
                        score = [fuzz.ratio(k,l) for l in s.split('|')]
                        m = max(score)
                        ind = score.index(m)
                        new_fuzz = s.split('|')[ind]
                        if m>=80:
                            if new_fuzz in fem_names:
                                return 'Yes'
                            else:
                                return 'No'
        
def lid_class(request):

    try:
        
        legName = request.args.get('legName')

        legRep = request.args.get('legRep')
        
        if legName is None:
            legName = ''
        if legRep is None:
            legRep = ''
        
        print(legRep)

        vogais = ['A','a','E','e','I','i','O','o','U','u']

        if legRep == '':
            u = legName.split()[0]
            if len(u)>1 and '.' not in u and any(v in u for v in vogais):
                return {'femLeadership' : lid_fem(u)}
            else:
                return {'femLeadership' : 'No'}
        else:
            is_fem = []
            for y in legRep.split(','):
                u = y.split('-')[1].split()[0]
                if len(u)>1 and '.' not in u and any(v in u for v in vogais):
                    is_fem.append(lid_fem(u))
            if 'Yes' in is_fem:
                return {'femLeadership' : 'Yes', 'percFeminine': is_fem.count('Yes')/len(is_fem)}
            else:
                return {'femLeadership' : 'No', 'percFeminine': 0}
    except:

        return { 'Error' : 'Bad Request.'}