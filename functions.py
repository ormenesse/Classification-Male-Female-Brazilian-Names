import datetime
import pandas as pd
import numpy as np
import pymongo

def arruma_cnpj(x):
    x = str(x)
    if x != 'nan':
        if len(str(x).split(' ')) >= 2:
            return str(x).split(" ")[0]+"/"+str(x).split(" ")[1]+"-"+str(x).split(" ")[2] 
        else:
            return str(x)[:2]+'.'+str(x)[2:5]+'.'+str(x)[5:8]+"/"+str(x)[8:12]+"-"+str(x)[12:]
    else:
        return np.nan

def return_forward_months(anomes,qtd,actualmonth=True):
    if actualmonth == True:
        meses = [anomes]
    else:
        meses = []
    mes = anomes
    for i in range(0,qtd):
        if (mes // 10**0 % 100) == 12:
            mes = mes - 11
            mes = mes + 100
        else:
            mes = mes + 1
        meses.append(int(mes))
    return meses

def return_one_year_months(anomes,qtd):
    meses = [anomes]
    mes = anomes
    for i in range(0,qtd):
        if (mes // 10**0 % 100) == 1:
            mes = mes + 11
            mes = mes - 100
        else:
            mes = mes - 1
        meses.append(int(mes))
    return meses

def check_install_delay(x):
    
    if x['Install_dueDate'] <= pd.to_datetime('now'):
        if pd.isnull(x['Invoice_paidAt']):
            return (pd.to_datetime('now')-x['Install_dueDate']).days
        else:
            return (x['Invoice_paidAt']-x['Install_dueDate']).days
    else:
        return pd.NaT

def return_proscore_aggr(numbers):
    query_aggr = \
    [
        {
          '$match' : {
              'businessNumber': { '$in' : numbers}
          }  
        },
        {
            '$project' : {
                'date' : '$_created_at',
                'summary' : True,
                'businessNumber' : True,
                'cpf' : True,
                'cnpj' : True
                
            }
        },
        {
            '$unwind' : {
                'path': '$summary'
            }
        },
        {
          '$match' : {
              'summary.numero_plugin': "100"
          }  
        }
        
    ]
    return query_aggr

def return_scr_aggr(numbers):
    query_aggr = \
    [
        {
          '$match' : {
              'businessNumber': { '$in' : numbers}
          }  
        },
        {
            '$project' : {
                'date' : True,
                'summary' : True,
                'businessNumber' : True,
                'cpf' : True,
                'cnpj' : True
                
            }
        }
    ]
    return query_aggr

def gera_tabelas_bad(df):
    
    timediff = datetime.datetime.now() - datetime.timedelta(weeks=1)
    np_anomes = pd.DataFrame([])
    
    bads = []

    for data_desembolso in df['disbursementDate_anomes'][( df['disbursementDate'] <= timediff)].unique():
        
        for contrato in df['_id'][(df['disbursementDate_anomes'] == data_desembolso) & ( df['disbursementDate'] <= timediff)].unique():
                
            copyd = df[['_id','businessNumber','ccbNumber','portfolioName','statusName','Install_anomes','Install_amount','number_installment','Install_delay']][(df['_id'] == contrato) & (df['Install_dueDate'] <= timediff)].sort_values(by='number_installment').copy()
                
            if copyd.shape[0] != 0:
                ccb_bads = {}
                #print( contrato, copyd['ccbNumber'].unique(),copyd['businessNumber'].unique())
                ccb_bads['anomes'] = data_desembolso
                ccb_bads['businessNumber'] = copyd['businessNumber'].unique()[0]
                ccb_bads['_id'] = copyd['_id'].unique()[0]
                ccb_bads['portfolioName'] = copyd['portfolioName'].unique()[0]
                ccb_bads['statusName'] = copyd['statusName'].unique()[0]
                ccb_bads['bad_30'] = 0
                ccb_bads['bad_60'] = 0
                ccb_bads['bad_90'] = 0
                ccb_bads['bad_180'] = 0

                # Ganhos e Retornos
                for delay_time in [30,60,90,180]:

                    for j in sorted(list(copyd['number_installment'].unique())):

                        # Perdas na Parcela Mensal
                        if copyd['Install_delay'][copyd['number_installment'] == j].values[0] >= delay_time and ccb_bads['bad_'+str(delay_time)] != 1:

                            ccb_bads['bad_'+str(delay_time)] = 1

                        if ccb_bads['bad_'+str(delay_time)] == 1:

                            break

                bads.append(ccb_bads)
            
    return bads
    
def gera_dfmodels(db_parcelas, client):

    bads = pd.DataFrame(gera_tabelas_bad(db_parcelas[db_parcelas['statusName'].isin(['Ajuizado','Ativo','Finalizado', 'Renegociação', 'Renegociado'])]))
    
    bads['anomes'] = bads['anomes'].astype('int')
    
    businessNumber = [int(i) for i in list(bads['businessNumber'].unique())]

    aggre = [
    {
        '$project' : { 
            '_p_business' : { '$substr': [ '$_p_business', 9, -1 ] }, 
            'anomes' : True, 'paymentCapacity' : True, 
            'riskGroup' : True,
            'modelVersion' : True,
            'score' : True 
        }
    },
    {
        '$lookup': {
            'from': 'Business', 
            'let': {
                'business': '$_p_business'
            }, 
            'pipeline': [
                {
                    '$project': {
                        'number' : True
                    }
                }, {
                    '$match': {
                        '$expr': {
                            '$eq': [
                                '$_id', '$$business'
                            ]
                        }
                    }
                }
            ], 
            'as': 'business'
        }
    },
    {
        '$project' : { 
            'businessNumber' : { '$arrayElemAt': [ "$business.number", 0 ] }, 
            'anomes' : True, 'paymentCapacity' : True, 
            'riskGroup' : True, 
            'score' : True,
            'modelVersion' : True
        }
    },
    {
        '$match' : {
            'businessNumber' : { '$in' :  businessNumber },
            'modelVersion' : "preLoanScore_v1.0"
        }
    }
    ]
    
    search = client['gyramais']['Score'].aggregate(aggre)
    search = list(search)
    
    df_scores = pd.DataFrame(search)
    
    pd_merged = pd.merge(bads,df_scores,how='left',on=['businessNumber', 'anomes'])
    
    return pd_merged

def get_main_query(time_diff,time_diff2,statuses):

    query = [
        {
            '$match' : { 'date' : {'$lte' : time_diff } }  
        },
        {
            '$match' : { 'date' : {'$gte' : time_diff2 } }  
        },
        {
        '$match': {
            'statusName': {
                '$in': statuses
            }
        }
        }, {
        '$lookup': {
            'from': 'Installment', 
            'let': {
                'loan': '$_id'
            }, 
            'pipeline': [
                {
                    '$project': {
                        'loanPointer': {
                            '$substr': [
                                '$_p_loan', 5, -1
                            ]
                        }, 
                        'dueDate': True, 
                        'amount': True, 
                        'interestAmount': True, 
                        'paidAmount': True, 
                        'totalAmount': True, 
                        'number_installment': '$number', 
                        'installStatus': '$statusName',
                        'loanPortfolioName' : '$loanPortfolioName',
                        'loanStatusName' : True
                    }
                }, {
                    '$match': {
                        '$expr': {
                            '$eq': [
                                '$loanPointer', '$$loan'
                            ]
                        }
                    }
                }
            ], 
            'as': 'Installments'
        }
    }, {
        '$unwind': {
            'path': '$Installments', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'Invoice', 
            'let': {
                'port': '$Installments._id'
            }, 
            'pipeline': [
                {
                    '$project': {
                        'dueDate': True, 
                        'paidAt': True, 
                        'remainingAmount': True, 
                        'amount': True, 
                        'installmentPaid': True, 
                        '_p_installment_id': {
                            '$substr': [
                                '$_p_installment', 12, -1
                            ]
                        }
                    }
                }, {
                    '$match': {
                        '$expr': {
                            '$eq': [
                                '$_p_installment_id', '$$port'
                            ]
                        }
                    }
                }
            ], 
            'as': 'Invoice'
        }
    },{
        '$addFields' : {
              "invoice_idid" : { '$indexOfArray' : ["$Invoice._id","$_p_lastPaidInvoice"]}
        }
    }, { '$addFields': {
          'Invoice': {
            '$arrayElemAt': [
                '$Invoice', "$invoice_idid"
                ]
            }
        }
    }, {
        '$project': {
            'date': True, 
            'disbursementDate': True, 
            'paidAmount': True, 
            'interestRate': True, 
            'installmentAmount': True, 
            'amount': True, 
            'finalAmount': True, 
            'installmentsCount': True, 
            'totalAmount': True, 
            'finalInstallmentsCount': True, 
            'ccbNumber': True, 
            'iofAmount': True, 
            'cet': True, 
            'annualCET': True, 
            '_p_parent': True, 
            'installID' : '$Installments._id',
            'loanPortfolioName' : '$Installments.loanPortfolioName',
            'Install_dueDate': '$Installments.dueDate', 
            'Install_amount': '$Installments.amount', 
            'Install_interest': '$Installments.interestAmount', 
            'Install_total': '$Installments.totalAmount', 
            'InstallStatus': '$Installments.installStatus', 
            'number_installment': '$Installments.number_installment', 
            'Invoice_dueDate': '$Invoice.dueDate', 
            'Invoice_paidAt': '$Invoice.paidAt', 
            'Invoice_totalAmount': '$Invoice.amount', 
            'Invoice_paid': '$Invoice.installmentPaid', 
            'businessNumber': True, 
            'portfolioName': True, 
            'statusName': True,
            'loanStatusName' : '$Installments.loanStatusName'
        }
    }
    ]
    return query