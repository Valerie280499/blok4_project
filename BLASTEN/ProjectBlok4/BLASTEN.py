# Project Blok4
# Project groep 12
# HAN, Nijmgegen 18 juni 2018
# Valerie Verhalle BIN-1c


from Bio.Blast import NCBIWWW
from Bio.Blast import NCBIXML
from Bio import Entrez
import mysql.connector


# In de main functie word er eerst een connectie gemaakt met de SQL database.
# Alle andere functies worden een voor een aangeroepen, standaard staan alle functies uit. Prints staan ook uit,
# behalve de controle prints (aan deze prints zie je waar BioPython mee bezig is).

# Wanneer je de functie database_sequentie wilt gebruiken, LET ER DAN OP DAT DE READ_FILE FUCNTIE AAN MOET STAAN.
# Zorg er verder voor dat wanneer je de functies database_entrez, databse_omschrijving_match en database_Blast wilt
# wilt gebruiken dat er dan een xml file aanwezig is.

# Standaard staan de bestanden: test.txt, test.fasta en test_results.xml file in gesteld.
# test.txt en test.fasta bestaan uit 1 forward en 1 reverse sequentie, test_results.xml bestaat uit de blast resultaten
# van deze 2 sequenties.
def main():
    conn = mysql.connector.connect(host='sql7.freemysqlhosting.net', db='sql7243063', user='sql7243063',
                                   password='2R1SHGtvvA')
    cursor = conn.cursor()

    # header, seq, ascii = read_file()
    # blast()
    # database_sequentie(conn, cursor, header, seq, ascii)
    # database_entrez(conn, cursor)
    # database_omschrijving_match(conn, cursor)
    # database_Blast(conn, cursor)


# De functie read_file laad een .txt bestand in met ruwe data(@header seq ascii)
# Dit .txt bestand wordt omgezet naar een .fasta file met per sequentie onderelkaar (>header'\n'sequentie'\n')
# Vervoglens returnt de functie 3 lijsten: header(met alleen headers), seq(met alleen sequetnies
# en ascii(met alleen ascii-scores) die daarna doorgegeven kunnen worden aan een volgende functie.
def read_file():
    bestand = open('test.txt')

    header = []
    seq = []
    ascii = []

    for line in bestand:
        line = line.split()
        # print(line)
        header.append(line[0].replace('@', '>') + '\n')
        seq.append(line[1] + '\n')
        ascii.append(line[2])

    dictionary = dict(zip(header, seq))

    # print(dictionary)
    # print(header)
    # print(seq)
    # print(ascii)

    fo = open('test.fasta', 'w')
    for k, v in dictionary.items():
        fo.write(str(k) + str(v))
    fo.close()

    print('je dataset.fasta is weggeschreven.')

    return header, seq, ascii


# De functie Blast laad het eerder weggeschreven .fasta bestand in en gaat hiermee blasten.
# Wanneer Blastx klaar is wordt er een xml file gegenereerd en ook deze wordt weggeschreven.
def blast():
    record = open('test.fasta').read()

    print('BioPython is bezig met BLASTEN')

    result_handle = NCBIWWW.qblast('blastx', 'nr', record, gapcosts='10 1',
                                   expect='0.0001', filter=True,
                                   matrix_name='BLOSUM62',
                                   word_size='6', alignments='10',
                                   descriptions='10', perc_ident='25')

    with open('test_results.xml', 'w') as out_handle:
        out_handle.write(result_handle.read())
    result_handle.close()

    print('BioPython is klaar met BLASTEN, je kunt je resultaten nu inzien in het bestand dataset_results.xml')


# De functie database_entrez gebruikt het weggeschreven xml file om hier de accessiecodes uit te halen.
# De accessiecode wordt gebruikt om met de module Entrez het organisme en de taxonomy per hit op te halen.
# De taxonomy wordt nog gesplitst in Familie, Geslacht en Soort die vervolgens naar de database geupdate worden.
def database_entrez(conn, cursor):
    result_handle = open('test_results.xml')
    blast_records = NCBIXML.parse(result_handle)
    blast_record = next(blast_records)

    Entrez.email = 'v.verhalle@kpnmail.nl'
    E_value_tresh = 0.0001

    print('biopython is bezig met het inserten naar de familie, geslacht en soort kolommen')
    for alignment in blast_record.alignments:
        for hsp in alignment.hsps:
            if hsp.expect < E_value_tresh:
                # print('-'*80)
                handle = Entrez.efetch(db='protein',
                                       id=alignment.accession,
                                       retmode='xml', rettype='gb')
                record = Entrez.parse(handle, 'genbank')

                for index in record:
                    taxonomy = index['GBSeq_taxonomy']
                    # print('taxonomy', index['GBSeq_taxonomy'])

                    familie = str(taxonomy.split(';')[3:4])
                    familie = ''.join(familie.replace('[', '').replace(']', '').split("'"))
                    # print('familie', familie)
                    Familie = ("""insert into Familie(Familie) values ('{}')""".format(familie))
                    cursor.execute(Familie)

                    geslacht = str(taxonomy.split(';')[4:5])
                    geslacht = ''.join(geslacht.replace('[', '').replace(']', '').split("'"))
                    # print('geslacht', geslacht)
                    Geslacht = ("""insert into Geslacht(Geslacht) values('{}')""".format(geslacht))
                    cursor.execute(Geslacht)

                    soort = str(taxonomy.split(';')[5:6])
                    soort = ''.join(soort.replace('[', '').replace(']', '').split("'"))
                    # print('soort', soort)
                    Soort = ("""insert into Soort(Soort) values('{}')""".format(soort))
                    cursor.execute(Soort)

                    # taxonomy = taxonomy.split(';')[3:7]
                    # print('taxonomy', taxonomy)

                handle.close()

    conn.commit()
    conn.close()
    cursor.close()
    print('biopython is klaar met het inserten naar de familie, geslacht en soort kolommen')


# De functie database_sequentie vult de kolom Sequentie in de database met de eerder gegenereerde lijsten:
# header, seq en ascii. Er wordt over deze lijsten heen geloopt en vervolgens per index geupdate naar de datase.
def database_sequentie(conn, cursor, header, seq, ascii):
    print('biopython is bezig met inserten naar de sequentie kolom')
    for index in range(len(header)):
        # index = index.replace('>', '').replace('\n', '')
        print(header[index])
        print(seq[index])
        print(ascii[index])

        sqlheader = ("""insert into Sequentie(header, sequentie, ascii_score) values ('{}', '{}','{}')"""
                     .format(header[index], seq[index], ascii[index]))
        cursor.execute(sqlheader)

    conn.commit()
    conn.close()
    cursor.close()
    print('biopython is klaar met het inserten naar de seqientie kolom')


# De functie databse_Omschrijving_match vult de kolom Omschrijving_match in de database door het eerder gegenereerde
# xml file op te halen. Uit dit xml file word de benodigde informatie gehaald en vervolgens geupdate naar de database.
# Voorbeelden van wat er naar de database geupdate wordt: E_value, identity, title, accession, subject, query, etc.
def database_omschrijving_match(conn, cursor):
    result_handle = open('test_results.xml')
    blast_records = NCBIXML.parse(result_handle)
    blast_record = next(blast_records)

    e_value_tresh = 0.0001
    # count = 0
    hit_id = ''
    organism = ''

    print('biopython begint met inserten naar de omschrijving_match kolom')
    # for blast_record in blast_records:
    #     print('hoi')

    for alignment in blast_record.alignments:
        for hsp in alignment.hsps:
            if hsp.expect < e_value_tresh:
                # print('title:', alignment.title)
                # print('length:', alignment.length)
                # print('E_value:', hsp.expect)
                # print('identity:', hsp.identities)
                # print('positive:', hsp.positives)
                # print('accessioncode:', alignment.accession)
                # print('frame:', hsp.frame)
                # print('match:  ', hsp.match)
                # print('subject:', hsp.sbjct)
                # print('query:', hsp.query)
                # print('gaps', hsp.gaps)
                # print('score:', hsp.score)

                for index in alignment.title.split(' ', 2)[:1]:
                    hit_id += index
                # print('hit_id', hit_id)

                Entrez.email = 'v.verhalle@kpnmail.nl'
                handle = Entrez.efetch(db='protein', id=alignment.accession, retmode='xml', rettype='gb')
                record = Entrez.parse(handle, 'genbank')

                for index in record:
                    organism += index['GBSeq_organism']
                    # print('organisme', organism)
                    # print(count)

                omschrijving_match = ("""insert into Omschrijving_match (Hit_id, Organisme, Accessiecode, Title, Score, E_value, Identitie, Positives, Gaps, Frame, Matches, Subject) values('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(hit_id, organism, alignment.accession, alignment.title, hsp.score, hsp.expect, hsp.identities, hsp.positives, hsp.gaps, hsp.frame, hsp.match, hsp.sbjct))
                cursor.execute(omschrijving_match)
                hit_id = ''
                organism = ''

    conn.commit()
    conn.close()
    cursor.close()

    print('biopython is klaar met inserten naar de omschrijving_match kolom')


# De functie database_Blast vult de kolom Blast in de database met de hit omschrijving, opgehaald uit het
# xml file, en de huidige datum.
def database_Blast(conn, cursor):
    result_handle = open('test_results.xml')
    blast_records = NCBIXML.parse(result_handle)
    blast_record = next(blast_records)

    E_value_tresh = 0.0001

    print('biopython is bezig met het inserten naar de blast kolom')
    for alignment in blast_record.alignments:
        for hsp in alignment.hsps:
            if hsp.expect < E_value_tresh:
                Blast = ("""insert into Blast(Description, Datum) values ('{}', NOW())""".format(alignment.title))
                cursor.execute(Blast)

    conn.commit()
    conn.close()
    cursor.close()
    print('biopython is klaar met het inserten naar de blast kolom')


main()
