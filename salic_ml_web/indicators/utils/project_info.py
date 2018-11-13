from salic_db.utils import make_query_from_db

def fetch_raised_funds(pronac):
    query = "SELECT capt.AnoProjeto+capt.Sequencial AS Pronac, SUM(CaptacaoReal) AS ValorCaptado \
            FROM SAC.dbo.Captacao capt \
            INNER JOIN SAC.dbo.Projetos	proj ON (capt.AnoProjeto = proj.AnoProjeto AND capt.Sequencial = proj.Sequencial) \
            WHERE (capt.AnoProjeto + capt.Sequencial) = '{}' \
            GROUP BY (capt.AnoProjeto + capt.Sequencial)".format(pronac)
    
    query_data = make_query_from_db(query)

    result = []

    for line in query_data:
        result.append({
            'pronac': line[0],
            'raised_funds': line[1]
        })

    final_data = None

    if len(result) == 1:
        final_data = result[0]['raised_funds']

    return final_data  

def fetch_general_data(pronac):
    query = "SELECT projetos.AnoProjeto + projetos.Sequencial as PRONAC, \
            NomeProjeto, \
            situacao.Descricao as Situacao, \
            DtInicioExecucao, \
            DtFimExecucao \
            FROM SAC.dbo.Projetos \
            INNER JOIN SAC.dbo.Situacao situacao ON projetos.Situacao = situacao.Codigo \
            WHERE (projetos.AnoProjeto + projetos.Sequencial) = '{}'".format(pronac)
    
    query_data = make_query_from_db(query)

    result = []

    for line in query_data:
        result.append({
            'pronac': line[0],
            'name': line[1],
            'situation': line[2],
            'start_date': line[3],
            'end_date': line[4]
        })

    final_data = None

    if len(result) == 1:
        final_data = result[0]
    else:
        final_data = {
            'pronac': pronac,
            'name': '',
            'situation': '',
            'start_date': '',
            'end_date': ''
        }

    return final_data  

    

def fetch_verified_funds(pronac):
    query = "SELECT (projetos.AnoProjeto + projetos.Sequencial) AS PRONAC, \
	        SUM(comprovacao.vlComprovado) AS vlComprovacao \
            FROM SAC.dbo.tbPlanilhaAprovacao aprovacao \
            INNER JOIN SAC.dbo.Projetos projetos ON (aprovacao.IdPRONAC = projetos.IdPRONAC) \
            INNER JOIN BDCorporativo.scSAC.tbComprovantePagamentoxPlanilhaAprovacao comprovacao ON (aprovacao.idPlanilhaAprovacao = comprovacao.idPlanilhaAprovacao) \
            WHERE  DtProtocolo>='2013-01-01 00:00:00' AND \
                aprovacao.nrFonteRecurso = 109 \
                AND (sac.dbo.fnVlComprovado_Fonte_Produto_Etapa_Local_Item \
                    (aprovacao.idPronac,aprovacao.nrFonteRecurso,aprovacao.idProduto,aprovacao.idEtapa,aprovacao.idUFDespesa,aprovacao.idMunicipioDespesa, aprovacao.idPlanilhaItem)) > 0 \
                AND (projetos.AnoProjeto + projetos.Sequencial) = '{}' \
            GROUP BY (projetos.AnoProjeto + projetos.Sequencial), projetos.DtProtocolo".format(pronac)
    
    query_data = make_query_from_db(query)

    result = []

    for line in query_data:
        result.append({
            'pronac': line[0],
            'verified_funds': line[1]
        })

    final_data = None

    if len(result) == 1:
        final_data = result[0]['verified_funds']

    return final_data  
