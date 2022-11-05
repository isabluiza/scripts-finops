#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Recommender referencee:
# https://cloud.google.com/recommender/docs/recommenders

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
# Arrays utilizados nas etapas seguintes, não precisam ser preenchidos
zones = []
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
        vm_list_command = f'gcloud compute instances list \
                            --project={project_id} \
                            --format=json \
                            --http-timeout=60'
        vm_list_output = json.loads(check_output(shlex.split(vm_list_command)))
        for vm in vm_list_output:
            vm_zone = vm["zone"]
            zone_only = vm_zone.rsplit('/', 1)[-1]
            zones.append(zone_only)
        zones_end = list(dict.fromkeys(zones))
        for z in zones_end:
            zone = z
            recommend_list_command = f'gcloud recommender recommendations list \
                                    --recommender=google.compute.instance.IdleResourceRecommender \
                                    --project={project_id} \
                                    --location={zone} \
                                    --format="json(content.overview.resourceName, recommenderSubtype, primaryImpact.costProjection.cost.units, primaryImpact.costProjection.cost.nanos, content.overview.location)"'
            recommend_list_output = json.loads(check_output(shlex.split(recommend_list_command)))
            print("...")
            for i in recommend_list_output:
                name = i["content"]["overview"]["resourceName"]
                # current = i["content"]["overview"]["currentMachineType"]["name"]
                recommend = i["recommenderSubtype"]
                zone = i["content"]["overview"]["location"]
                if 'primaryImpact' in i:
                    ecconomy = i["primaryImpact"]["costProjection"]["cost"]["units"]
                    ecconomy_n = i["primaryImpact"]["costProjection"]["cost"]["nanos"]
                else:
                    ecconomy = 0
                    ecconomy_n = 0
                values.append([project_id, name, recommend, zone, ecconomy, ecconomy_n])
fields = ['PROJECT', 'NAME', 'RECOMMENDED_ACTION', 'ZONE', 'ECCONOMY', 'ECCONOMY_CENTS']
filename = "gce-recommend-idle-" + datetime.now().strftime("%d%m%y-%H%m%S") + ".csv"
with open("/caminho/para/pasta/" + filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    csvwriter.writerow(fields)
    csvwriter.writerows(values)
print("Recommend scraping... DONE, check: " + filename)