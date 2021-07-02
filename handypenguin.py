import json
import sys
import xlrd
import copy
import glob
from datetime import date
import os
import shutil


def retrieve_file_path(wd):
	try:
		wb = xlrd.open_workbook("{}/starlims_to_json.xls".format(wd))
		sheet = wb.sheet_by_index(0)
		starlims_files=[]
		concentration_files=[]
		indexes=[]
		index_ids=[]
		for i in range(1,sheet.nrows):
			#print(sheet.cell_value(i, 2))
			starlims_files.append(sheet.cell_value(i, 0).strip() )
			concentration_files.append(sheet.cell_value(i, 1).strip() )
			indexes.append(sheet.cell_value(i, 2).strip() )
			index_ids.append(sheet.cell_value(i, 3))
			try:
				batch_name=str(int(sheet.cell_value(i, 4)))
			except:
				print("err")
				batch_name=sheet.cell_value(i, 4)
			
	except:
		f=open("{}/error.txt".format(wd),"w")
		f.write("starlims_to_json.xls saknas, eller är felformaterad!")
		quit()

	return(starlims_files, concentration_files, indexes, index_ids,batch_name)

def read_index_file(index_per_well,index_id_per_well,index_file_path,index_id,wd):
	try:
		for line in open(index_file_path):
			content=line.strip().split()
			index_per_well[content[0]]="{} ({}-{})".format(content[1],content[2],content[3])
			index_id_per_well[content[0]]=index_id
	except:
		f=open("{}/error.txt".format(wd),"w")
		f.write("Kunde ej läsa index filen:{}".format(index_file_path))
		quit()

	return(index_per_well,index_id_per_well)


def read_concentration_file(sample_concentration_to_well,concentration_file_path,wd):

	wb = xlrd.open_workbook("{}/{}".format(wd,concentration_file_path))
	sheet = wb.sheet_by_index(0)
	rows=["A","B","C","D","E","F","G","H"]
	row=0
	for i in range(12,20):
		for j in range(1,13):
			sample_concentration_to_well[rows[row]+str(j)]=sheet.cell_value(i, j)
			
		row+=1		
		 
	return(sample_concentration_to_well)
	

main_template={
  "name": "Name",
  "customer": "cust032",
  "comment": "Automatically generated by the Handy Penguin",
  "samples": []
}

sample_template={
      "name": "SampleName",
      "application": "RMLP05R800",
      "data_analysis": "fluffy",
      "comment": "",
      "volume": "200",
      "concentration": "10",
      "concentration_sample":"SampleConcentration",
      "pool": "Pool",
      "rml_plate_name": "",
      "well_position_rml": "",
      "index": "Index",
      "index_number": "IndexNumber",
      "index_sequence": "IndexSequence",
      "priority": "standard"
}


wd=os.path.dirname(os.path.realpath(__file__))
starlims_files, concentration_files, indexes, index_id, name=retrieve_file_path(wd)

out_file_prefix=starlims_files[0].split("_")[0].split(" ")[0]

print (indexes)
index_per_well={}
index_id_per_well={}
i=0
for index_file_path in indexes:
	index_per_well,index_id_per_well=read_index_file(index_per_well,index_id_per_well,index_file_path,index_id[i],wd)
	i+=1

sample_concentration_to_well={}
try:
	for concentration_file_path in concentration_files:
		sample_concentration_to_well=read_concentration_file(sample_concentration_to_well,concentration_file_path,wd)
except:
	f=open("{}/error.txt".format(wd),"w")
	f.write("Kunde ej läsa koncentration-filen:{}".format(concentration_file_path))	
	quit()

sample_data=[]
for file in starlims_files:
	wb = xlrd.open_workbook(file)
	sheet = wb.sheet_by_index(0)

	for i in range(sheet.nrows):
		if i ==0:
			continue
		sample_data.append(copy.deepcopy(sample_template))
		well=sheet.cell_value(i, 13)+str(int(sheet.cell_value(i, 14)))
		well_out=sheet.cell_value(i, 13)+":"+str(int(sheet.cell_value(i, 14)))

		sample_data[-1]["name"]=sheet.cell_value(i, 0)
		sample_data[-1]["comment"]=well_out
		sample_data[-1]["index_number"]=str(index_per_well[ well ].split(" ")[0].replace("UDI",""))
		sample_data[-1]["index_sequence"]=index_per_well[ well ]
		sample_data[-1]["index"]=index_id_per_well[ well ]
		sample_data[-1]["pool"]=name
		sample_data[-1]["concentration_sample"]=str(sample_concentration_to_well[well])

current_date = date.today()
directory_path=out_file_prefix+"_JSON"
try:
	os.mkdir(directory_path)

except:
	pass

for file in starlims_files:	
	shutil.move(file, directory_path)
for file in concentration_files:	
	shutil.move(file, directory_path)

shutil.move( "{}/starlims_to_json.xls".format(wd) , directory_path)

main_template["name"]=str(name)
main_template["samples"]=sample_data
f=open("{}/{}_nipt_rml.json".format(directory_path,out_file_prefix),"w")
f.write(json.dumps(main_template,indent=4)) 
f.close()
