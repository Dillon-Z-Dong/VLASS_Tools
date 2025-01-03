import time
import numpy as np
import os
from casacore.tables import table

def msclip(ms_path, time_clip_tables = ['POINTING','SYSPOWER'], time_chunk_col = 'FIELD_ID'):
	'''Input a path to a ms. 

	This code will:
	
	- replace the tables in time_clip_tables (default POINTING, SYSPOWER) with only the rows which are within the bounds of a time chunk actually present in the ms 
		- for VLASS, this is 'FIELD_ID' (since fields are 0.45s each). For a regular ms, you'd probably want 'SCAN_NUMBER'
		- This assumes that your table has a column named 'TIME' and that it is in the same convention as the ms as a whole (should be. The convention is MJD seconds.)
	''' 


	#Timing
	start = time.time()

	#Add slash to end of ms_path if needed
	ms_path = ms_path.rstrip('/')+'/'

	#Open the ms as a table using python casacore
	ms = table(ms_path, readonly=True)

	#Clip tables in time_clip_tables
	try:
		if len(time_clip_tables) > 0:

			#Get time chunks
			chunk_ids = ms.getcol(time_chunk_col)
			unique_chunks = np.unique(chunk_ids)
			print('Found', len(unique_chunks), time_chunk_col+'s', 'in ms')
			indices = [np.where(chunk_ids == val) for val in unique_chunks]

			#Get times corresonding to timechunks
			mstime = ms.getcol('TIME')
			chunktimes = [mstime[index] for index in indices]
			min_times = np.array([np.min(x) for x in chunktimes])
			max_times = np.array([np.max(x) for x in chunktimes])

			#Clip each table
			for tabname in time_clip_tables:
				tabpath = ms_path+tabname
				cliptab = table(tabpath,readonly=False)

				if cliptab.nrows == 0:
					print('Not clipping', tabname, 'table has 0 rows')
					cliptab.close()
					cliptab.done()

				else:
					#Get initial info
					print('Clipping table: ', tabpath)

					#Read in the table
					cliptime = cliptab.getcol('TIME')

					#Array operation which is essentially the same as doing a bunch of np.wheres and concatinating
					#RAM intensive. Can use a loop if needed
					condition = np.logical_and(cliptime[:,np.newaxis] >= min_times, cliptime[:,np.newaxis] <= max_times)  
					
					#Get rows to keep (usually a small fraction of original for VLASS)
					keeper_indices = np.where(condition.any(axis=1))[0]
					print('Keeping', round(len(keeper_indices)/len(cliptime)*100,5),'percent of the table:',len(keeper_indices),'rows')
					keepers = cliptab.selectrows(rownrs = keeper_indices)
					keepers.copy(tabpath+'_keepers', valuecopy = True)
					
					for tab in [ms, keepers, cliptab]:
						tab.close()
						tab.done()

					os.popen('rm -rf '+tabpath+' && mv '+tabpath+'_keepers '+tabpath)

		
	except Exception as e:
		print('Error:')
		print(e)
		try:
			for tab in [ms, keepers, cliptab]:
				try:
					tab.done()
				except:
					pass
		except:
			pass
		return


	#Wrap up
	
	try:
		for tab in [ms, keepers, cliptab]:
			try:
				tab.done()
			except:
				pass
	except:
		pass

	end = time.time()
	runtime = end-start
	print('Finished in', runtime, 'seconds')
	return runtime