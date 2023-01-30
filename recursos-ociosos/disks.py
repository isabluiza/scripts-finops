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
diskDeleteLog = []
diskDeleteCsv = []

#Iniciar a função de dia atual em uma variável
dataAtual = datetime.datetime.now()
diasValidos = dataAtual - datetime.timedelta(days=7)
regraData = diasValidos.strftime("%Y-%m-%dT%H:%M:%S.000-07:00")

#Iniciar nome e formato do arquivo log
arquivoNomeLog = "deleted-disks-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".log"

#Colocar a data atual no nome do arquivo csv que será gerado
arquivoNomeCsv = "deleted-disks-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".csv"

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

            try:
                users = d["users"]
            except (KeyError):
                users = 0

#Validar regra de data
            if creationTimestamp <= regraData:

#Discos validados para exclusão são concatenados
                diskDeleteCsv.append([parentId, projectId, name, creationTimestamp, zone, sizeGb, users])

                diskDeleteLog.append({"parentId": parentId, "projectId": projectId, "name": name, "creationTimestamp": creationTimestamp, "location": zone, "sizeGb": sizeGb, "users": users})

#Passar todos os discos a serem excluídos para um arquivo .csv
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'LOCATION', 'SIZE_GB', 'USERS']     #Nomes das colunas
with open("/caminho/da/pasta/" + arquivoNomeCsv, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(diskDeleteCsv)

#Ação de exclusão e registro em log
for d in diskDeleteLog:
    
    data = str(d)[1:-1]
    name = d["name"]
    projectId = d["projectId"]
    zone = d["zone"]

    try:
        comando3 = f"gcloud compute disks delete {name} --zone={zone} --project={projectId} --quiet"
        delete_disks = check_output(shlex.split(comando3),shell=True)

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