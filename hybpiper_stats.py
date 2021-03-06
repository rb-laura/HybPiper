#!/usr/bin/env python2

#########################
# HybPiper Stats Script #
#########################

helptext = '''Gather statistics about HybPiper run.

Supply the output of get_seq_lengths.py and a list of HybPiper directories

For an explanation of columns, see github.com/mossmatters/HybPiper/wiki

'''

import argparse, os, sys, subprocess

def file_len(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])


def enrich_efficiency_blastx(blastxfilename):
	'''Parse BLASTX results to calculate enrichment effiiency'''
	reads_with_hits = [x.split()[0] for x in open(blastxfilename)]
	if os.path.isfile(blastxfilename.replace(".blastx","_unpaired.blastx")):
		reads_with_hits += [x.split()[0] for x in open(blastxfilename.replace(".blastx","_unpaired.blastx"))]
	numReads = len(set(reads_with_hits))
	
	return("NA",str(numReads),"NA")


def enrich_efficiency_bwa(bamfilename):
	'''Run and parse samtools flagstat output, return number of reads and number on target'''
	samtools_cmd = "samtools flagstat {}".format(bamfilename)
	child = subprocess.Popen(samtools_cmd,shell=True,stdout=subprocess.PIPE)
	flagstat_results = [line for line in child.stdout.readlines()]
	numReads = float(flagstat_results[0].split()[0])
	mappedReads = float(flagstat_results[4].split()[0])
	
	if os.path.isfile(bamfilename.replace(".bam","_unpaired.bam")):
		unpaired_samtools_cmd = "samtools flagstat {}".format(bamfilename.replace(".bam","_unpaired.bam"))
		unpaired_child = subprocess.Popen(unpaired_samtools_cmd,shell=True,stdout=subprocess.PIPE)
		flagstat_results = [line for line in unpaired_child.stdout.readlines()]
		numReads += float(flagstat_results[0].split()[0])
		mappedReads += float(flagstat_results[4].split()[0])
	
	return str(int(numReads)),str(int(mappedReads)),"{0:.3f}".format(mappedReads/numReads)
	
def recovery_efficiency(name):
	'''Report the number of genes with mapping hits, contigs, and exon sequences'''
	a= file_len("{}/spades_genelist.txt".format(name))
	b= file_len("{}/exonerate_genelist.txt".format(name))
	c= file_len("{}/genes_with_seqs.txt".format(name))
	
	return str(a),str(b),str(c)
	
def seq_length_calc(seq_lengths_fn):
	'''From the output of get_seq_lengths.py, calculate the number of genes with seqs, and at least a pct of the reference length'''
	seq_length_dict = {}
	with open(seq_lengths_fn) as seq_len:
		gene_names = seq_len.readline()
		target_lengths = seq_len.readline().split()[1:]
		for line in seq_len:
			line = line.split()
			name = line.pop(0)
			is_25pct = 0
			is_50pct = 0
			is_75pct = 0
			is_150pct = 0
			for gene in xrange(len(line)):
				gene_length = float(line[gene])
				target_length = float(target_lengths[gene])
				if gene_length > target_length * 0.25:
					is_25pct += 1
				if gene_length > target_length * 0.50:
					is_50pct += 1
				if gene_length > target_length * 0.75:
					is_75pct += 1
				if gene_length > target_length * 1.5:
					is_150pct += 1	
			seq_length_dict[name] = [str(is_25pct),str(is_50pct),str(is_75pct),str(is_150pct)]
	return seq_length_dict
	
def main():
	parser = argparse.ArgumentParser(description=helptext,formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("seq_lengths",help="output of get_seq_lengths.py")
	parser.add_argument("namelist",help="text file with names of HybPiper output directories, one per line")
	args = parser.parse_args()
	
	categories = ["Name",
		"NumReads",
		"ReadsMapped",
		"PctOnTarget",
		"GenesMapped",
		"GenesWithContigs",
		"GenesWithSeqs",
		"GenesAt25pct",
		"GenesAt50pct",
		"GenesAt75pct",
		"Genesat150pct",
		"ParalogWarnings"
			]
	sys.stdout.write("{}\n".format("\t".join(categories)))
	
	seq_length_dict = seq_length_calc(args.seq_lengths) 
	stats_dict = {}
	
	
	for line in open(args.namelist):
		name = line.rstrip()
		stats_dict[name] = []
		#Enrichment Efficiency
		bamfile = "{}/{}.bam".format(name,name)
		blastxfile ="{}/{}.blastx".format(name,name)
		if os.path.isfile(bamfile):
			stats_dict[name] += enrich_efficiency_bwa(bamfile)
		elif os.path.isfile(blastxfile):
			stats_dict[name] += enrich_efficiency_blastx(blastxfile)
		else:
			sys.stderr.write("No .bam or .blastx file found for {}\n".format(name))
			
		#Recovery Efficiency
		stats_dict[name] += recovery_efficiency(name)
		stats_dict[name] += seq_length_dict[name]
		
		#Paralogs
		paralog_warns = file_len("{}/genes_with_paralog_warnings.txt".format(name))
		stats_dict[name].append(str(paralog_warns))
	#SeqLengths
	
	
	for name in stats_dict:	
		sys.stdout.write("{}\t{}\n".format(name,"\t".join(stats_dict[name])))


if __name__ == "__main__":main()


