input_path = "../data/structures_end_ac.txt"
cities_output_path = "../data/cities.txt"
stronghold_output_path = "../data/strongholds.txt"

import csv
import os

def extract_structure_data(input_path):
    cities = []
    strongholds = []
    with open(input_path, 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            if len(row) > 1 and (row[1] == 'ancient_city'):
                cities.append((row[2], row[3]))
            if len(row) > 1 and (row[1] == 'stronghold'):
                strongholds.append((row[2], row[3]))

    return cities, strongholds

def write_to_file(data, output_path):
    with open(output_path, 'w') as file:
        for item in data:
            file.write(f"{item[0]} 100 {item[1]}\n")

cities, strongholds = extract_structure_data(input_path)
write_to_file(cities, cities_output_path)
write_to_file(strongholds, stronghold_output_path)