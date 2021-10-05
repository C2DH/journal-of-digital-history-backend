import marko


def parseJupyterNotebook(notebook):
    cells = notebook.get('cells')
    title = []
    abstract = []
    contributor = []
    disclaimer = []
    paragraphs = []
    collaborators = []
    keywords = []

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
        'keywords': keywords
    }
