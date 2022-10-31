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
value = []
diasDelete = []
diskDelete = []
diskResult = []

#Iniciar a função de dia atual em uma variável
dataAtual = datetime.datetime.now()
diasValidos = dataAtual - datetime.timedelta(days=7)
regraData = diasValidos.strftime("%Y-%m-%dT%H:%M:%S.000-07:00")

#Iniciar nome e formato do arquivo log
arquivoLOGNome = "deleted-snapshots-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".log"
log_format = "{'level': '%(levelname)s', 'timestamp': '%(asctime)s', 'status': '%(message)s}"

#Colocar a data atual no nome do arquivo csv que será gerado
arquivoCSVNome = dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss")+".csv"

#Listar todos os projetos de dev, homolog e prod
for p in parent:

    parentId = p
    comando1 = f'gcloud projects list --filter=parent.id={parentId} --format=json'
    projetos = json.loads(check_output(shlex.split(comando1),shell=True))

    for p in projetos:

#Armazenar o ID de cada projeto
        projectId = p["projectId"]

#Listar os discos de cada projeto em formato JSON e em desuso
        comando2 = f"gcloud compute disks list --project={projectId} --format=json --filter='-users:*'"
        disks = json.loads(check_output(shlex.split(comando2),shell=True))

#Armazenar nome, data de criação, zona e tamanho em GB de cada disco listado
        for d in disks:

            name = d["name"]
            creationTimestamp = d["creationTimestamp"]

            try:
                zone = d["zone"].rsplit('/', 1)[-1]
            except (KeyError):
                zone = 0

            try:
                sizeGb = d["sizeGb"]
            except (KeyError):
                sizeGb = 0

#Concatenar informações em única variável value
            value.append([parentId, projectId, name, creationTimestamp, zone, sizeGb])

#Validar regra de data
for v in value:

    if v[3] <= regraData:
        diskDelete = v

#Discos validados para exclusão são concatenados
        diskResult.append(diskDelete)

for d in diskResult:
    
    data = str(d)[1:-1]
    name = d["name"]
    projectId = d["projectId"]

    try:
        comando3 = f"gcloud compute disks delete {name} --project={projectId} --quiet"
        delete_disks = check_output(shlex.split(comando3),shell=True)

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

#Passar todos os discos a serem excluídos para um arquivo .csv
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'ZONE', 'SIZE_GB']     #Nomes das colunas
filename = "deleted-disks-" + arquivoCSVNome     #Nome do arquivo
with open("caminho/da/pasta/" + filename, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(diskResult)

#Mensagem final de realizado com sucesso!
print("Recommend scraping... DONE, check: " + filename)