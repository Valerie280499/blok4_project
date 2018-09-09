from flask import Flask, render_template, request, redirect, url_for
import json
from Bio.Blast import NCBIWWW
from Bio.Blast import NCBIXML
from Bio import Entrez
import importlib
import mysql.connector
import matplotlib.pyplot as plt
#import numpy
from io import BytesIO
import base64

app = Flask(__name__)
# App routes voor de basisnavigatie bovenaan de webapplicatie, en voor specifieke redirects in de code
@app.route('/index')
def index():
    return render_template('index.html')
@app.route('/team')
def team():
    return render_template('team.html')
@app.route('/database')
def database():
    return render_template('database.html')
@app.route('/blast')
def blast2():
    return render_template('blast.html')
@app.route('/login')
def login2():
    return redirect('/')
@app.route('/updated')
def updated():
    return render_template('databasewrite.html')
@app.route('/', methods=['GET', 'POST'])
def login():
    # Login pakt de gegevens uit de html met een request, controleers of deze hetzelfde is als onderstaande strings, redirect naar homescherm als deze
    # goed zijn, of geeft een error door aan de template als deze fout is, opgeslagen in de error variabele.
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect('front')
    return render_template('login.html', error=error)

@app.route('/front', methods=['GET','POST'])
def home():
    return render_template('index.html')
@app.route('/blast1', methods=['GET', 'POST'])
def blast():
    bestand = request.form.get('fasta') # Pakt de fasta uit de html form en stopt deze in een variabele.

    print("Python is bezig met blast()")


    qresult = NCBIWWW.qblast('blastx', 'nr',bestand , gapcosts='10 1',   # Blast functie met de parameter die deze gebruikt
                             expect = '0.0001', filter=True,
                             matrix_name='BLOSUM62',
                             word_size='6', alignments='10',
                             descriptions='10', perc_ident = '25')

    print('python maakt bestand')

    with open("my_blast.xml", "w") as out_handle:
        out_handle.write(qresult.read())  # schrijft de resultaten van de blast uit in een .xml file
        qresult.close()

    print('python opent bestand en parsed in nested list')
    blastlist = []
    nestedblastlist = []

    qresult = open("my_blast.xml", "r") # Blast_record voor het uitzetten van de resultaten in een lijst, deze worden vervolgens in de juiste volgorde
    blast_records = NCBIXML.parse(qresult) # gezet in een 2dlijst
    for blast_record in blast_records:
        for alignment in blast_record.alignments:
            for hsp in alignment.hsps:
                blastlist.append(alignment.title)
                blastlist.append(alignment.length)
                blastlist.append(hsp.expect)
                blastlist.append(hsp.align_length / blast_record.query_length * 100)
    for i in range(0, len(blastlist), 4):
        nestedblastlist.append(blastlist[i: i + 4])
    print(nestedblastlist)

    print("Python is klaar met blasten")

    return render_template('blastresult.html', blastresult = nestedblastlist)

@app.route('/databaseresult', methods=['GET','POST'])
def database2():
    zoekwoord = request.form.get('zoekwoord') # Pakt het zoekwoord uit de html form
    conn = mysql.connector.connect(host='sql7.freemysqlhosting.net', db='sql7243063', user='sql7243063',
                                   password='2R1SHGtvvA', port='3306') # Maakt connectie met de gebruikte database
    cursor = conn.cursor()
    countlist = ("""Select Organisme,count(Organisme) from Omschrijving_match where Title like '%{}%' group by Organisme""").format(zoekwoord) # Deze code stopt het zoekwoord in de SQL query
    cursor.execute(countlist)
    symbol = []
    synprodcount = []
    for value in cursor:
        symbol.append(value[0])  # De eerste in de lijst index is steeds het symbol, en de tweede steeds de count, dus zet die dat op de juiste volgorde in de lijst
        synprodcount.append(value[1])

    print(symbol)
    print(synprodcount)
    barx = symbol
    bary = synprodcount
    print('append shit')
    plt.xticks(rotation=90, fontsize=5)
    plt.bar(barx, bary)
    print('bar')
    print('figfile')
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0) # Deze code wordt gebruikt om van een Matplotlib een png te maken, vervolgens wordt deze ge-encode en gedecode als deze in de template wordt gerendered
    figdata_png = base64.b64encode(figfile.getvalue())
    resultplot = figdata_png
    return render_template('databaseresult.html', plotimage = resultplot.decode('utf8'))

@app.route('/databasewrite', methods=['GET', 'POST'])

def main():
    conn = mysql.connector.connect(host='sql7.freemysqlhosting.net', db='sql7243063', user='sql7243063',
                                   password='2R1SHGtvvA', port='3306')
    cursor = conn.cursor()

    result_handle = open('my_blast.xml')
    blast_records = NCBIXML.parse(result_handle)
    blast_record = next(blast_records)

    Entrez.email = 'v.verhalle@kpnmail.nl'
    E_value_tresh = 0.0001

    print('biopython is bezig met het inserten naar de familie, geslacht en soort kolommen')
    for alignment in blast_record.alignments:
        for hsp in alignment.hsps:
            if hsp.expect < E_value_tresh:
                # print('-'*80)
                handle = Entrez.efetch(db='protein', id=alignment.accession, retmode='xml', rettype='gb')
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


    conn = mysql.connector.connect(host='sql7.freemysqlhosting.net', db='sql7243063', user='sql7243063',
                                   password='2R1SHGtvvA', port='3306')
    cursor = conn.cursor()
    result_handle = open('my_blast.xml')
    blast_records = NCBIXML.parse(result_handle)
    blast_record = next(blast_records)

    e_value_tresh = 0.0001
    count = 0
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
                # print(count)

                for index in alignment.title.split(' ', 2)[:1]:
                    hit_id += index
                #print('hit_id', hit_id)

                Entrez.email = 'v.verhalle@kpnmail.nl'
                handle = Entrez.efetch(db='protein', id=alignment.accession, retmode='xml', rettype='gb')
                record = Entrez.parse(handle, 'genbank')

                for index in record:
                    organism += index['GBSeq_organism']
                    #print('organisme', organism)

                omschrijving_match = ("""insert into Omschrijving_match (Hit_id, Organisme, Accessiecode, Title, Score, E_value, Identitie, Positives, Gaps, Frame, Matches, Subject) values('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(hit_id, organism, alignment.accession, alignment.title, hsp.score, hsp.expect, hsp.identities, hsp.positives, hsp.gaps, hsp.frame, hsp.match, hsp.sbjct))
                cursor.execute(omschrijving_match)
                hit_id = ''
                organism = ''

    conn.commit()
    conn.close()
    cursor.close()

    print('biopython is klaar met inserten naar de omschrijving_match kolom')
    return redirect('updated') #Geeft een template die de gebruiker laat weten dat de database is ge-update


# De functie database_Blast vult de kolom Blast in de database met de hit omschrijving, opgehaald uit het



if __name__ == '__main__':
    app.run()
