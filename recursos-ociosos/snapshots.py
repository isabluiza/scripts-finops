from subprocess import check_output
import shlex
import json     
import datetime 
import logging
import csv

#Iniciar as variáveis que serão utilizadas
parent = ["1",   #ID dos parents
"2",             
"3"]     

# Arrays utilizados nas etapas seguintes, não precisam ser preenchidos
value = []
diasDelete = []
snapDelete = []
snapResult = []

#Iniciar a função de dia atual em uma variável
dataAtual = datetime.datetime.now()
diasValidos = dataAtual - datetime.timedelta(days=7)
regraData = diasValidos.strftime("%Y-%m-%dT%H:%M:%S.000-07:00")

#Iniciar nome e formato do arquivo log
arquivoLOGNome = "deleted-snapshots-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".log"
log_format = "{'level': '%(levelname)s', 'timestamp': '%(asctime)s', 'status': '%(message)s}"

#Colocar a data atual no nome do arquivo csv que será gerado
arquivoCSVNome = dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss")+".csv"

#Listar todos os projetos
for p in parent:

    parentId = p
    comando1 = f'gcloud projects list --filter=parent.id={parentId} --format=json'
    projetos = json.loads(check_output(shlex.split(comando1),shell=True))

    for p in projetos:

#Armazenar o ID de cada projeto
        projectId = p["projectId"]

#Listar os snapshots de cada projeto em formato JSON
        comando2 = f"gcloud compute snapshots list --project={projectId} --format=json"
        snapshots = json.loads(check_output(shlex.split(comando2),shell=True))

#Armazenar nome, data de criação, zona e tamanho em bytes de cada snap listado
        for s in snapshots:

            name = s["name"]
            creationTimestamp = s["creationTimestamp"]

            try:
                storageLocations = s["storageLocations"]
            except (KeyError):
                storageLocations = 0

            try:
                storageBytes = s["storageBytes"]
            except (KeyError):
                storageBytes = 0

#Concatenar informações em única variável value
            value.append([parentId, projectId, name, creationTimestamp, storageLocations, storageBytes])

#Validar regra de data
for v in value:

    if v[3] <= regraData:
        snapDelete = v

#Snapshots validados para exclusão são concatenados
        snapResult.append(snapDelete)

#Passar todos os snapshots a serem excluídos para um arquivo .csv
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'LOCATION', 'STORAGE_BYTES']       #Nomes das colunas
filename = "recommend-snapshots-" + arquivoCSVNome         #Nome do arquivo
with open("/caminho/da/pasta/" + filename, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(snapResult)

#Ação de exclusão e registro em log
for s in snapResult:
    
    data = str(s)[1:-1]
    name = s["name"]
    projectId = s["projectId"]

    try:
        comando3 = f"gcloud compute snapshots delete {name} --project={projectId} --quiet"
        delete_snaps = check_output(shlex.split(comando3),shell=True)

        logging.basicConfig(filename = arquivoLOGNome,
                    filemode = "w",
                    format = log_format, 
                    level = logging.INFO)
        logger = logging.getLogger()
        logger.info("Deleted', " + data)

    except:
        logging.basicConfig(filename = arquivoLOGNome,
                        filemode = "w",
                        format = log_format, 
                        level = logging.ERROR)
        logger = logging.getLogger()
        logger.error("Failed', " + data)  

#Mensagem final de realizado com sucesso!
print("Log and CSV scraping... DONE, check: " + arquivoLOGNome + "and " + arquivoCSVNome)