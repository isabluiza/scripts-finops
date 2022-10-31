from subprocess import check_output
import shlex    
import json     
import datetime
import logging 
import csv

#Iniciar as variáveis que serão utilizadas
parent = ["744421660312",   #ID de dev
"893525270595",             #ID de homolog
"105926244922"]             #ID de prod
value = []
diasDelete = []
ipDelete = []
ipResult = []

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

#Listar os discos de cada projeto em formato JSON
        comando2 = f'gcloud compute addresses list --project={projectId} --format=json'
        ipaddress = json.loads(check_output(shlex.split(comando2),shell=True))

#Armazenar nome, data de criação, zona e usuário de cada endereço de IP listado
        for i in ipaddress:

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

#Concatenar informações em única variável value
            value.append([parentId, projectId, name, creationTimestamp, region, users])

#Validar regra de data e se o campo "user" está vazio
for v in value:

    if (v[3] <= regraData) and (v[5] == 0):
        ipDelete = v

#Endereços de IP validados para exclusão são concatenados
        ipResult.append(ipDelete)

for i in ipResult:
    
    data = str(i)[1:-1]
    name = i["name"]
    projectId = i["projectId"]

    try:
        comando3 = f"gcloud compute addresses delete {name} --project={projectId} --quiet"
        delete_ip = check_output(shlex.split(comando3),shell=True)

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
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'REGION', 'USER']        #Nomes das colunas
filename = "recommend-ipaddress-" + arquivoCSVNome         #Nome do arquivo
with open("caminho/da/pasta/" + filename, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(ipResult)

#Mensagem final de realizado com sucesso!
print("Recommend scraping... DONE, check: " + filename)