from subprocess import check_output
import shlex    
import json     
import datetime
import logging 
import csv

#Iniciar as variáveis que serão utilizadas
parent = ["1",   #ID de dev
"2",             #ID de homolog
"3"]             #ID de prod

# Arrays utilizados nas etapas seguintes, não precisam ser preenchidos
value = []
diasDelete = []
ipDeleteLog = []
ipDeleteCsv = []

#Iniciar a função de dia atual em uma variável
dataAtual = datetime.datetime.now()
diasValidos = dataAtual - datetime.timedelta(days=7)
regraData = diasValidos.strftime("%Y-%m-%dT%H:%M:%S.000-07:00")

#Iniciar nome e formato do arquivo log
arquivoNomeLog = "deleted-ipaddresses-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".log"

#Colocar a data atual no nome do arquivo csv que será gerado
arquivoNomeCsv = "deleted-ipaddresses-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".csv"

#Listar todos os projetos de dev, homolog e prod
for p in parent:

    parentId = p
    comando1 = f'gcloud projects list --filter=parent.id={parentId} --format=json'
    projetos = json.loads(check_output(shlex.split(comando1),shell=True))

    for p in projetos:

#Armazenar o ID de cada projeto
        projectId = p["projectId"]

#Listar os endereços de ip de cada projeto em formato JSON
        comando2 = f'gcloud compute addresses list --project={projectId} --format=json'
        ipaddresses = json.loads(check_output(shlex.split(comando2),shell=True))

#Armazenar nome, data de criação, zona e usuário de cada endereço de IP listado
        for i in ipaddresses:

            name = i["name"]
            creationTimestamp = i["creationTimestamp"]

            try:
                region = i["region"].rsplit('/', 1)[-1]
            except (KeyError):
                region = 0

            try:
                users = i["users"]
            except (KeyError):
                users = 0

#Validar regra de data e se o campo "user" está vazio
            if (creationTimestamp <= regraData) and (users == 0):

#Endereços de IP validados para exclusão são concatenados
                ipDeleteCsv.append([parentId, projectId, name, creationTimestamp, region, users])

                ipDeleteLog.append({"parentId": parentId, "projectId": projectId, "name": name, "creationTimestamp": creationTimestamp, "location": region, "sizeGb": None, "users": users})

#Passar todos os endereços de ip a serem excluídos para um arquivo .csv
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'LOCATION', 'USER']        #Nomes das colunas
with open("/caminho/da/pasta/" + arquivoNomeCsv, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(ipDeleteCsv)


#Ação de exclusão e registro em log
for i in ipDeleteLog:
    
    data = str(i)[1:-1]
    name = i["name"]
    projectId = i["projectId"]
    region = i["region"]

    try:
        comando3 = f"gcloud compute addresses delete {name} --region={region} --project={projectId} --quiet"
        delete_ip = check_output(shlex.split(comando3),shell=True)

        logging.basicConfig(filename = arquivoNomeLog,
                            filemode = "w",
                            format = "{'level': '%(levelname)s', 'timestamp': '%(asctime)s', 'status': '%(message)s}",
                            datefmt='%Y-%m-%dT%Hh%Mmin%Ss',  
                            level = logging.INFO)
        logger = logging.getLogger()
        logger.info("Deleted', " + data)

    except:
        logging.basicConfig(filename = arquivoNomeLog,
                            filemode = "w",
                            format = "{'level': '%(levelname)s', 'timestamp': '%(asctime)s', 'status': '%(message)s}",
                            datefmt='%Y-%m-%dT%Hh%Mmin%Ss',
                            level = logging.ERROR)
        logger = logging.getLogger()
        logger.error("Failed', " + data)  

#Mensagem final de realizado com sucesso!
print("Log and CSV scraping... DONE, check: " + arquivoNomeLog + "and " + arquivoNomeCsv)