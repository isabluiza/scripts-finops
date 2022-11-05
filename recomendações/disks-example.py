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
        disk_list_command = f'gcloud compute instances list \
                            --project={project_id} \
                            --format=json \
                            --http-timeout=60'
        disk_list_output = json.loads(check_output(shlex.split(disk_list_command)))
        for disk in disk_list_output:
            vm_zone = disk["zone"]
            zone_only = vm_zone.rsplit('/', 1)[-1]
            zones.append(zone_only)
        zones_end = list(dict.fromkeys(zones))
        for z in zones_end:
            zone = z
            recommend_list_command = f'gcloud recommender recommendations list \
                                    --recommender=google.compute.disk.IdleResourceRecommender \
                                    --project={project_id} \
                                    --location={zone} \
                                    --format="json(content.overview.resourceName, content.overview.recommendedAction, primaryImpact.costProjection.cost.units, primaryImpact.costProjection.cost.nanos, content.overview.location)"'
            recommend_list_output = json.loads(check_output(shlex.split(recommend_list_command)))
            print("...")
            for i in recommend_list_output:
                name = i["content"]["overview"]["resourceName"]
                recommend = i["content"]["overview"]["recommendedAction"]
                zone = i["content"]["overview"]["location"]
                try:
                    ecconomy = i["primaryImpact"]["costProjection"]["cost"]["units"]
                except (KeyError):
                    ecconomy = 0
                try:
                    ecconomy_n = i["primaryImpact"]["costProjection"]["cost"]["nanos"]
                except (KeyError):    
                    ecconomy_n = 0
                values.append([parent_id, project_id, name, recommend, zone, ecconomy, ecconomy_n])
fields = ['PARENT', 'PROJECT', 'NAME', 'RECOMMENDED', 'ZONE', 'ECCONOMY', 'ECCONOMY_CENTS', 'TOTAL']
filename = "gce-recommend-disks-" + datetime.now().strftime("%d%m%y-%H%m%S") + ".csv"
with open("/caminho/para/pasta/" + filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    csvwriter.writerow(fields)
    csvwriter.writerows(values)
print("Recommend scraping... DONE, check: " + filename)