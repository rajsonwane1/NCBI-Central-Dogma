from flask import Flask, render_template, request, jsonify
from Bio import Entrez, SeqIO
from Bio.Seq import Seq
from io import StringIO
import os
import re

app = Flask(__name__)

Entrez.email = os.getenv('NCBI_EML', 'your_email@example.com')

if os.getenv('NCBI_API_KEY'):
    Entrez.api_key = os.getenv('NCBI_API_KEY')


def clean_sequence(sequence):
    sequence = re.sub(r'[^ACGTUNacgtun]', '', sequence)
    sequence = sequence.upper()
    sequence = sequence.replace('U', 'T')
    return sequence


def get_feature_value(feature, name, default='Not available'):
    values = feature.qualifiers.get(name, [])

    if values:
        return values[0]

    return default


def get_ncbi_record(accession):
    accession = accession.strip()

    for database in ['nuccore', 'protein']:
        try:
            with Entrez.efetch(
                db=database,
                id=accession,
                rettype='gb',
                retmode='text'
            ) as handle:
                text = handle.read()

            if text:
                record = SeqIO.read(StringIO(text), 'genbank')
                return database, record

        except Exception:
            pass

    raise ValueError('NCBI could not find this accession.')


def get_protein(protein_id):
    with Entrez.efetch(
        db='protein',
        id=protein_id,
        rettype='gp',
        retmode='text'
    ) as handle:
        text = handle.read()

    return SeqIO.read(StringIO(text), 'genbank')


def analyze_accession(accession):
    database, record = get_ncbi_record(accession)

    result = {
        'input_type': database,
        'accession': record.id,
        'definition': record.description,
        'organism': record.annotations.get('organism', 'Not available'),
        'length': len(record.seq),
        'molecule_type': record.annotations.get('molecule_type', 'Not available'),
        'source': 'NCBI',
        'ncbi_url': f'https://www.ncbi.nlm.nih.gov/{database}/{record.id}'
    }

    if database == 'protein':
        result.update({
            'dna': None,
            'rna': None,
            'protein': str(record.seq),
            'protein_id': record.id,
            'protein_definition': record.description,
            'protein_length': len(record.seq),
            'gene': 'Not available',
            'function': 'See the NCBI protein record for annotation.',
            'cds_location': 'Protein accession supplied directly',
            'translation_source': 'NCBI protein record'
        })

        return result

    cds_list = []

    for feature in record.features:
        if feature.type == 'CDS':
            cds_list.append(feature)

    if not cds_list:
        result.update({
            'dna': str(record.seq),
            'rna': str(record.seq).replace('T', 'U'),
            'protein': '',
            'protein_id': None,
            'protein_definition': 'No CDS was found in this record.',
            'protein_length': 0,
            'gene': 'Not available',
            'function': 'No annotated CDS was found.',
            'cds_location': 'Not available',
            'translation_source': 'No CDS annotation'
        })

        return result

    chosen_cds = cds_list[0]

    for feature in cds_list:
        if feature.qualifiers.get('protein_id'):
            chosen_cds = feature
            break

    cds = chosen_cds.extract(record.seq)

    ncbi_translation = get_feature_value(chosen_cds, 'translation', None)

    if ncbi_translation:
        protein = ncbi_translation
        translation_source = 'NCBI annotated translation'
    else:
        protein = str(cds.translate(to_stop=False))
        translation_source = 'Biopython translation of NCBI CDS'

    protein_id = get_feature_value(chosen_cds, 'protein_id', None)
    protein_record = None

    if protein_id:
        try:
            protein_record = get_protein(protein_id)
        except Exception:
            pass

    if protein_record:
        protein_definition = protein_record.description
    else:
        protein_definition = get_feature_value(chosen_cds, 'product')

    result.update({
        'dna': str(cds),
        'rna': str(cds).replace('T', 'U'),
        'protein': protein,
        'protein_id': protein_id,
        'protein_definition': protein_definition,
        'protein_length': len(protein),
        'gene': get_feature_value(chosen_cds, 'gene'),
        'function': get_feature_value(chosen_cds, 'product'),
        'cds_location': str(chosen_cds.location),
        'translation_source': translation_source
    })

    return result


def analyze_sequence(sequence, frame):
    dna = clean_sequence(sequence)

    if len(dna) < 3:
        raise ValueError('Enter at least 3 DNA bases.')

    if not set(dna) <= set('ACGTN'):
        raise ValueError('Use only A, C, G, T or N.')

    frame = int(frame)

    if frame not in [1, 2, 3]:
        raise ValueError('Reading frame must be 1, 2 or 3.')

    coding = dna[frame - 1:]
    protein = str(Seq(coding).translate(to_stop=False))

    return {
        'input_type': 'raw_dna',
        'accession': 'User sequence',
        'definition': 'DNA translated locally. No NCBI annotation was used.',
        'organism': 'Not available',
        'length': len(dna),
        'molecule_type': 'DNA',
        'source': 'Local analysis',
        'ncbi_url': 'https://www.ncbi.nlm.nih.gov/',
        'dna': coding,
        'rna': coding.replace('T', 'U'),
        'protein': protein,
        'protein_id': None,
        'protein_definition': 'No NCBI protein annotation for this sequence.',
        'protein_length': len(protein),
        'gene': 'Not available',
        'function': 'Not available for a raw sequence.',
        'cds_location': f'Reading frame +{frame}',
        'translation_source': f'Biopython translation, frame +{frame}'
    }


@app.get('/')
def home():
    return render_template('index.html')


@app.post('/api/analyze')
def analyze():
    try:
        data = request.get_json()
        mode = data.get('mode', 'accession')

        if mode == 'sequence':
            result = analyze_sequence(
                data.get('sequence', ''),
                data.get('frame', 1)
            )
        else:
            result = analyze_accession(data.get('accession', ''))

        return jsonify({
            'ok': True,
            'result': result
        })

    except Exception as error:
        return jsonify({
            'ok': False,
            'error': str(error)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
