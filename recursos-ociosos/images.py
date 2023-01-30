from subprocess import check_output
import shlex    #importando bibliotecas
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
imgDeleteLog = []
imgDeleteCsv = []

#Iniciar a função de dia atual em uma variável
dataAtual = datetime.datetime.now()
diasValidos = dataAtual - datetime.timedelta(days=7)
regraData = diasValidos.strftime("%Y-%m-%dT%H:%M:%S.000-07:00")

#Iniciar nome e formato do arquivo log
arquivoNomeLog = "deleted-images-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".log"

#Iniciar nome do arquivo
arquivoNomeCsv = "deleted-images-" + dataAtual.strftime("%Y-%m-%dT%Hh%Mmin%Ss") + ".csv"

#Listar todos os projetos
for p in parent:

    parentId = p
    comando1 = f'gcloud projects list --filter=parent.id={parentId} --format=json'
    projetos = json.loads(check_output(shlex.split(comando1),shell=True))

    for p in projetos:

#Armazenar o ID de cada projeto
        projectId = p["projectId"]

#Listar as imagens de cada projeto em formato JSON e imagens não públicas
        comando2 = f"gcloud compute images list --project={projectId} --format=json --no-standard-images"
        images = json.loads(check_output(shlex.split(comando2),shell=True))

#Armazenar nome, data de criação, zona e tamanho em Bytes de cada imagem listada
        for i in images:

            name = i["name"]
            creationTimestamp = i["creationTimestamp"]

            try:
                location = i["storageLocations"]
            except (KeyError):
                location = 0

            try:
                archiveSize = int(i["archiveSizeBytes"])
            except (KeyError):
                archiveSize = 0

            sizeGb = float("{:.2f}".format(archiveSize/(1024 ** 3)))

#Validar regra de data
            if creationTimestamp <= regraData:

#Imagens validadas para exclusão são concatenadas
                imgDeleteCsv.append([parentId, projectId, name, creationTimestamp, location, sizeGb])

                imgDeleteLog.append({"parentId": parentId, "projectId": projectId, "name": name, "creationTimestamp": creationTimestamp, "location": location, "sizeGb": sizeGb})

#Passar todas as imagens a serem excluídas para um arquivo .csv
fields = ['PARENT', 'PROJECT', 'NAME', 'CREATION_TIMESTAMP', 'LOCATION', 'SIZE_GB']        #Nomes das colunas
with open("/caminho/da/pasta/" + arquivoNomeCsv, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';') 
    csvwriter.writerow(fields)
    csvwriter.writerows(imgDeleteCsv)

#Ação de exclusão e registro em log
for i in imgDeleteLog:
    
    data = str(i)[1:-1]
    name = i["name"]
    projectId = i["projectId"]

    try:
        comando3 = f"gcloud compute images delete {name} --project={projectId} --quiet"
        delete_images = check_output(shlex.split(comando3),shell=True)

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