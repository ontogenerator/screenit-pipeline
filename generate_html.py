import pickle
from collections import defaultdict


symbol_dict = {0: "<td class='icon-column check-mark'>✔</td>",
               1: "<td class='icon-column'>⚠</td>",
               2: "<td class='icon-column cross-mark'>✖</td>"}


def generate_table(rows, name, tools):
    table = ''
    for row in rows:
        symbol = symbol_dict[row[0]]
        if len(row) == 2:
            table += f"<tr>{symbol}<td class='description-column'>{row[1]}</td></tr>"
        else:
            table += f"<tr>{symbol}<td class='description-column'>{row[1]}</td><td>{row[2]}</td></tr>"
    return f'<h2>{name}</h2><table>{table}</table><i>Generated by {", ".join(tools)}</i>'


def generate_html(doi, filename, jetfighter, limitation_recognizer, trial_identifier, sciscore, barzooka, oddpub, reference_check, rtransparent):
    print('dumping')
    pickle.dump((doi, filename, jetfighter, limitation_recognizer, trial_identifier, sciscore, barzooka, oddpub, reference_check, rtransparent, filename, jetfighter, limitation_recognizer, trial_identifier, sciscore, barzooka, oddpub, reference_check, rtransparent), open('data_for_html.pickle', 'wb'))
    print('done')
    import time
    time.sleep(999999)
    exit()
    html = ''
    after_html = ''

    # reference check
    critical = False
    if reference_check[doi]['raw_json']['status'] == 'FAILURE':
        rows = [(0, 'We found no retracted references, and no references with erratums or corrections.')]
    else:
        rows = []
        for citation_doi in reference_check[doi]['raw_json']['papers']:
            if 'retracted' in reference_check[doi]['raw_json']['papers'][citation_doi]:
                title = reference_check[doi]['raw_json']['papers'][citation_doi]['title']
                title = title[:60] + ('…' if len(title) > 60 else '')
                if reference_check[doi]['raw_json']['papers'][citation_doi]['retracted'] == True or reference_check[doi]['raw_json']['papers'][citation_doi]['retracted'] == 'Retracted':
                    critical = True
                    rows.append((2, 'Retracted', f'''A paper you reference, {citation_doi} ("{title}"), has been retracted. If you need to cite this paper, we recommend noting at the beginning of the citation that the paper is retracted (i.e. RETRACTED: Title of paper, authors, journal, etc.).'''))
                elif isinstance(reference_check[doi]['raw_json']['papers'][citation_doi]['retracted'], str) and ['Has erratum', 'Has correction', 'Has expression of concern'] in reference_check[doi]['raw_json']['papers'][citation_doi]['retracted']:
                    rows.append((1, 'Has erratum', f'''A paper you reference, {citation_doi} ("{title}"), has an erratum posted. We recommend checking the erratum to confirm that it does not impact the accuracy of your citation.'''))
        if not rows:
            rows = [(0, 'We found no retracted references, and no references with erratums or corrections.')]
    if critical:
        html += generate_table(rows, 'Critical issues (references)', ['scite.ai'])
    else:
        after_html += generate_table(rows, 'References', ['scite.ai'])

    # rigor
    if sciscore[doi]['is_modeling_paper']:
        rows = [(0, 'NIH rigor criteria are not applicable to paper type.')]
    else:
        if trial_identifier[doi]['trial_identifiers']:
            alert = 0
            bullets = []
            for trial in trial_identifier[doi]['trial_identifiers']:
                if trial['link']:
                    bullets.append(f"<a href=\"{trial['link']}\">{trial['identifier']}</a>: {trial['status']}")
                else:
                    bullets.append(f"{trial['identifier']}: {trial['status']}")
                if not (trial['resolved'] or 'ISRCTN' in trial['identifier']):
                    alert = 2
                    bullets[-1] += ' (Trial number did not resolve on <a href="https://clinicaltrials.gov/">clinicaltrials.gov</a>. Is the number correct?)'
                    bullets[-1] = f'<a style="color:red">{bullets[-1]}</a>'
                bullets[-1] = f'<li>{bullets[-1]}</li>'
            rows.append((alert, 'Clinical trial numbers', f"The following clinical trial numbers were referenced:<br><ul>{''.join(bullets)}</ul>"))
        else:
            rows.append((0, 'Clinical trial numbers', 'No clinical trial numbers were referenced.'))
        rows = []
        for sr in sciscore[doi]['raw_json']['rigor-table']['sections']:
            if sr['title'] == 'Attrition':
                if barzooka[doi]['graph_types']['flowyes']:
                    if sr['srList'][0]['sentence'] in ['not detected.', 'not required.']:
                        rows.append((0, 'Flow charts and attrition', 'Thank you for including a study flow chart to help readers evaluate the risk of bias.'))
                    else:
                        rows.append((0, 'Flow charts and attrition', 'Thank you for including a study flow chart and information about attrition and exclusions to help readers evaluate the risk of bias.'))
                else:
                    if sr['srList'][0]['sentence'] in ['not detected.', 'not required.']:
                        rows.append((0, 'Flow charts and attrition', 'We did not find a study flow chart or information about attrition and excluded observations. If you included a study flow chart in your supplemental files, we apologize for missing this. Our tool is not able to screen separate supplemental files.<br><br>We recommend including a study flow chart to help readers evaluate the risk of bias. Study flow charts efficiently illustrate the study design, and show the number of included and excluded observations at each phase of the experiment. Many reporting guidelines contain flow chart templates for different study design types (e.g. CONSORT for clinical trials, PRISMA for systematic reviews, STROBE for observational studies). Flow charts are also important for animal studies and in vitro experiments. The NC3Rs Experimental Design Assistant tool can create flow charts for preclinical studies.'))
                    else:
                        rows.append((0, 'Flow charts and attrition', 'Thank you for including information about attrition and excluded observations. You may want to present this information in a flow chart. Study flow charts efficiently illustrate the study design, and show the number of included and excluded observations at each phase of the experiment.'))
            else:
                rows.append([(1 if sr['srList'][0]['sentence'] == 'not detected.' else 0), sr['title'], '<blockquote>' + '</blockquote><br><blockquote>'.join([(((s['title'] + ': ') if 'title' in s else '') + s['sentence']) for s in sr['srList']]) + '</blockquote>'])
                if sr['srList'][0]['sentence'] in ['not detected.', 'not required.']:
                    rows[-1][2] = rows[-1][2].replace('<blockquote>', '').replace('</blockquote>', '')
    html += generate_table(rows, 'Rigor', ['SciScore'])

    # sciscore resources
    if len(sciscore[doi]['raw_json']['sections']) == 0:
        resource_table = '<p><i>No key resources detected.</i></p>'
    else:
        resource_table = '<table>'
        for section in sciscore[doi]['raw_json']['sections']:
            title = section['sectionName']
            resource_table += f'<tr><th style="min-width:100px;text-align:center; padding-top:4px;" colspan="2">{title}</th></tr>'
            resource_table += '<tr><td style="min-width:100px;text=align:center"><i>Sentences</i></td><td style="min-width:100px;text-align:center"><i>Resources</i></td></tr>'
            sentences = []
            mentions = defaultdict(list)
            for item in section['srList']:
                sentence = item['sentence']
                sentences.append(sentence)
                for mention in item['mentions']:
                    identifier = mention['rrid']
                    detected = True
                    if identifier is None:
                        if 'suggestedRrid' in mention.keys():
                            identifier = mention['suggestedRrid']
                        detected = False
                    identifier = str(identifier)
                    identifier = identifier.replace(')', '')
                    if 'RRID:' in identifier:
                        rrid = identifier.split('RRID:')[1].strip().replace(')', '')
                        identifier = identifier.replace('RRID:', 'RRID:<a href="https://scicrunch.org/resources/Any/search?q=') + '">' + rrid + '</a>)'
                    mentions[sentence].append({'source': mention['source'], 'term': mention['neText'], 'identifier': identifier, 'detected': detected})
            for sentence in sentences:
                mention_texts = []
                for mention in mentions[sentence]:
                    if mention['detected']:
                        mention_texts.append(f'<div style="margin-bottom:8px"><div><b>{mention["term"]}</b></div><div>detected: {mention["identifier"]}</div></div>')
                    else:
                        mention_texts.append(f'<div style="margin-bottom:8px"><div><b>{mention["term"]}</b></div><div>suggested: {mention["identifier"]}</div></div>')
                mention_text = ''.join(mention_texts)
                resource_table += f'<tr><td style="min-width:100px;vertical-align:top;border-bottom:1px solid lightgray">{sentence}</td><td style="min-width:100px;border-bottom:1px solid lightgray">{mention_text}</td></tr>'
        resource_table += '</table>'
    html += f'<h2>Resources</h2><table>{resource_table}</table><i>Generated by {", ".join(["SciScore"])}</i>'

    # transparency
    rows = []
    if oddpub[doi]['open_code']:
        rows.append((0, 'Open code', f"Thank you for sharing your code. This makes it easier for others to reproduce your analyses.<br><blockquote>{oddpub[doi]['open_code_statement']}</blockquote>"))
    else:
        rows.append((1, 'Open code', 'If you wrote code to analyze your data, please consider sharing the code in a public repository. This makes it easier for others to reproduce your analyses, and may also aid others seeking to analyze similar datasets.'))
    if oddpub[doi]['open_data']:
        rows.append((0, 'Open data', f"Thank you for sharing your data.<br><blockquote>{oddpub[doi]['open_data_statement']}</blockquote>"))
    else:
        rows.append((1, 'Open data', 'If permitted, sharing data can improve reproducibility and make it easier for other scientists to expand on your work. Papers with open data are cited more often than paper without open data. Some institutions have an expert who can provide advice on data sharing.'))
    limitations = ' '.join(limitation_recognizer[doi]['sents']).replace('  ', ' ')
    if limitations:
        rows.append((0, 'Self-acknowledged limitations', f'Thank you for including a limitations section to acknowledge the limitations of your study. The following limitations were found:<br><blockquote>{limitations[:1500]}</blockquote>'))
    else:
        rows.append((1, 'Self-acknowledged limitations', 'An explicit section about the limitations of this study was not found. We encourage authors to include a paragraph in the discussion that addresses study limitations. Every study has limitations. Describing these limitations helps readers to understand and contextualize the research.'))
    if rtransparent[doi]['coi_statement']:
        rows.append((0, 'Conflict of interest statement', 'Thank you for stating any conflicts of interest.'))
    else:
        rows.append((1, 'Conflict of interest statement', 'It is important to supply a conflict of interest statement, even if there are none to declare, to transparently present the research.'))
    if rtransparent[doi]['funding_statement']:
        rows.append((0, 'Funding statement', 'Thank you for reporting your funding source(s), or stating that there was no specific funding for this work.'))
    else:
        rows.append((1, 'Funding statement', 'It is important to supply a funding statement because it makes the funding source and potential conflicts of interests transparent.'))
    if rtransparent[doi]['registration_statement']:
        rows.append((0, 'Registration statement', 'Thank you for registering your study.'))
    else:
        rows.append((1, 'Registration statement', 'A registered protocol makes the planned research project more transparent and can protect against bias.'))
    html += generate_table(rows, 'Transparency', ['ODDPub', 'limitation-recognizer', 'rtransparent', 'trial-identifier'])
    
    # figures
    rows = []
    if barzooka[doi]['graph_types']['bar']:
        rows.append((1, 'Bar graphs of continuous data', 'We found bar graphs of continuous data. We recommend replacing these with more informative graphics (e.g. dotplots, box plots, violin plots), as many different datasets can lead to the same bar graph. The actual data may suggest different conclusions from the summary statistics alone. Please see the following resources for more information on the problems with bar graphs (Weissgerber et al 2015) and what to use instead (Weissgerber et al, 2019).'))
    else:
        rows.append((0, 'Bar graphs of continuous data', 'Thank you for not using bar graphs to present continuous data. Many different datasets and data distributions can lead to the same bar graph, and the actual data may suggest different conclusions from the summary statistics alone.'))
    if barzooka[doi]['graph_types']['bardot']:
        rows.append((1, 'Bar graphs with dot plots', 'Thank you for showing individual data points on your bar graphs. We recommend removing the bars and showing only a dot plot. The following resource illustrates several reasons why dot plots are better than bar graphs with dot plots (https://twitter.com/T_Weissgerber/status/1192694947385876480).'))
    if jetfighter[doi]['page_nums']:
        rows.append((1, 'Rainbow color maps', f'Please consider replacing  the rainbow (“jet”) colormap(s) used on page(s) {",".join(jetfighter[doi]["page_nums"])} with alternatives like Viridis or Cividis. Rainbow color maps distort readers’ perception of the data by introducing visual artifacts. Rainbow color maps are  also inaccessible to readers with colorblindness. Alternatives colormaps like Viridis and Cividis are accessible to colorblind readers and avoid visual artifacts.'))
    else:
        rows.append((0, 'Rainbow color maps', 'Thank you for not using rainbow colormaps. Rainbow color maps distort readers’ perception of the data by introducing visual artifacts and are not accessible to colorblind readers.'))
    html += generate_table(rows, 'Visualization', ['JetFighter', 'Barzooka'])

    html = open('base.html', 'r').read().replace('_PAPER_ID_', doi).replace('_TABLES_', html + after_html)
    return html


# doi, filename, jetfighter, limitation_recognizer, trial_identifier, sciscore, barzooka, oddpub, reference_check, rtransparentdoi, filename, jetfighter, limitation_recognizer, trial_identifier, sciscore, barzooka, oddpub, reference_check, rtransparent = pickle.load(open('data_for_html.pickle', 'rb'))