const $ = id => document.getElementById(id)

let mode = 'accession'


document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(button => {
            button.classList.remove('active')
        })

        tab.classList.add('active')
        mode = tab.dataset.mode

        $('accessionMode').classList.toggle('hidden', mode !== 'accession')
        $('sequenceMode').classList.toggle('hidden', mode !== 'sequence')
        $('status').textContent = ''
    })
})



$('analyzeAccession').onclick = () => {
    analyze({
        mode: 'accession',
        accession: $('accession').value.trim()
    })
}


$('analyzeSequence').onclick = () => {
    analyze({
        mode: 'sequence',
        sequence: $('sequence').value,
        frame: $('frame').value
    })
}


$('accession').addEventListener('keydown', event => {
    if (event.key === 'Enter') {
        $('analyzeAccession').click()
    }
})


async function analyze(data) {
    if (data.mode === 'accession' && !data.accession) {
        setStatus('Enter an accession number.', true)
        return
    }

    if (data.mode === 'sequence' && !data.sequence.trim()) {
        setStatus('Enter a DNA sequence.', true)
        return
    }

    setStatus('Analyzing...')
    $('results').classList.add('hidden')

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })

        const result = await response.json()

        if (!result.ok) {
            throw new Error(result.error)
        }

        showResult(result.result)
        setStatus('Analysis complete.')

    } catch (error) {
        setStatus(error.message, true)
    }
}


function setStatus(message, error = false) {
    $('status').textContent = message
    $('status').classList.toggle('error', error)
}


function value(value) {
    return value || 'Not available'
}


function showResult(result) {
    $('title').textContent = result.accession
    $('definition').textContent = result.definition

    $('organism').textContent = value(result.organism)
    $('length').textContent = `${result.length.toLocaleString()} bp / aa`
    $('molecule').textContent = value(result.molecule_type)
    $('proteinLength').textContent = `${result.protein_length.toLocaleString()} aa`

    $('ncbiLink').href = result.ncbi_url

    $('dna').textContent = result.dna || 'Not available'
    $('rna').textContent = result.rna || 'Not available'
    $('protein').textContent = result.protein || 'Not available'

    $('dnaMeta').textContent = result.cds_location || ''
    $('proteinMeta').textContent = result.protein_id || ''
    $('translationSource').textContent = result.translation_source || ''

    $('proteinId').textContent = value(result.protein_id)
    $('gene').textContent = value(result.gene)
    $('cdsLocation').textContent = value(result.cds_location)
    $('function').textContent = value(result.function)

    $('results').classList.remove('hidden')

    window.scrollTo({
        top: $('results').offsetTop - 30,
        behavior: 'smooth'
    })
}
