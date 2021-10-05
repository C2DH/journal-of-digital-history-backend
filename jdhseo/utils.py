import marko
import logging
from citeproc import formatter
from citeproc import Citation
from citeproc import CitationItem
from citeproc import CitationStylesStyle
from citeproc import CitationStylesBibliography
from citeproc.source.json import CiteProcJSON

logger = logging.getLogger(__name__)


def getReferencesFromJupyterNotebook(notebook):
    metadata = notebook.get('metadata')
    references = []
    bibliography = []
    try:
        references = metadata.get('cite2c').get('citations')
        bib_source = CiteProcJSON(references.values())
        bib_style = CitationStylesStyle(
            'jdhseo/styles/modern-language-association.csl', validate=False)
        bib = CitationStylesBibliography(
            bib_style, bib_source, formatter.html)
        # register citation
        for key, entry in bib_source.items():
            # print(key)
            # for name, value in entry.items():
            #     print('   {}: {}'.format(name, value))
            bib.register(Citation([CitationItem(key)]))
        for item in bib.bibliography():
            bibliography.append(str(item))
    except Exception as e:
        logger.exception(e)
        pass
    return references, bibliography


def parseJupyterNotebook(notebook):
    cells = notebook.get('cells')
    title = []
    abstract = []
    contributor = []
    disclaimer = []
    paragraphs = []
    collaborators = []
    keywords = []
    references, bibliography = getReferencesFromJupyterNotebook(notebook)

    for cell in cells:
        # check cell metadata
        tags = cell.get('metadata', {}).get('tags', [])
        source = ''.join(cell.get('source', ''))
        if 'hidden' in tags:
            continue
        if 'title' in tags:
            title.append(marko.convert(source))
        elif 'abstract' in tags:
            abstract.append(marko.convert(source))
        elif 'contributor' in tags:
            contributor.append(marko.convert(source))
        elif 'disclaimer' in tags:
            disclaimer.append(marko.convert(source))
        elif 'collaborators' in tags:
            collaborators.append(marko.convert(source))
        elif 'keywords' in tags:
            keywords.append(marko.convert(source))
        elif cell.get('cell_type') == 'markdown':
            paragraphs.append(marko.convert(source))

    return {
        'title': title,
        'abstract': abstract,
        'contributor': contributor,
        'disclaimer': disclaimer,
        'paragraphs': paragraphs,
        'collaborators': collaborators,
        'keywords': keywords,
        'references': references,
        'bibliography': bibliography
    }
