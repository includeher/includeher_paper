# Script to extract summary statistics for a state or territory

# imports
import numpy as np
import pandas as pd
import json
import argparse

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)


parser.add_argument('-f', '--filename', help='filename', type=str, required=True)
args = parser.parse_args()


# categories in csv file
keys = [
    'Subject', # includes core subjects: Physics, Chemistry, Biology and Enviromental Science
    'Mention', # list of names or laws apearing in curriculum e.g. "Stefan-Boltzmann Law" or "Einsteins theory of special relativity"
    'Name of Scientist', # full names of scientist(s) for each mention e.g. mention of "Stefan-Boltzmann Law" = [Josef Stefan, Ludwig Boltzmann]
    'Gender', # gender of scientist(s) for each mention
    'Type of Mention', # categorisation of mention; either "concept" or "scientist"
    'Nationality', # nationality of scientist(s) for each mention (if two given, uses birthplace nationality)
    'Region' # continent/region of the scientist(s) for each mention
]

subjects = ["physics", "chemistry", "biology", "environment"]

# read data
fname = args.filename
label = fname.split(".")[0]
df = pd.read_csv(fname, encoding='latin-1')


# expand data for mentions with two entries e.g. "Stefan-Boltzmann Law"
if "Examinable" in df.keys():
    for key in ['Name of Scientist', 'Gender', 'Nationality', 'Region', 'Examinable']:
        df[key] = df[key].str.split(";")
    exdf = df.explode(["Name of Scientist","Gender", "Nationality", "Region", "Examinable"])
else:
    for key in ['Name of Scientist', 'Gender', 'Nationality', 'Region']:
        df[key] = df[key].str.split(";")    
    exdf = df.explode(["Name of Scientist","Gender", "Nationality", "Region"])


# create dictionary for output data
data = {}
data["subjects"] = {}
data["names"] = {}
data["overall"] = {}

#calculate stats
n_concept_m_tot = 0
n_concept_f_tot = 0
n_scientist_m_tot = 0
n_scientist_f_tot = 0

for key in subjects:
    data["subjects"][key] = {}
    exdf_subject = exdf[exdf["Subject"]==key]

    # find gender split for mentions of concept vs scientists
    mention = exdf_subject.apply(lambda x : 1 if x['Type of Mention'] == "concept" else 2, axis=1)
    gender = exdf_subject.apply(lambda x : 1 if x['Gender'] == "male" else 3, axis=1)
    
    arr = mention.values*gender.values
    n_concept_m   = np.count_nonzero(arr==1)
    n_concept_f   = np.count_nonzero(arr==3)
    n_scientist_m = np.count_nonzero(arr==2)
    n_scientist_f = np.count_nonzero(arr==6)

    n_concept_m_tot   += n_concept_m
    n_concept_f_tot   += n_concept_f
    n_scientist_m_tot += n_scientist_m
    n_scientist_f_tot += n_scientist_f

    data["subjects"][key]["concept"]   = {"male" : n_concept_m,   "female": n_concept_f}
    data["subjects"][key]["scientist"] = {"male" : n_scientist_m, "female": n_scientist_f}

    
# find gender split of unique mentions of scientists
uni_df = exdf.drop_duplicates(subset = ["Name of Scientist"])
uni_scientist_m_tot = len(uni_df[uni_df["Gender"] == "male"].index)
uni_scientist_f_tot = len(uni_df[uni_df["Gender"] == "female"].index)


# get data per unique name
names = uni_df["Name of Scientist"].values.tolist()
print(names)
for ii in range(len(names)):
    name = names[ii]
    data["names"][name] = {
        "gender" : uni_df["Gender"].iloc[ii],
        "nationality" : uni_df["Nationality"].iloc[ii],
        "region" : uni_df["Region"].iloc[ii],
        "number of mentions" : len(exdf[exdf["Name of Scientist"] == name]),
    }

# get summary statistics
if "Examinable" in df.keys():
    condf = exdf[exdf["Type of Mention"] == "concept"]
    scidf = exdf[exdf["Type of Mention"] == "scientist"]
    data["overall"]["concept"]   = {"male" : n_concept_m_tot,   "female": n_concept_f_tot, "examinable":len(condf[condf["Examinable"]=="yes"])}
    data["overall"]["scientist"] = {"male" : n_scientist_m_tot, "female": n_scientist_f_tot, "examinable":len(scidf[scidf["Examinable"]=="yes"])}
else:
    data["overall"]["concept"]   = {"male" : n_concept_m_tot,   "female": n_concept_f_tot}
    data["overall"]["scientist"] = {"male" : n_scientist_m_tot, "female": n_scientist_f_tot}

continent_df = uni_df.groupby(uni_df["Region"].tolist(), as_index=False).size()

data["overall"]["unique"] = {"male" : uni_scientist_m_tot, "female": uni_scientist_f_tot}
data["overall"]["unique"]["region"] = {}

for key in continent_df["index"].values:
    data["overall"]["unique"]["region"][key] = int(continent_df['size'].loc[continent_df['index'] == key])

with open('{}_SummaryStats.json'.format(label), 'w') as fp:
    json.dump(data, fp, indent=4)
