# -*- coding: utf-8 -*-
"""
Created on Tue May 26 13:09:30 2015

@author: benj29
"""

import json
import os
import csv
import random
from nltk.metrics.distance import jaccard_distance
from pprint import pprint

CSV_FILE = "linkedin_connections20150525.csv"
OUT_FILE = "d3-data.json"

#tweak this distance threshold and try different distance calculations
#during experimentation
DISTANCE_THRESHOLD = 0.75
DISTANCE = jaccard_distance
#adjust sample size as needed to reduce the runtime of the
#nested loop that invokes the DISTANCE function
SAMPLE_SIZE = 90

def cluster_contacts_by_title(csv_file):
    #Normalizing common Job Titles
    ##it reads in csv records and makes a mild attempt at normalizing them
    #by splitting apart combined titles that use the forward slash and
    #replacing known abbreviations
    transforms = [('Sr.','Senior'),('Sr','Senior'),('Jr.','Junior'),
              ('Jr','Junior'),('CEO','Chief Executive Officer'),
              ('COO','Chief Operating Officer'),
              ('CTO','Chief Technology Officer'),
              ('CFO','Chief Finance Officer'),('VP','Vice President'),
              ('Operations Manager','Manager')]

    separators = ['/','and','&','-']
    csvReader = csv.DictReader(open(CSV_FILE),delimiter=',',quotechar='"')
    contacts = [row for row in csvReader]

    #normalize and/or replace known abbreviations
    #and build up list of common titles
    all_titles = []
    for i, _ in enumerate(contacts):
        if contacts[i]['Job Title'] == '':
            contacts[i]['Job Titles'] = ['']
            continue
        titles = [contacts[i]['Job Title']]
        #this tight loop is where most of the real action happens;
        #it's where each title is compared to each other title
        for title in titles:
            for separator in separators:
                if title.find(separator) >= 0:
                    print title
                    titles.remove(title)
                    titles.extend([title.strip() for title in \
                    title.split(separator) if title.strip() != ''])
        for transform in transforms:
            titles = [title.replace(*transform) for title in titles]
        contacts[i]['Job Titles'] = titles
        all_titles.extend(titles)

    all_titles = list(set(all_titles))
    clusters = {}
    for title1 in all_titles:
        clusters[title1] = []
        for sample in xrange(SAMPLE_SIZE):
            title2 = all_titles[random.randint(0,len(all_titles)-1)]
            if title2 in clusters[title1] or clusters.has_key(title2) \
                and title1 in clusters[title2]:
                    continue
            distance = DISTANCE(set(title1.split()),set(title2.split()))
            #if the distance between any two titles as determined by a
            #similarity heuristic is "close enough",we greedily
            #group them together
            if distance < DISTANCE_THRESHOLD:
                clusters[title1].append(title2)
    #flatten out clusters
    clusters = [clusters[title] for title in clusters \
                if len(clusters[title]) > 1]
    #round up contacts who are in these clusters and group them together
    clustered_contacts = {}
    for cluster in clusters:
        clustered_contacts[tuple(cluster)] = []
        for contact in contacts:
            for title in contact['Job Titles']:
                if title in cluster:
                    clustered_contacts[tuple(cluster)].append('%s %s'
                    % (contact['First Name'],contact['Last Name']))
    return clustered_contacts

#clustered_contacts = cluster_contacts_by_title(CSV_FILE)
#print clustered_contacts


for titles in clustered_contacts:
    common_titles_heading = 'Common Titles: ' + ', '.join(titles)
    print common_titles_heading
    descriptive_terms = set(titles[0].split())
    for title in titles:
        descriptive_terms.intersection_update(set(title.split()))
    descriptive_terms_heading = 'Descriptive Terms: ' \
        + ', '.join(descriptive_terms)
    print descriptive_terms_heading
    print '-' * max(len(descriptive_terms_heading), \
        len(common_titles_heading))
    print '\n'.join(clustered_contacts[titles])
    print

def write_d3_json_output(clustered_contacts):
    json_output = {'name': 'My Linkedin','children':[]}
    
    for titles in clustered_contacts:
        descriptive_terms = set(titles[0].split())
        
        for title in titles:
            descriptive_terms.intersection_update(set(title.split()))
        json_output['children'].append({'name' : ',' \
            .join(descriptive_terms)[:30],'children' : [{'name': \
            c.decode('utf-8','replace')} for c in clustered_contacts \
            [titles]]})
        f = open(OUT_FILE,'w')
        f.write(json.dumps(json_output,indent=1))
        f.close()
#import output to json file        
write_d3_json_output(clustered_contacts)

#load json file
with open(OUT_FILE) as data_file:
    data = json.load(data_file)
pprint(data)

#convert back to json
json.dumps(data)

