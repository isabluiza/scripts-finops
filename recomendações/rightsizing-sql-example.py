#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Recommender referencee:
# https://cloud.google.com/recommender/docs/recommenders

from ast import Try
from subprocess import check_output
import shlex
import json
import csv
from datetime import datetime

parent = [
    # ID das folders GCP
    "111111111",
    "222222222",
    "333333333"
]
# Zonas utilizadas pela empresa
zones = [
    "us-east1",
    "southamerica-east1"
]
# Array utilizado nas etapas seguintes, não precisa ser preenchido
values = []

print("Starting gcp recommend scraping...")
for p in parent:
    parent_id = p
    project_list_command = f'gcloud projects list \
                --filter=parent.id={parent_id} \
                --sort-by=projectId \
                --format=json \
                --http-timeout=60'
    project_list_output = json.loads(check_output(shlex.split(project_list_command)))
    for project in project_list_output:
        project_id = project['projectId']
        sql_list_command = f'gcloud sql instances list \
                            --project={project_id} \
                            --format=json \
                            --http-timeout=60'
        sql_list_output = json.loads(check_output(shlex.split(sql_list_command)))
        for z in zones:
            zone = z
            if zone == None:
                print("Skipping None zone")
            else:
                recommend_list_command = f'gcloud recommender recommendations list \
                                        --recommender=google.cloudsql.instance.OverprovisionedRecommender \
                                        --project={project_id} \
                                        --location={zone} \
                                        --format=json'
                recommend_list_output = json.loads(check_output(shlex.split(recommend_list_command)))
                print("...")
                for i in recommend_list_output:
                    name = i["content"]["overview"]["instanceName"]
                    current = i["content"]["overview"]["currentMachineType"]
                    recommend = i["content"]["overview"]["recommendedMachineType"]
                    if 'primaryImpact' in i:
                        ecconomy = i["primaryImpact"]["costProjection"]["cost"]["units"]
                        ecconomy_n = i["primaryImpact"]["costProjection"]["cost"]["nanos"]
                    else:
                        ecconomy = 0
                        ecconomy_n = 0
                    values.append([project_id, name, current, recommend, zone, ecconomy, ecconomy_n])
fields = ['PROJECT', 'NAME', 'MACHINE_TYPE', 'RECOMMENDED', 'ZONE', 'ECCONOMY', 'ECCONOMY_CENTS', 'TOTAL']
filename = "gce-recommend-sql-" + datetime.now().strftime("%d%m%y-%H%m%S") + ".csv"
with open("/caminho/para/pasta/" + filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    csvwriter.writerow(fields)
    csvwriter.writerows(values)
print("Recommend scraping... DONE, check: " + filename)